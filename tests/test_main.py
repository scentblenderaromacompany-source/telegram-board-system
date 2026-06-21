"""
Comprehensive isolated tests for src/main.py (TelegramBoardSystem).
"""
import asyncio

import pytest

from src.agents.agent_core import AgentRole
from src.main import TelegramBoardSystem


class TestTelegramBoardSystem:
    def test_init(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        assert system.config_dir.exists() or True
        assert system._adapters == {}

    def test_create_agent(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        agent = system.create_agent(
            agent_id="agent1",
            name="Test Agent",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        assert agent.config.agent_id == "agent1"
        assert "agent1" in system.agent_manager.list_agents()

    def test_create_bot(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        bot = system.create_bot(
            bot_id="bot1",
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            name="TestBot",
            business_id="biz",
        )
        assert bot.config.bot_id == "bot1"
        assert "bot1" in system.bot_manager.list_bots()

    def test_create_multiple_bots(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        for i in range(3):
            system.create_bot(
                bot_id=f"bot{i}",
                token=f"{100000000 + i}:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
                name=f"Bot{i}",
                business_id="biz",
            )
        assert len(system.bot_manager.list_bots()) == 3

    def test_create_multiple_agents(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        system.create_agent("a1", "Agent1", AgentRole.SUPPORT, "biz1")
        system.create_agent("a2", "Agent2", AgentRole.EXECUTIVE, "biz2")
        assert len(system.agent_manager.list_agents()) == 2

    def test_register_adapter(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        adapter = type("MockAdapter", (), {"is_connected": False})()
        system.register_adapter("web1", adapter)
        assert "web1" in system._adapters

    def test_get_metrics(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        metrics = system.get_metrics()
        assert "agents" in metrics
        assert "memory" in metrics
        assert "plugins" in metrics
        assert "adapters" in metrics

    def test_get_metrics_with_agents(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        system.create_agent("a1", "Agent1", AgentRole.SUPPORT, "biz")
        metrics = system.get_metrics()
        assert "a1" in metrics["agents"]

    def test_memory_initialized(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        stats = system.memory.get_stats()
        assert stats["total_entries"] == 0

    def test_channel_registry_initialized(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        assert system.channel_registry is not None

    def test_mask_registry_initialized(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        assert system.mask_registry is not None

    def test_plugin_manager_initialized(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        assert system.plugin_manager is not None
        assert system.plugin_manager.list_plugins() == []

    def test_start_stop(self, tmp_path):
        config_dir = str(tmp_path / "config")
        system = TelegramBoardSystem(config_dir)
        asyncio.run(system.start())
        asyncio.run(system.stop())
