"""
Comprehensive isolated tests for src/agents/memory.py.
"""
import json
import time

import pytest

from src.agents.memory import MemoryStore, MemoryEntry, MemoryCategory


class TestMemoryCategory:
    def test_values(self):
        assert MemoryCategory.USER_PREFERENCE.value == "user_preference"
        assert MemoryCategory.BUSINESS_CONTEXT.value == "business_context"
        assert MemoryCategory.LEARNED_BEHAVIOR.value == "learned_behavior"
        assert MemoryCategory.PROJECT_HISTORY.value == "project_history"
        assert MemoryCategory.RELATIONSHIP.value == "relationship"
        assert MemoryCategory.SKILL_KNOWLEDGE.value == "skill_knowledge"
        assert MemoryCategory.SOP_REFERENCE.value == "sop_reference"

    def test_count(self):
        assert len(MemoryCategory) == 7


class TestMemoryEntry:
    def test_creation(self):
        entry = MemoryEntry(
            content="test content",
            category=MemoryCategory.USER_PREFERENCE,
            metadata={"key": "value"},
            importance=0.8,
            tags=["tag1", "tag2"],
        )
        assert entry.content == "test content"
        assert entry.category == MemoryCategory.USER_PREFERENCE
        assert entry.importance == 0.8
        assert "tag1" in entry.tags

    def test_defaults(self):
        entry = MemoryEntry(content="test")
        assert entry.category is None
        assert entry.metadata == {}
        assert entry.importance == 0.5
        assert entry.tags == []
        assert entry.timestamp > 0


class TestMemoryStore:
    def test_empty_store(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        assert store._entries == []

    def test_store_entry(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        entry = MemoryEntry(content="test", category=MemoryCategory.USER_PREFERENCE)
        asyncio.run(store.store(entry))
        assert len(store._entries) == 1

    def test_store_persists(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store1 = MemoryStore(str(state_file))
        entry = MemoryEntry(content="persistent", category=MemoryCategory.USER_PREFERENCE)
        asyncio.run(store1.store(entry))
        store2 = MemoryStore(str(state_file))
        assert len(store2._entries) == 1
        assert store2._entries[0].content == "persistent"

    def test_store_max_entries(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file), max_entries=5)
        for i in range(10):
            entry = MemoryEntry(content=f"entry {i}")
            asyncio.run(store.store(entry))
        assert len(store._entries) == 5

    def test_search(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(content="hello world", importance=0.9))
        )
        asyncio.run(
            store.store(MemoryEntry(content="goodbye world", importance=0.5))
        )
        asyncio.run(
            store.store(MemoryEntry(content="something else", importance=0.8))
        )
        results = store.search("world")
        assert len(results) == 2

    def test_search_with_category(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(
                content="jewelry preference",
                category=MemoryCategory.USER_PREFERENCE,
            ))
        )
        asyncio.run(
            store.store(MemoryEntry(
                content="jewelry business",
                category=MemoryCategory.BUSINESS_CONTEXT,
            ))
        )
        results = store.search("jewelry", category=MemoryCategory.USER_PREFERENCE)
        assert len(results) == 1
        assert results[0].category == MemoryCategory.USER_PREFERENCE

    def test_search_with_limit(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        for i in range(20):
            asyncio.run(
                store.store(MemoryEntry(content=f"item {i} common"))
            )
        results = store.search("common", limit=5)
        assert len(results) == 5

    def test_search_orders_by_importance(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(content="low importance", importance=0.1))
        )
        asyncio.run(
            store.store(MemoryEntry(content="high importance", importance=0.9))
        )
        results = store.search("importance")
        assert results[0].importance >= results[1].importance

    def test_get_recent(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        for i in range(10):
            asyncio.run(
                store.store(MemoryEntry(content=f"entry {i}"))
            )
        recent = store.get_recent(5)
        assert len(recent) == 5

    def test_get_recent_empty(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        recent = store.get_recent()
        assert recent == []

    def test_get_by_category(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(content="a", category=MemoryCategory.USER_PREFERENCE))
        )
        asyncio.run(
            store.store(MemoryEntry(content="b", category=MemoryCategory.USER_PREFERENCE))
        )
        asyncio.run(
            store.store(MemoryEntry(content="c", category=MemoryCategory.BUSINESS_CONTEXT))
        )
        prefs = store.get_by_category(MemoryCategory.USER_PREFERENCE)
        assert len(prefs) == 2

    def test_delete(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(content="to_delete"))
        )
        asyncio.run(
            store.store(MemoryEntry(content="to_keep"))
        )
        result = store.delete("to_delete")
        assert result is True
        assert len(store._entries) == 1
        assert store._entries[0].content == "to_keep"

    def test_delete_nonexistent(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        result = store.delete("nonexistent")
        assert result is False

    def test_get_stats(self, tmp_path):
        state_file = tmp_path / "memory.json"
        store = MemoryStore(str(state_file))
        asyncio.run(
            store.store(MemoryEntry(content="a", category=MemoryCategory.USER_PREFERENCE))
        )
        asyncio.run(
            store.store(MemoryEntry(content="b", category=MemoryCategory.USER_PREFERENCE))
        )
        asyncio.run(
            store.store(MemoryEntry(content="c", category=MemoryCategory.BUSINESS_CONTEXT))
        )
        stats = store.get_stats()
        assert stats["total_entries"] == 3
        assert stats["categories"]["user_preference"] == 2
        assert stats["categories"]["business_context"] == 1

    def test_load_nonexistent(self, tmp_path):
        state_file = tmp_path / "nonexistent.json"
        store = MemoryStore(str(state_file))
        assert store._entries == []

    def test_load_corrupt_json(self, tmp_path):
        state_file = tmp_path / "memory.json"
        state_file.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            MemoryStore(str(state_file))


import asyncio
