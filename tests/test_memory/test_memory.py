import pytest
from src.memory.short_term import ShortTermMemory, ConversationTurn
from src.memory.long_term import LongTermMemory
from src.memory.manager import MemoryManager


class TestShortTermMemory:
    def test_add_and_retrieve(self):
        mem = ShortTermMemory(max_turns=5)
        mem.add("user", "hello")
        mem.add("assistant", "hi there")
        assert len(mem) == 2

    def test_max_turns(self):
        mem = ShortTermMemory(max_turns=3)
        for i in range(5):
            mem.add("user", f"msg {i}")
        assert len(mem) == 3
        assert mem._history[-1].content == "msg 4"

    def test_to_messages(self):
        mem = ShortTermMemory(max_turns=5)
        mem.add("user", "hello")
        msgs = mem.to_messages()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_clear(self):
        mem = ShortTermMemory()
        mem.add("user", "hello")
        mem.clear()
        assert len(mem) == 0

    def test_get_last_n(self):
        mem = ShortTermMemory(max_turns=10)
        mem.add("user", "1")
        mem.add("user", "2")
        mem.add("user", "3")
        result = mem.get_history(last_n=2)
        assert len(result) == 2
        assert result[-1].content == "3"


class TestLongTermMemory:
    def test_set_and_get(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = LongTermMemory(db)
        mem.set("key1", {"name": "test"})
        assert mem.get("key1") == {"name": "test"}

    def test_get_default(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = LongTermMemory(db)
        assert mem.get("nonexistent", "default") == "default"

    def test_category(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = LongTermMemory(db)
        mem.set("k1", "v1", "preferences")
        mem.set("k2", "v2", "preferences")
        mem.set("k3", "v3", "rules")
        prefs = mem.get_by_category("preferences")
        assert len(prefs) == 2
        assert prefs["k1"] == "v1"

    def test_delete(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = LongTermMemory(db)
        mem.set("k1", "v1")
        mem.delete("k1")
        assert mem.get("k1") is None

    def test_session_log(self, tmp_path):
        db = str(tmp_path / "test.db")
        mem = LongTermMemory(db)
        mem.log_session("s1", "code_review", "review PR", "found 3 issues", 5, 100)
        # Should not raise


class TestMemoryManager:
    def test_message_flow(self):
        mgr = MemoryManager()
        mgr.add_message("user", "review this")
        mgr.add_message("assistant", "ok")
        conv = mgr.get_conversation()
        assert len(conv) == 2

    def test_remember_and_recall(self, tmp_path):
        db = str(tmp_path / "test.db")
        ltm = LongTermMemory(db)
        mgr = MemoryManager(long_term=ltm)
        mgr.remember("pref_review_strictness", "high")
        assert mgr.recall("pref_review_strictness") == "high"

    def test_log_task(self, tmp_path):
        db = str(tmp_path / "test.db")
        ltm = LongTermMemory(db)
        mgr = MemoryManager(long_term=ltm)
        mgr.log_completed_task("sid1", "review", "task", "summary", 3, 50)
        # Should not raise
