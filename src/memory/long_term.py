import sqlite3
import json
from datetime import datetime, timezone
from typing import Any
from pathlib import Path
from src.config import settings
from src.observability.logger import get_logger

logger = get_logger(__name__)


class LongTermMemory:
    """Persistent memory stored in SQLite. Stores user preferences, project rules, and session summaries."""

    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or _db_path_from_url(settings.database_url)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                task TEXT,
                result_summary TEXT,
                tool_calls INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
            CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        """)
        self.conn.commit()

    def set(self, key: str, value: Any, category: str = "general") -> None:
        now = datetime.now(timezone.utc).isoformat()
        data = json.dumps(value, ensure_ascii=False)
        self.conn.execute(
            "INSERT OR REPLACE INTO memories (key, value, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (key, data, category, now, now),
        )
        self.conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM memories WHERE key = ?", (key,)).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    def get_by_category(self, category: str) -> dict[str, Any]:
        rows = self.conn.execute(
            "SELECT key, value FROM memories WHERE category = ?", (category,)
        ).fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    def delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self.conn.commit()

    def list_keys(self, category: str | None = None) -> list[str]:
        if category:
            rows = self.conn.execute(
                "SELECT key FROM memories WHERE category = ?", (category,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT key FROM memories").fetchall()
        return [r["key"] for r in rows]

    def log_session(
        self,
        session_id: str,
        agent_name: str,
        task: str,
        result_summary: str,
        tool_calls: int = 0,
        tokens_used: int = 0,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO session_log (session_id, agent_name, task, result_summary, tool_calls, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, agent_name, task, result_summary, tool_calls, tokens_used, now),
        )
        self.conn.commit()


def _db_path_from_url(url: str) -> str:
    """Extract file path from SQLite URL like 'sqlite:///data/devflow.db'."""
    return url.replace("sqlite:///", "")
