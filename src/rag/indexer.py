from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.config import settings
from src.rag.chunker import Chunk, chunk_file
from src.rag.embedder import Embedder, DummyEmbedder
from src.observability.logger import get_logger

logger = get_logger(__name__)

VECTOR_SIZE = 1024  # voyage-code-3 dimension


class CodebaseIndexer:
    """Manages Qdrant collection for codebase RAG."""

    COLLECTION_NAME = "codebase"

    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or settings.qdrant_path
        self.db_dir = Path(path)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.client = QdrantClient(path=str(self.db_dir))
        self.embedder = self._init_embedder()
        self._ensure_collection()

    def _init_embedder(self):
        if settings.anthropic_api_key:
            return Embedder()
        return DummyEmbedder()

    def _ensure_collection(self) -> None:
        collections = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._ensure_collection()

    def count(self) -> int:
        info = self.client.count(self.COLLECTION_NAME)
        return info.count

    async def index_directory(self, root: str, extensions: tuple[str, ...] | None = None) -> int:
        """Walk a directory, chunk files, embed, and store in Qdrant."""
        if extensions is None:
            extensions = (".py", ".ts", ".tsx", ".js", ".md", ".yaml", ".yml", ".toml")

        root_path = Path(root).resolve()
        chunks: list[Chunk] = []

        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            if any(p.startswith(".") for p in file_path.parts):
                continue
            if "__pycache__" in file_path.parts or "node_modules" in file_path.parts:
                continue
            if file_path.suffix not in extensions:
                continue

            try:
                file_chunks = chunk_file(file_path)
                chunks.extend(file_chunks)
            except Exception as e:
                logger.warning("chunk_failed", path=str(file_path), error=str(e))

        if not chunks:
            logger.info("no_chunks", root=root)
            return 0

        batch_size = 50

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.content for c in batch]
            try:
                embeddings = await self.embedder.embed(texts)
            except Exception:
                logger.warning("embed_failed, using dummy embedder")
                dummy = DummyEmbedder()
                embeddings = await dummy.embed(texts)

            points = []
            for j, chunk in enumerate(batch):
                doc_id = f"{chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
                # Qdrant needs UUID or int64 as point id; use a deterministic hash
                point_id = abs(hash(doc_id)) % (2**63)
                points.append(PointStruct(
                    id=point_id,
                    vector=embeddings[j],
                    payload={
                        "doc_id": doc_id,
                        "file_path": chunk.file_path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "chunk_type": chunk.chunk_type,
                        "name": chunk.name,
                        "content": chunk.content[:3000],
                        "text": f"{chunk.file_path}:{chunk.start_line}\n{chunk.content[:2000]}",
                    },
                ))

            try:
                self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)
            except Exception as e:
                logger.error("index_failed", batch_start=i, error=str(e))

        logger.info("indexed_chunks", count=len(chunks))
        return len(chunks)
