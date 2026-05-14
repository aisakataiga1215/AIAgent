from langgraph.graph import StateGraph, END
from src.workflow.state import WorkflowState
from src.workflow.nodes import orchestrator_node, code_review_node, test_gen_node, aggregate_node
from src.observability.logger import get_logger

logger = get_logger(__name__)


def build_workflow() -> StateGraph:
    """Build the default multi-agent workflow graph."""
    graph = StateGraph(WorkflowState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("test_gen", test_gen_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        _route_after_plan,
        {
            "review": "code_review",
            "test": "test_gen",
            "aggregate": "aggregate",
            END: END,
        },
    )

    graph.add_edge("code_review", "orchestrator")
    graph.add_edge("test_gen", "orchestrator")
    graph.add_edge("aggregate", END)

    return graph


def _route_after_plan(state: WorkflowState) -> str:
    """Determine next node based on plan status."""
    plan = state.get("plan", [])
    pending = [p for p in plan if p.get("status") == "pending"]

    if not pending:
        return "aggregate"

    next_task = pending[0]
    next_task["status"] = "running"

    agent_type = next_task.get("agent", "")
    if agent_type == "code_review":
        return "review"
    if agent_type == "test_gen":
        return "test"

    return "aggregate"
