import chromadb
from pathlib import Path
from src.config import settings
from src.rag.chunker import Chunk, chunk_file
from src.rag.embedder import Embedder, DummyEmbedder
from src.observability.logger import get_logger

logger = get_logger(__name__)


class CodebaseIndexer:
    """Manages ChromaDB collection for codebase RAG."""

    COLLECTION_NAME = "codebase"

    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or settings.chromadb_path
        Path(path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=path)
        self.embedder = self._init_embedder()

    def _init_embedder(self):
        if settings.anthropic_api_key:
            return Embedder()
        return DummyEmbedder()

    @property
    def collection(self):
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass

    async def index_directory(self, root: str, extensions: tuple[str, ...] | None = None) -> int:
        """Walk a directory, chunk files, embed, and store in ChromaDB."""
        if extensions is None:
            extensions = (".py", ".ts", ".tsx", ".js", ".md", ".yaml", ".yml", ".toml")

        root_path = Path(root).resolve()
        chunks: list[Chunk] = []

        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            if any(p.startswith(".") for p in file_path.parts):
                continue
            if "__pycache__" in file_path.parts:
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

        # Batch embed
        batch_size = 50
        col = self.collection

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.content for c in batch]
            try:
                embeddings = await self.embedder.embed(texts)
            except Exception:
                logger.warning("embed_failed, using dummy embedder")
                dummy = DummyEmbedder()
                embeddings = await dummy.embed(texts)

            ids = [f"{c.file_path}:{c.start_line}-{c.end_line}" for c in batch]
            metadatas = [
                {
                    "file_path": c.file_path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "chunk_type": c.chunk_type,
                    "name": c.name,
                }
                for c in batch
            ]
            doc_texts = [f"{c.file_path}:{c.start_line}-{c.end_line}\n{c.content[:2000]}" for c in batch]

            try:
                col.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=doc_texts)
            except Exception as e:
                logger.error("index_failed", batch_start=i, error=str(e))

        logger.info("indexed_chunks", count=len(chunks))
        return len(chunks)
