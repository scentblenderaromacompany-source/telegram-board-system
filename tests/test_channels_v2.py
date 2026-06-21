"""
Comprehensive isolated tests for src/channels/ module.
"""
import asyncio
import json

import pytest

from src.channels.channel_registry import ChannelRegistry, Channel, ChannelType, ChannelStatus
from src.channels.channel_manager import ChannelManager
from src.channels.message_router import MessageRouter
from src.channels.webhook_manager import WebhookManager
from src.channels.channel_adapters import (
    BaseChannelAdapter,
    TelegramAdapter,
    SlackAdapter,
    WebAdapter,
)


class TestChannelType:
    def test_values(self):
        assert ChannelType.BROADCAST.value == "broadcast"
        assert ChannelType.SUPPORT.value == "support"
        assert ChannelType.INTERNAL.value == "internal"
        assert ChannelType.MONITORING.value == "monitoring"


class TestChannelStatus:
    def test_values(self):
        assert ChannelStatus.ACTIVE.value == "active"
        assert ChannelStatus.INACTIVE.value == "inactive"
        assert ChannelStatus.ARCHIVED.value == "archived"


class TestChannel:
    def test_creation(self):
        ch = Channel(
            channel_id="ch1",
            name="Support",
            business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        assert ch.channel_id == "ch1"
        assert ch.status == ChannelStatus.ACTIVE
        assert ch.description == ""
        assert ch.bot_id is None
        assert ch.rate_limit == 30


class TestChannelRegistry:
    def test_empty(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        assert len(reg._channels) == 0

    def test_register(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        ch = Channel(
            channel_id="ch1", name="Support", business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        reg.register(ch)
        assert reg.get("ch1") is ch

    def test_register_persists(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg1 = ChannelRegistry(str(state_file))
        ch = Channel(
            channel_id="ch1", name="Support", business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        reg1.register(ch)
        reg2 = ChannelRegistry(str(state_file))
        assert reg2.get("ch1") is not None

    def test_list_by_business(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz1",
            channel_type=ChannelType.SUPPORT,
        ))
        reg.register(Channel(
            channel_id="ch2", name="B", business_id="biz2",
            channel_type=ChannelType.SUPPORT,
        ))
        assert len(reg.list_by_business("biz1")) == 1

    def test_list_by_type(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz",
            channel_type=ChannelType.SUPPORT,
        ))
        reg.register(Channel(
            channel_id="ch2", name="B", business_id="biz",
            channel_type=ChannelType.BROADCAST,
        ))
        assert len(reg.list_by_type(ChannelType.SUPPORT)) == 1
        assert len(reg.list_by_type(ChannelType.BROADCAST)) == 1

    def test_update(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz",
            channel_type=ChannelType.SUPPORT,
        ))
        updated = reg.update("ch1", name="B")
        assert updated.name == "B"

    def test_update_nonexistent(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        assert reg.update("nonexistent", name="B") is None

    def test_delete(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz",
            channel_type=ChannelType.SUPPORT,
        ))
        assert reg.delete("ch1") is True
        assert reg.get("ch1") is None

    def test_delete_nonexistent(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        assert reg.delete("nonexistent") is False


class TestChannelManager:
    def test_create_channel(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        ch = mgr.create_channel(
            channel_id="ch1",
            name="Support",
            business_id="biz",
            channel_type=ChannelType.SUPPORT,
        )
        assert ch.channel_id == "ch1"
        assert reg.get("ch1") is ch

    def test_get_channel(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        mgr.create_channel("ch1", "A", "biz", ChannelType.SUPPORT)
        assert mgr.get_channel("ch1") is not None

    def test_list_channels(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        mgr.create_channel("ch1", "A", "biz1", ChannelType.SUPPORT)
        mgr.create_channel("ch2", "B", "biz2", ChannelType.SUPPORT)
        assert len(mgr.list_channels()) == 2
        assert len(mgr.list_channels("biz1")) == 1

    def test_update_channel(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        mgr.create_channel("ch1", "A", "biz", ChannelType.SUPPORT)
        updated = mgr.update_channel("ch1", name="B")
        assert updated.name == "B"

    def test_delete_channel(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        mgr.create_channel("ch1", "A", "biz", ChannelType.SUPPORT)
        assert mgr.delete_channel("ch1") is True
        assert mgr.get_channel("ch1") is None

    def test_activate_deactivate(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        mgr = ChannelManager(reg)
        mgr.create_channel("ch1", "A", "biz", ChannelType.SUPPORT)
        mgr.deactivate_channel("ch1")
        ch = mgr.get_channel("ch1")
        assert ch.status == ChannelStatus.INACTIVE
        mgr.activate_channel("ch1")
        ch = mgr.get_channel("ch1")
        assert ch.status == ChannelStatus.ACTIVE


class TestMessageRouter:
    def test_empty(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        router = MessageRouter(reg)
        assert router.get_routes() == {}

    def test_set_route(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        router = MessageRouter(reg)
        router.set_route("biz1", "ch1")
        assert router.get_routes()["biz1"] == "ch1"

    def test_resolve_channel_explicit_route(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        router = MessageRouter(reg)
        router.set_route("biz1", "ch1")
        assert router.resolve_channel("biz1") == "ch1"

    def test_resolve_channel_fallback(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz1",
            channel_type=ChannelType.SUPPORT,
        ))
        router = MessageRouter(reg)
        assert router.resolve_channel("biz1") == "ch1"

    def test_resolve_channel_with_type(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz1",
            channel_type=ChannelType.SUPPORT,
        ))
        reg.register(Channel(
            channel_id="ch2", name="B", business_id="biz1",
            channel_type=ChannelType.BROADCAST,
        ))
        router = MessageRouter(reg)
        assert router.resolve_channel("biz1", ChannelType.BROADCAST) == "ch2"

    def test_resolve_channel_not_found(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        router = MessageRouter(reg)
        assert router.resolve_channel("nonexistent") is None

    def test_route_message(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz1",
            channel_type=ChannelType.SUPPORT,
        ))
        router = MessageRouter(reg)
        received = []

        async def handler(channel_id, chat_id, text, **kwargs):
            received.append((channel_id, chat_id, text))

        router.register_handler("ch1", handler)
        result = asyncio.run(
            router.route_message("biz1", "user1", "hello")
        )
        assert result is True
        assert len(received) == 1

    def test_route_message_no_channel(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        router = MessageRouter(reg)
        result = asyncio.run(
            router.route_message("nonexistent", "user1", "hello")
        )
        assert result is False

    def test_route_message_no_handler(self, tmp_path):
        state_file = tmp_path / "channels.json"
        reg = ChannelRegistry(str(state_file))
        reg.register(Channel(
            channel_id="ch1", name="A", business_id="biz1",
            channel_type=ChannelType.SUPPORT,
        ))
        router = MessageRouter(reg)
        result = asyncio.run(
            router.route_message("biz1", "user1", "hello")
        )
        assert result is False


class TestWebhookManager:
    def test_register(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = WebhookManager(str(state_file))
        wm.register_webhook("bot1", "https://example.com", "secret")
        wh = wm.get_webhook("bot1")
        assert wh is not None
        assert wh["url"] == "https://example.com"

    def test_remove(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = WebhookManager(str(state_file))
        wm.register_webhook("bot1", "https://example.com")
        wm.remove_webhook("bot1")
        assert wm.get_webhook("bot1") is None

    def test_verify_secret(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = WebhookManager(str(state_file))
        wm.register_webhook("bot1", "https://example.com", "secret")
        assert wm.verify_secret("bot1", "secret") is True
        assert wm.verify_secret("bot1", "wrong") is False

    def test_verify_no_secret(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = WebhookManager(str(state_file))
        wm.register_webhook("bot1", "https://example.com")
        assert wm.verify_secret("bot1", "anything") is True

    def test_list_webhooks(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm = WebhookManager(str(state_file))
        wm.register_webhook("bot1", "https://a.com")
        wm.register_webhook("bot2", "https://b.com")
        webhooks = wm.list_webhooks()
        assert len(webhooks) == 2

    def test_persistence(self, tmp_path):
        state_file = tmp_path / "webhooks.json"
        wm1 = WebhookManager(str(state_file))
        wm1.register_webhook("bot1", "https://example.com")
        wm2 = WebhookManager(str(state_file))
        assert wm2.get_webhook("bot1") is not None


class TestChannelAdapters:
    def test_slack_adapter(self):
        adapter = SlackAdapter("slack1", {"token": "x"})
        asyncio.run(adapter.connect())
        assert adapter.is_connected is True
        asyncio.run(adapter.disconnect())
        assert adapter.is_connected is False

    def test_web_adapter(self):
        adapter = WebAdapter("web1", {})
        asyncio.run(adapter.connect())
        assert adapter.is_connected is True
        result = asyncio.run(
            adapter.send_message("user1", "hello")
        )
        assert result["text"] == "hello"
        asyncio.run(adapter.disconnect())
        assert adapter.is_connected is False

    def test_web_adapter_delete(self):
        adapter = WebAdapter("web1", {})
        asyncio.run(adapter.connect())
        result = asyncio.run(
            adapter.delete_message("user1", 123)
        )
        assert result is True
