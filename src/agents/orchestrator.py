from src.agents.base import ReActAgent, AgentResult
from src.tools.registry import ToolRegistry
from src.tools.filesystem_tool import FileReadTool
from src.agents.code_review import CodeReviewAgent


class OrchestratorAgent(ReActAgent):
    """Plan-and-Execute orchestrator. Plans multi-step tasks and dispatches to specialist agents."""

    role = "Orchestrator Agent"
    role_description = (
        "You are a workflow orchestrator. Your job is to understand the user's intent, "
        "decompose it into subtasks, dispatch each to a specialist agent, and aggregate the results."
    )
    system_prompt_extra = """
## Your Process
1. Analyze the user's task
2. Break it down into subtasks
3. For each subtask, determine which specialist agent should handle it
4. After all agents report back, synthesize the findings

## Available Specialist Agents
- **code_review**: Reviews code for security, correctness, performance, and style

## Output Format
Plan the work as:
```
Plan:
1. [agent_name]: subtask description
2. [agent_name]: subtask description
...

Then dispatch to each agent, wait for results, and provide a Final Answer.
"""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        model: str | None = None,
        max_iterations: int = 10,
    ) -> None:
        if registry is None:
            registry = ToolRegistry()
            registry.register(FileReadTool())
        super().__init__(registry, model, max_iterations)
        self._specialist_agents = {
            "code_review": CodeReviewAgent,
        }

    async def dispatch(self, agent_name: str, task: str) -> AgentResult:
        """Dispatch a subtask to a specialist agent."""
        if agent_name in self._specialist_agents:
            # Create a fresh agent instance and run
            agent_class = self._specialist_agents[agent_name]
            agent = agent_class(self.registry)
            return await agent.run(task)
        else:
            return AgentResult(success=False, content=f"Unknown agent: {agent_name}")
