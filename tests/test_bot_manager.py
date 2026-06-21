"""
Comprehensive isolated tests for src/bots/bot_manager.py.
"""
import asyncio

import pytest

from src.bots.bot_core import TelegramBot, BotConfig, BotState
from src.bots.bot_manager import BotManager


class TestBotManager:
    def test_init(self):
        mgr = BotManager()
        assert mgr._bots == {}
        assert mgr._running is False

    def test_register(self):
        mgr = BotManager()
        config = BotConfig(token="t", bot_id="b1", name="Bot1", business_id="biz")
        bot = TelegramBot(config)
        mgr.register(bot)
        assert "b1" in mgr.list_bots()

    def test_register_overwrites(self):
        mgr = BotManager()
        config1 = BotConfig(token="t1", bot_id="b1", name="Bot1", business_id="biz")
        config2 = BotConfig(token="t2", bot_id="b1", name="Bot2", business_id="biz")
        mgr.register(TelegramBot(config1))
        mgr.register(TelegramBot(config2))
        assert mgr.get("b1").config.name == "Bot2"

    def test_unregister(self):
        mgr = BotManager()
        config = BotConfig(token="t", bot_id="b1", name="Bot1", business_id="biz")
        mgr.register(TelegramBot(config))
        mgr.unregister("b1")
        assert mgr.get("b1") is None

    def test_unregister_nonexistent(self):
        mgr = BotManager()
        mgr.unregister("nonexistent")

    def test_get(self):
        mgr = BotManager()
        config = BotConfig(token="t", bot_id="b1", name="Bot1", business_id="biz")
        bot = TelegramBot(config)
        mgr.register(bot)
        assert mgr.get("b1") is bot

    def test_get_nonexistent(self):
        mgr = BotManager()
        assert mgr.get("nonexistent") is None

    def test_list_bots(self):
        mgr = BotManager()
        for i in range(3):
            config = BotConfig(token=f"t{i}", bot_id=f"b{i}", name=f"Bot{i}", business_id="biz")
            mgr.register(TelegramBot(config))
        assert len(mgr.list_bots()) == 3

    def test_list_bots_empty(self):
        mgr = BotManager()
        assert mgr.list_bots() == []

    def test_start_all_no_bots(self):
        mgr = BotManager()
        asyncio.run(mgr.start_all())
        assert mgr._running is True

    def test_stop_all_no_bots(self):
        mgr = BotManager()
        asyncio.run(mgr.stop_all())
        assert mgr._running is False

    def test_start_bot_nonexistent(self):
        mgr = BotManager()
        asyncio.run(mgr.start_bot("nonexistent"))

    def test_stop_bot_nonexistent(self):
        mgr = BotManager()
        asyncio.run(mgr.stop_bot("nonexistent"))

    def test_multiple_bots(self):
        mgr = BotManager()
        for i in range(5):
            config = BotConfig(token=f"t{i}", bot_id=f"b{i}", name=f"Bot{i}", business_id="biz")
            mgr.register(TelegramBot(config))
        assert len(mgr.list_bots()) == 5
        mgr.unregister("b2")
        assert len(mgr.list_bots()) == 4
        assert mgr.get("b2") is None
