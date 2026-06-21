"""
Comprehensive isolated tests for src/integration.py.
"""
import asyncio
import json

import pytest

from src.integration import TelegramIntegration


class TestTelegramIntegration:
    def test_init(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        assert integration._running is False
        assert integration._start_time == 0.0

    def test_from_config(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration.from_config(config_dir)
        assert integration is not None

    def test_create_agent(self, tmp_path):
        from src.agents.agent_core import AgentRole
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        agent = integration.create_agent(
            agent_id="agent1",
            name="Test Agent",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        assert agent.config.agent_id == "agent1"
        assert "agent1" in integration.agent_manager.list_agents()

    def test_create_bot(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        adapter = integration.create_bot(
            bot_id="bot1",
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            business_id="biz",
        )
        assert adapter is not None
        assert "bot1" in integration._adapters

    def test_create_bot_with_mask(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        from src.masks.mask_registry import Mask, MaskType
        mask = Mask(
            mask_id="m1", name="Test", mask_type=MaskType.SUPPORT,
            business_id="biz", display_name="TestBot",
        )
        integration.mask_registry.register(mask)
        adapter = integration.create_bot(
            bot_id="bot1",
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            business_id="biz",
            mask_id="m1",
        )
        assert adapter is not None
        assert integration.mask_manager.get_mask_for_bot("bot1") is not None

    def test_get_adapter(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        integration.create_bot(
            bot_id="bot1",
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            business_id="biz",
        )
        assert integration.get_adapter("bot1") is not None
        assert integration.get_adapter("nonexistent") is None

    def test_get_metrics(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        metrics = integration.get_metrics()
        assert metrics["running"] is False
        assert metrics["uptime_seconds"] == 0
        assert "bots" in metrics
        assert "agents" in metrics
        assert "memory" in metrics
        assert "masks" in metrics
        assert "channels" in metrics

    def test_start_stop(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        asyncio.run(integration.start())
        assert integration._running is True
        asyncio.run(integration.stop())
        assert integration._running is False

    def test_command_registry(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        cmds = integration.command_registry.list_commands()
        assert len(cmds) >= 5

    def test_formatter(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        result = integration.formatter.bold("test")
        assert result == "<b>test</b>"

    def test_media_handler(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        assert integration.media_handler.detect_type("photo.jpg") == "photo"

    def test_mask_registry_empty(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        assert len(integration.mask_registry._masks) == 0

    def test_channel_registry_empty(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        assert len(integration.channel_registry._channels) == 0

    def test_memory_store_empty(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        stats = integration.memory.get_stats()
        assert stats["total_entries"] == 0

    def test_get_business_for_bot(self, tmp_path):
        config_dir = str(tmp_path / "config")
        integration = TelegramIntegration(config_dir)
        integration.create_bot(
            bot_id="bot1",
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            business_id="test_biz",
        )
        assert integration._get_business_for_bot("bot1") == "test_biz"
        assert integration._get_business_for_bot("nonexistent") == ""
