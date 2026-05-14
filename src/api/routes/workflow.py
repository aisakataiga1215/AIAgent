from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.workflow.templates import WORKFLOW_TEMPLATES
from src.workflow.state import WorkflowState
from src.workflow.nodes import orchestrator_node, code_review_node, test_gen_node, aggregate_node

router = APIRouter(tags=["workflow"])


class WorkflowRequest(BaseModel):
    name: str = "pr-review"
    repo: str = "."
    target: str = "HEAD~1"


class WorkflowResponse(BaseModel):
    status: str
    report: str
    errors: list[str]


@router.post("/workflow", response_model=WorkflowResponse)
async def run_workflow(req: WorkflowRequest) -> WorkflowResponse:
    """Run a multi-agent workflow."""
    if req.name not in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown workflow: {req.name}")

    template = WORKFLOW_TEMPLATES[req.name](repo=req.repo, target=req.target)

    state: WorkflowState = {
        "messages": [],
        "task": template["task"],
        "plan": template["plan"],
        "agent_outputs": {},
        "errors": [],
        "status": "pending",
        "metadata": template["metadata"],
    }

    update = await orchestrator_node(state)
    state.update(update)

    for p in state["plan"]:
        if p["agent"] == "code_review":
            update = await code_review_node(state)
            state.update(update)
        elif p["agent"] == "test_gen":
            update = await test_gen_node(state)
            state.update(update)

    final = await aggregate_node(state)
    state.update(final)

    messages = state.get("messages", [])
    report = messages[-1]["content"] if messages else "No output"

    return WorkflowResponse(
        status=state["status"],
        report=report,
        errors=state.get("errors", []),
    )


@router.get("/workflow/templates")
async def list_templates():
    """List available workflow templates."""
    return {"templates": list(WORKFLOW_TEMPLATES.keys())}
