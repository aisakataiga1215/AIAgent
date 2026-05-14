import httpx
from src.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information. Returns titles, URLs, and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {"type": "integer", "description": "Maximum results. Default 5."},
        },
        "required": ["query"],
    }

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                    headers={"User-Agent": "DevFlowAI/0.1"},
                )
                data = resp.json()
                results = []
                for item in data.get("RelatedTopics", [])[:max_results]:
                    title = item.get("Text", "")
                    url = item.get("FirstURL", "")
                    results.append(f"- {title}\n  {url}")

                if not results:
                    return ToolResult(success=True, content=f"No results found for: {query}")

                return ToolResult(
                    success=True,
                    content=f"Search results for '{query}':\n\n" + "\n\n".join(results),
                )
        except Exception as e:
            return ToolResult(success=False, content=f"Search failed: {e}")
