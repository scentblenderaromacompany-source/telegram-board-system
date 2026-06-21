"""
Comprehensive isolated tests for src/telegram/webhook.py.
"""
import asyncio
import json
import time

import pytest

from src.telegram.webhook import TelegramWebhookManager


class TestWebhookManagerInit:
    def test_default_state_file(self):
        wm = TelegramWebhookManager()
        assert wm._state_file.name == "telegram_webhooks.json"

    def test_custom_state_file(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        assert wm._webhooks == {}


class TestRegister:
    def test_register_webhook(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com/hook", "secret123")
        wh = wm.get("bot1")
        assert wh is not None
        assert wh["url"] == "https://example.com/hook"
        assert wh["secret_token"] == "secret123"
        assert wh["active"] is True

    def test_register_without_secret(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com/hook")
        wh = wm.get("bot1")
        assert wh["secret_token"] is None

    def test_register_with_allowed_updates(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com/hook", allowed_updates=["message"])
        wh = wm.get("bot1")
        assert wh["allowed_updates"] == ["message"]

    def test_register_overwrites(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://old.com")
        wm.register("bot1", "https://new.com")
        wh = wm.get("bot1")
        assert wh["url"] == "https://new.com"


class TestRemove:
    def test_remove_existing(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com")
        wm.remove("bot1")
        assert wm.get("bot1") is None

    def test_remove_nonexistent(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.remove("nonexistent")


class TestVerifySecret:
    def test_verify_correct_secret(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com", "my_secret")
        assert wm.verify_secret("bot1", "my_secret") is True

    def test_verify_wrong_secret(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com", "my_secret")
        assert wm.verify_secret("bot1", "wrong_secret") is False

    def test_verify_no_secret_stored(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com")
        assert wm.verify_secret("bot1", "anything") is True

    def test_verify_nonexistent_bot(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        assert wm.verify_secret("nonexistent", "secret") is True


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com", "secret")
        wm2 = TelegramWebhookManager(str(state_file))
        wh = wm2.get("bot1")
        assert wh is not None
        assert wh["url"] == "https://example.com"

    def test_load_nonexistent(self, tmp_path):
        state_file = tmp_path / "nonexistent.json"
        wm = TelegramWebhookManager(str(state_file))
        assert wm._webhooks == {}


class TestHandlerRegistration:
    def test_register_handler(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        async def handler(update):
            pass
        wm.register_handler("bot1", handler)
        assert wm._handlers["bot1"] is handler

    def test_handle_update_no_handler(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        result = asyncio.run(wm.handle_update("nonexistent", {}))
        assert result is None


class TestListWebhooks:
    def test_list_empty(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        assert wm.list_webhooks() == {}

    def test_list_with_entries(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://a.com")
        wm.register("bot2", "https://b.com")
        webhooks = wm.list_webhooks()
        assert len(webhooks) == 2
        assert "bot1" in webhooks
        assert "bot2" in webhooks


class TestGetWebhookInfo:
    def test_get_info(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        wm.register("bot1", "https://example.com", "secret")
        info = wm.get_webhook_info("bot1")
        assert info["url"] == "https://example.com"
        assert info["has_secret"] is True
        assert info["active"] is True
        assert "message" in info["allowed_updates"]

    def test_get_info_nonexistent(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = TelegramWebhookManager(str(state_file))
        info = wm.get_webhook_info("nonexistent")
        assert info["url"] == ""
        assert info["has_secret"] is False
