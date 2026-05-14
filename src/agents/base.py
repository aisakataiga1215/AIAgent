import json
import re
from dataclasses import dataclass, field
from typing import Any
from anthropic import Anthropic
from src.config import settings
from src.tools.registry import ToolRegistry
from src.tools.base import ToolResult
from src.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentStep:
    iteration: int
    thought: str = ""
    action: str = ""
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    final_answer: str = ""


@dataclass
class AgentResult:
    success: bool
    content: str
    steps: list[AgentStep] = field(default_factory=list)
    tool_calls: int = 0
    tokens_used: int = 0


SYSTEM_PROMPT_TEMPLATE = """You are {role}.
{role_description}

You work in a ReAct (Reasoning + Acting) loop:
1. Analyze the task
2. Decide which tool to use (if any)
3. Use the tool and observe the result
4. Repeat until you have enough information

## Available Tools
{tool_descriptions}

## Output Format
When you need to use a tool, respond with:
```
Action: tool_name
Action Input: {{"param": "value"}}
```

When you have the final answer, respond with:
```
Final Answer:
<your complete response here>
```

## Constraints
- Use tools when you need more information; do not guess.
- If a tool fails, try an alternative approach or report the failure.
- Cite specific evidence (line numbers, file paths, tool outputs) in your final answer.
- Be concise and actionable.
"""


class ReActAgent:
    """Base ReAct Agent. Think → Act → Observe loop."""

    role: str = "Agent"
    role_description: str = "A helpful AI agent."
    system_prompt_extra: str = ""

    def __init__(
        self,
        registry: ToolRegistry,
        model: str | None = None,
        max_iterations: int = 10,
    ) -> None:
        self.registry = registry
        self.model = model or settings.llm_model
        self.max_iterations = max_iterations
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.steps: list[AgentStep] = []

    def _build_system_prompt(self) -> str:
        tools_desc = "\n".join(
            f"- **{t.name}**: {t.description}" for t in self.registry.list_tools()
        )
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            role=self.role,
            role_description=self.role_description,
            tool_descriptions=tools_desc,
        )
        if self.system_prompt_extra:
            prompt += "\n" + self.system_prompt_extra
        return prompt

    def _parse_output(self, text: str) -> dict[str, Any]:
        """Parse ReAct output: Action, Action Input, or Final Answer."""
        # Check for Final Answer
        if "Final Answer:" in text:
            idx = text.index("Final Answer:")
            return {"type": "final", "content": text[idx + len("Final Answer:"):].strip()}

        # Check for Action
        action_match = re.search(r"Action:\s*(\S+)", text)
        if action_match:
            action = action_match.group(1)
            action_input = {}
            input_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
            if input_match:
                try:
                    action_input = json.loads(input_match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"type": "action", "action": action, "action_input": action_input}

        # Plain text (shouldn't normally happen, treat as final)
        return {"type": "final", "content": text.strip()}

    async def run(self, task: str) -> AgentResult:
        """Execute the ReAct loop for a given task."""
        self.steps = []
        messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
        total_tokens = 0

        for i in range(self.max_iterations):
            step = AgentStep(iteration=i + 1)

            # Build request with tools
            tool_schemas = self.registry.to_anthropic_schemas()
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._build_system_prompt(),
                tools=tool_schemas if tool_schemas else None,
                messages=messages,
            )
            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Process response
            msg = response.content
            assistant_block: dict[str, Any] = {"role": "assistant", "content": msg}
            messages.append(assistant_block)

            # Check for tool calls
            tool_use_blocks = [b for b in msg if b.type == "tool_use"]
            text_blocks = [b for b in msg if b.type == "text"]

            if tool_use_blocks:
                tool_block = tool_use_blocks[0]
                step.action = tool_block.name
                step.action_input = tool_block.input or {}
                step.thought = text_blocks[0].text if text_blocks else ""

                # Execute tool
                result = await self.registry.execute(tool_block.name, **step.action_input)
                step.observation = result.content[:3000]
                self.steps.append(step)

                logger.info(
                    "agent_step",
                    iteration=i + 1,
                    action=step.action,
                    success=result.success,
                )

                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": result.content[:5000],
                        }
                    ],
                })
            else:
                # No tool calls — final answer
                text = "".join(b.text for b in text_blocks)
                parsed = self._parse_output(text)
                if parsed["type"] == "action":
                    # Text-based action (fallback parsing)
                    step.action = parsed["action"]
                    step.action_input = parsed["action_input"]
                    result = await self.registry.execute(step.action, **step.action_input)
                    step.observation = result.content[:3000]
                    self.steps.append(step)
                    messages.append({"role": "user", "content": f"Tool result: {result.content[:5000]}"})
                else:
                    step.final_answer = parsed["content"]
                    self.steps.append(step)
                    logger.info("agent_finished", iterations=i + 1, tool_calls=self.total_tool_calls)
                    return AgentResult(
                        success=True,
                        content=parsed["content"],
                        steps=self.steps,
                        tool_calls=self.total_tool_calls,
                        tokens_used=total_tokens,
                    )

        # Max iterations reached
        return AgentResult(
            success=False,
            content="Agent reached maximum iterations without a final answer.",
            steps=self.steps,
            tool_calls=self.total_tool_calls,
            tokens_used=total_tokens,
        )

    @property
    def total_tool_calls(self) -> int:
        return sum(1 for s in self.steps if s.action)
