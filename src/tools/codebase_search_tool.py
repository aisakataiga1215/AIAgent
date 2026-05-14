from src.tools.base import BaseTool, ToolResult
from src.rag.indexer import CodebaseIndexer
from src.rag.retriever import HybridRetriever


class CodebaseSearchTool(BaseTool):
    name = "codebase_search"
    description = "Semantically search the codebase. Returns relevant code snippets, file paths, and line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language query about the codebase"},
            "top_k": {"type": "integer", "description": "Number of results to return. Default 5."},
        },
        "required": ["query"],
    }

    def __init__(self) -> None:
        self.retriever = HybridRetriever()

    async def execute(self, query: str, top_k: int = 5) -> ToolResult:
        try:
            results = self.retriever.search(query, top_k=top_k)
        except Exception as e:
            return ToolResult(success=False, content=f"Search failed: {e}. Try running 'devflow ingest' first.")

        if not results:
            return ToolResult(success=True, content="No results found. The codebase may not be indexed yet.", metadata={"count": 0})

        output = []
        for r in results:
            meta = r["metadata"]
            file_path = meta.get("file_path", "unknown")
            name = meta.get("name", "")
            line = meta.get("start_line", "")
            label = f"{name}()" if name else file_path
            output.append(f"### {label} — {file_path}:{line}")
            output.append(r["document"][:800])
            output.append("")

        return ToolResult(
            success=True,
            content="\n".join(output),
            metadata={"count": len(results), "query": query},
        )
