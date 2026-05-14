from typing import Any
from src.memory.short_term import ShortTermMemory
from src.memory.long_term import LongTermMemory


class MemoryManager:
    """Unified interface for short-term (session) and long-term (persistent) memory."""

    def __init__(self, long_term: LongTermMemory | None = None) -> None:
        self.short_term = ShortTermMemory()
        self.long_term = long_term or LongTermMemory()

    # Short-term (current conversation)
    def add_message(self, role: str, content: str) -> None:
        self.short_term.add(role, content)

    def get_conversation(self) -> list[dict[str, Any]]:
        return self.short_term.to_messages()

    def clear_conversation(self) -> None:
        self.short_term.clear()

    # Long-term (persistent preferences/knowledge)
    def remember(self, key: str, value: Any, category: str = "general") -> None:
        self.long_term.set(key, value, category)

    def recall(self, key: str, default: Any = None) -> Any:
        return self.long_term.get(key, default)

    def recall_category(self, category: str) -> dict[str, Any]:
        return self.long_term.get_by_category(category)

    def forget(self, key: str) -> None:
        self.long_term.delete(key)

    # Session logging
    def log_completed_task(
        self, session_id: str, agent_name: str, task: str, result_summary: str, tool_calls: int = 0, tokens_used: int = 0
    ) -> None:
        self.long_term.log_session(session_id, agent_name, task, result_summary, tool_calls, tokens_used)
