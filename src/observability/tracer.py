from contextlib import contextmanager
from typing import Any
from src.config import settings
from src.observability.logger import get_logger

logger = get_logger(__name__)


class Tracer:
    """Lightweight tracing wrapper. Integrates with Langfuse when configured."""

    def __init__(self) -> None:
        self._langfuse = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse
                self._langfuse = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except ImportError:
                logger.warning("langfuse_not_installed")

    @contextmanager
    def trace(self, name: str, **metadata: Any):
        if self._langfuse:
            trace = self._langfuse.trace(name=name, metadata=metadata)
            try:
                yield trace
            finally:
                trace.update(status="completed")
        else:
            # No-op trace
            logger.info("trace", name=name, **metadata)
            yield None

    def log_agent_step(self, trace: Any, iteration: int, action: str, success: bool) -> None:
        if trace and self._langfuse:
            trace.span(
                name=f"step_{iteration}",
                input={"action": action},
                output={"success": success},
            )

    def flush(self) -> None:
        if self._langfuse:
            self._langfuse.flush()


tracer = Tracer()
