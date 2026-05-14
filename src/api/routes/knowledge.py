from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from src.rag.ingestion import ingest_codebase
from src.rag.retriever import HybridRetriever

router = APIRouter(tags=["knowledge"])


class IngestRequest(BaseModel):
    repo: str = "."
    reset: bool = False


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/knowledge/ingest")
async def ingest(req: IngestRequest):
    """Index a codebase into the knowledge base."""
    try:
        count = await ingest_codebase(root=req.repo, reset=req.reset)
        return {"success": True, "chunks_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/search")
async def search(query: str = Query(...), top_k: int = Query(5)):
    """Search the indexed codebase."""
    retriever = HybridRetriever()
    results = retriever.search(query, top_k=top_k)
    return {"query": query, "results": results, "count": len(results)}
