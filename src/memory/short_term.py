from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationTurn:
    role: str  # user | assistant | tool
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """In-memory conversation history for a single session."""

    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self._history: list[ConversationTurn] = []

    def add(self, role: str, content: str, **meta: Any) -> None:
        self._history.append(ConversationTurn(role=role, content=content, metadata=meta))
        if len(self._history) > self.max_turns:
            self._history = self._history[-self.max_turns:]

    def get_history(self, last_n: int | None = None) -> list[ConversationTurn]:
        if last_n:
            return self._history[-last_n:]
        return list(self._history)

    def to_messages(self) -> list[dict[str, Any]]:
        """Convert to Anthropic messages format."""
        return [{"role": t.role, "content": t.content} for t in self._history]

    def clear(self) -> None:
        self._history = []

    def __len__(self) -> int:
        return len(self._history)
