"""
Comprehensive isolated tests for src/telegram/forum.py.
"""
import pytest

from src.telegram.forum import TelegramForumManager


class TestForumManager:
    def test_init(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        assert fm._topics == {}

    def test_get_topic_empty(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        assert fm.get_topic(123) is None

    def test_list_topics_empty(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        assert fm.list_topics() == []

    def test_create_topic_no_bot(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        import asyncio
        result = asyncio.run(
            fm.create_topic(123, "Test Topic")
        )
        assert result is None

    def test_close_topic_no_bot(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        import asyncio
        result = asyncio.run(
            fm.close_topic(123, 456)
        )
        assert result is False

    def test_reopen_topic_no_bot(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        import asyncio
        result = asyncio.run(
            fm.reopen_topic(123, 456)
        )
        assert result is False

    def test_edit_topic_no_bot(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        import asyncio
        result = asyncio.run(
            fm.edit_topic(123, 456, "New Name")
        )
        assert result is False

    def test_delete_topic_no_bot(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        import asyncio
        result = asyncio.run(
            fm.delete_topic(123, 456)
        )
        assert result is False

    def test_topics_stored(self):
        class FakeBot:
            _bot = None
        fm = TelegramForumManager(FakeBot())
        fm._topics[123] = {"name": "Test", "message_thread_id": 123}
        assert fm.get_topic(123) is not None
        assert len(fm.list_topics()) == 1
