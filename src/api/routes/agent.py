from fastapi import APIRouter

router = APIRouter(tags=["agent"])


@router.get("/agent/list")
async def list_agents():
    """List all available agents and their status."""
    return {
        "agents": [
            {"name": "code_review", "status": "idle", "type": "ReAct", "tools": 5},
            {"name": "orchestrator", "status": "idle", "type": "Plan-Execute", "tools": 1},
            {"name": "test_gen", "status": "planned", "type": "ReAct", "tools": 4},
            {"name": "doc_manager", "status": "planned", "type": "ReAct", "tools": 3},
            {"name": "knowledge", "status": "planned", "type": "ReAct", "tools": 2},
        ]
    }
