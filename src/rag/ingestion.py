from pathlib import Path
from src.rag.indexer import CodebaseIndexer


async def ingest_codebase(
    root: str = ".",
    reset: bool = False,
    extensions: tuple[str, ...] | None = None,
) -> int:
    """Ingest a codebase into the RAG index. Returns number of chunks indexed."""
    indexer = CodebaseIndexer()
    if reset:
        indexer.reset()
    return await indexer.index_directory(root, extensions=extensions)
