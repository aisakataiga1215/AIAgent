from rank_bm25 import BM25Okapi
from src.config import settings
from src.rag.embedder import Embedder, DummyEmbedder
from src.rag.indexer import CodebaseIndexer
from src.observability.logger import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    """Hybrid retrieval: semantic (ChromaDB) + keyword (BM25) + reranker."""

    def __init__(self, indexer: CodebaseIndexer | None = None) -> None:
        self.indexer = indexer or CodebaseIndexer()
        self.embedder = self.indexer.embedder if isinstance(self.indexer.embedder, Embedder) else Embedder()

    def semantic_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Vector semantic search via ChromaDB."""
        col = self.indexer.collection
        try:
            results = col.query(query_texts=[query], n_results=top_k)
        except Exception:
            # Fallback: use get() + manual embedding
            try:
                embedder = DummyEmbedder()
                import asyncio
                q_embedding = asyncio.get_event_loop().run_until_complete(embedder.embed_query(query))
                results = col.query(query_embeddings=[q_embedding], n_results=top_k)
            except Exception:
                return []

        docs = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                docs.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                })
        return docs

    def keyword_search(self, query: str, top_k: int = 10) -> list[dict]:
        """BM25 keyword search over indexed chunks."""
        col = self.indexer.collection
        try:
            all_data = col.get()
        except Exception:
            return []

        if not all_data or not all_data["documents"]:
            return []

        tokenized = [doc.lower().split() for doc in all_data["documents"]]
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())

        # Rank by score
        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        docs = []
        for idx, score in ranked:
            docs.append({
                "id": all_data["ids"][idx],
                "document": all_data["documents"][idx],
                "metadata": all_data["metadatas"][idx] if all_data["metadatas"] else {},
                "score": float(score),
            })
        return docs

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Hybrid search: combine semantic + keyword results with reciprocal rank fusion."""
        semantic = self.semantic_search(query, top_k=top_k * 2)
        keyword = self.keyword_search(query, top_k=top_k * 2)

        # Reciprocal Rank Fusion
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
