from typing import Sequence
from anthropic import Anthropic
from src.config import settings


class Embedder:
    """Generate embeddings using Anthropic API (voyage-code-3 for code)."""

    MODEL = "voyage-code-3"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.MODEL
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        result = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )
        return [e.embedding for e in result.embeddings]

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        results = await self.embed([query])
        return results[0]


class DummyEmbedder:
    """Fallback embedder using simple token-count vectors for testing / offline dev."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._simple_vector(t) for t in texts]

    async def embed_query(self, query: str) -> list[float]:
        return self._simple_vector(query)

    @staticmethod
    def _simple_vector(text: str, dim: int = 128) -> list[float]:
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        # Expand to required dim
        result = []
        for i in range(dim):
            b = h[i % len(h)]
            result.append((b / 255.0) * 2 - 1)
        return result
