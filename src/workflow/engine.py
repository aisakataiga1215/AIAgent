from langgraph.graph import StateGraph, END
from src.workflow.state import WorkflowState
from src.workflow.nodes import orchestrator_node, code_review_node, aggregate_node
from src.observability.logger import get_logger

logger = get_logger(__name__)


def build_workflow() -> StateGraph:
    """Build the default multi-agent workflow graph."""
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("code_review", code_review_node)
    graph.add_node("aggregate", aggregate_node)

    # Set entry point
    graph.set_entry_point("orchestrator")

    # Orchestrator routes to agents or aggregate
    graph.add_conditional_edges(
        "orchestrator",
        _route_after_plan,
        {
            "review": "code_review",
            "aggregate": "aggregate",
            END: END,
        },
    )

    # Agent nodes go back to orchestrator
    graph.add_edge("code_review", "orchestrator")

    # Aggregate is the end
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

    return "aggregate"
