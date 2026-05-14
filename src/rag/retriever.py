import asyncio
from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from src.config import settings
from src.rag.embedder import Embedder, DummyEmbedder
from src.rag.indexer import CodebaseIndexer
from src.observability.logger import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """Hybrid retrieval: semantic (Qdrant) + keyword (BM25) + RRF fusion."""

    COLLECTION_NAME = "codebase"

    def __init__(self, indexer: CodebaseIndexer | None = None) -> None:
        self.indexer = indexer or CodebaseIndexer()
        self.client = self.indexer.client
        self.embedder = self.indexer.embedder if isinstance(self.indexer.embedder, Embedder) else Embedder()

    def semantic_search(self, query: str, top_k: int = 10, filter_by: dict | None = None) -> list[dict]:
        """Vector semantic search via Qdrant."""
        try:
            loop = asyncio.get_event_loop()
            q_embedding = loop.run_until_complete(self.embedder.embed_query(query))
        except Exception:
            dummy = DummyEmbedder()
            q_embedding = asyncio.get_event_loop().run_until_complete(dummy.embed_query(query))

        qdrant_filter = None
        if filter_by:
            conditions = []
            for key, value in filter_by.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            if conditions:
                qdrant_filter = Filter(must=conditions)

        try:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=q_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
        except Exception:
            return []

        docs = []
        for hit in results:
            payload = hit.payload or {}
            docs.append({
                "id": payload.get("doc_id", str(hit.id)),
                "document": payload.get("text", ""),
                "metadata": {
                    "file_path": payload.get("file_path", ""),
                    "start_line": payload.get("start_line", 0),
                    "end_line": payload.get("end_line", 0),
                    "chunk_type": payload.get("chunk_type", ""),
                    "name": payload.get("name", ""),
                },
                "score": 1.0 - min(hit.score, 1.0),
            })
        return docs

    def keyword_search(self, query: str, top_k: int = 10) -> list[dict]:
        """BM25 keyword search over all indexed chunks."""
        try:
            all_points = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                with_payload=True,
                limit=1000,
            )[0]
        except Exception:
            return []

        if not all_points:
            return []

        doc_texts = [p.payload.get("text", "") for p in all_points if p.payload]
        tokenized = [doc.lower().split() for doc in doc_texts]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())

        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        docs = []
        for idx, score in ranked:
            payload = all_points[idx].payload or {}
            docs.append({
                "id": payload.get("doc_id", str(all_points[idx].id)),
                "document": payload.get("text", ""),
                "metadata": {
                    "file_path": payload.get("file_path", ""),
                    "start_line": payload.get("start_line", 0),
                    "end_line": payload.get("end_line", 0),
                    "chunk_type": payload.get("chunk_type", ""),
                    "name": payload.get("name", ""),
                },
                "score": float(score),
            })
        return docs

    def search(self, query: str, top_k: int = 10, filter_by: dict | None = None) -> list[dict]:
        """Hybrid search: combine semantic + keyword results with reciprocal rank fusion."""
        semantic = self.semantic_search(query, top_k=top_k * 2, filter_by=filter_by)
        keyword = self.keyword_search(query, top_k=top_k * 2)

        k = 60
        scores: dict[str, float] = {}
        docs: dict[str, dict] = {}

        for rank, doc in enumerate(semantic):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            docs[doc_id] = doc

        for rank, doc in enumerate(keyword):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
            docs[doc_id] = doc

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        result = []
        for doc_id, score in ranked:
            doc = docs[doc_id]
            doc["fusion_score"] = score
            result.append(doc)

        return result
