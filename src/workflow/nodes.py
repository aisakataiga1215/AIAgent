import asyncio
from src.workflow.state import WorkflowState
from src.agents.code_review import review_repository
from src.agents.test_gen import generate_tests
from src.observability.logger import get_logger

logger = get_logger(__name__)


async def orchestrator_node(state: WorkflowState) -> dict:
    """Orchestrator: create or check execution plan."""
    plan = state.get("plan", [])

    if not plan:
        plan = [
            {"agent": "code_review", "subtask": "Review code changes for issues", "status": "pending"},
        ]
        state["plan"] = plan
        state["status"] = "running"
        logger.info("orchestrator_plan", task=state.get("task", ""), steps=len(plan))

    return state


async def code_review_node(state: WorkflowState) -> dict:
    """Run the Code Review Agent."""
    repo = state.get("metadata", {}).get("repo", ".")
    target = state.get("metadata", {}).get("target", "HEAD~1")

    logger.info("code_review_start", repo=repo, target=target)
    result = await review_repository(workspace=repo, target=target)

    agent_outputs = state.get("agent_outputs", {})
    if result.success:
        agent_outputs["code_review"] = result.content
    else:
        agent_outputs["code_review"] = f"Review failed: {result.content}"
        state.setdefault("errors", []).append(f"Code review failed: {result.content}")

    _mark_done(state, "code_review")
    return {"agent_outputs": agent_outputs, "plan": state["plan"]}


async def test_gen_node(state: WorkflowState) -> dict:
    """Run the Test Generation Agent."""
    repo = state.get("metadata", {}).get("repo", ".")

    logger.info("test_gen_start", repo=repo)
    result = await generate_tests(workspace=repo)

    agent_outputs = state.get("agent_outputs", {})
    if result.success:
        agent_outputs["test_gen"] = result.content
    else:
        agent_outputs["test_gen"] = f"Test generation failed: {result.content}"
        state.setdefault("errors", []).append(f"Test generation failed: {result.content}")

    _mark_done(state, "test_gen")
    return {"agent_outputs": agent_outputs, "plan": state["plan"]}


def _mark_done(state: WorkflowState, agent_name: str) -> None:
    for p in state.get("plan", []):
        if p.get("agent") == agent_name and p.get("status") == "running":
            p["status"] = "done"


async def aggregate_node(state: WorkflowState) -> dict:
    """Aggregate all agent outputs into a final report."""
    outputs = state.get("agent_outputs", {})
    errors = state.get("errors", [])

    sections = [f"# AgentFlow Workflow Report\n"]
    sections.append(f"## Task: {state.get('task', 'N/A')}\n")

    for agent_name, output in outputs.items():
        sections.append(f"### {agent_name}\n{output}\n")

    if errors:
        sections.append("### Errors\n")
        for e in errors:
            sections.append(f"- {e}")

    report = "\n".join(sections)
    state["status"] = "completed"

    return {"status": "completed", "messages": [{"role": "assistant", "content": report}]}
