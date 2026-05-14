import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.base import ReActAgent, AgentStep, AgentResult, SYSTEM_PROMPT_TEMPLATE
from src.tools.registry import ToolRegistry
from src.tools.base import BaseTool, ToolResult


class EchoTool(BaseTool):
    name = "echo"
    description = "Echo back the input"
    parameters = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

    async def execute(self, text: str = "") -> ToolResult:
        return ToolResult(success=True, content=f"Echo: {text}")


@pytest.fixture
def agent_with_tools():
    registry = ToolRegistry()
    registry.register(EchoTool())
    agent = ReActAgent(registry, model="claude-haiku-4-5-20251001")
    agent.client = MagicMock()
    return agent


def test_build_system_prompt(agent_with_tools):
    prompt = agent_with_tools._build_system_prompt()
    assert "Code Review Agent" in prompt or "Agent" in prompt
    assert "echo" in prompt


def test_parse_action_output(agent_with_tools):
    result = agent_with_tools._parse_output(
        'Action: echo\nAction Input: {"text": "hello"}'
    )
    assert result["type"] == "action"
    assert result["action"] == "echo"
    assert result["action_input"] == {"text": "hello"}


def test_parse_final_output(agent_with_tools):
    result = agent_with_tools._parse_output("Final Answer:\nEverything looks good.")
    assert result["type"] == "final"
    assert "Everything looks good" in result["content"]


def test_agent_result_defaults():
    result = AgentResult(success=True, content="test")
    assert result.tool_calls == 0
    assert result.tokens_used == 0
    assert result.steps == []


def test_agent_step_defaults():
    step = AgentStep(iteration=1)
    assert step.thought == ""
    assert step.action == ""


@pytest.mark.asyncio
async def test_run_with_final_answer(agent_with_tools):
    mock_response = MagicMock()
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Final Answer:\nAll clear, no issues found."
    mock_response.content = [text_block]

    agent_with_tools.client.messages.create.return_value = mock_response

    result = await agent_with_tools.run("Review this code")
    assert result.success
    assert "All clear" in result.content
    assert result.tokens_used == 15


@pytest.mark.asyncio
async def test_run_with_tool_call(agent_with_tools):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "echo"
    tool_block.id = "tool_123"
    tool_block.input = {"text": "hello"}

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Let me echo something first."

    response1 = MagicMock()
    response1.usage.input_tokens = 10
    response1.usage.output_tokens = 5
    response1.content = [text_block, tool_block]

    text_block2 = MagicMock()
    text_block2.type = "text"
    text_block2.text = "Final Answer:\nDone after echo."

    response2 = MagicMock()
    response2.usage.input_tokens = 8
    response2.usage.output_tokens = 4
    response2.content = [text_block2]

    agent_with_tools.client.messages.create.side_effect = [response1, response2]

    result = await agent_with_tools.run("Test with echo")
    assert result.success
    assert result.tool_calls == 1
    assert "Done after echo" in result.content
    assert len(result.steps) == 2


def test_template_formatting():
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        role="Tester",
        role_description="Tests things.",
        tool_descriptions="- **echo**: Echo back",
    )
    assert "Tester" in prompt
    assert "echo" in prompt
    assert "ReAct" in prompt
