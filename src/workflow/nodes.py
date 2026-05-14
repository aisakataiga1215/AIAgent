import asyncio
from src.workflow.state import WorkflowState
from src.agents.code_review import review_repository
from src.observability.logger import get_logger

logger = get_logger(__name__)


async def orchestrator_node(state: WorkflowState) -> dict:
    """Orchestrator: create or check execution plan."""
    task = state.get("task", "")
    plan = state.get("plan", [])

    if not plan:
        # Initial plan creation
        plan = [
            {"agent": "code_review", "subtask": "Review code changes for issues", "status": "pending"},
        ]
        state["plan"] = plan
        state["status"] = "running"
        logger.info("orchestrator_plan", task=task, steps=len(plan))

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

    # Mark current task as done
    for p in state.get("plan", []):
        if p.get("agent") == "code_review" and p.get("status") == "running":
            p["status"] = "done"

    return {"agent_outputs": agent_outputs, "plan": state["plan"]}


async def aggregate_node(state: WorkflowState) -> dict:
    """Aggregate all agent outputs into a final report."""
    outputs = state.get("agent_outputs", {})
    errors = state.get("errors", [])

    sections = [f"# DevFlow Workflow Report\n"]
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
