from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.agents.code_review import review_repository

router = APIRouter(tags=["review"])


class ReviewRequest(BaseModel):
    repo: str = "."
    target: str = "HEAD~1"


class ReviewResponse(BaseModel):
    success: bool
    content: str
    tool_calls: int
    tokens_used: int


@router.post("/review", response_model=ReviewResponse)
async def create_review(req: ReviewRequest) -> ReviewResponse:
    """Run a Code Review Agent on a repository."""
    try:
        result = await review_repository(workspace=req.repo, target=req.target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ReviewResponse(
        success=result.success,
        content=result.content,
        tool_calls=result.tool_calls,
        tokens_used=result.tokens_used,
    )


@router.get("/review/status")
async def review_status():
    """Get review agent status."""
    return {"status": "idle", "available_tools": ["git_diff", "read_file", "ast_analyze"]}
