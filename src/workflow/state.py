from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict):
    """Shared state across all workflow nodes."""
    messages: Annotated[list, add_messages]
    task: str
    plan: list[dict[str, Any]]  # [{agent, subtask, status}]
    agent_outputs: dict[str, str]  # {agent_name: output}
    errors: list[str]
    status: str  # pending | running | completed | failed
    metadata: dict[str, Any]  # repo path, PR number, etc.
