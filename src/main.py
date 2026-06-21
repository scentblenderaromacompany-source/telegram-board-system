"""
Main entry point for Telegram Board System v2.
Integrates agents, channels, masks, plugins, and memory.
Runs an HTTP health server for UptimeRobot / Render keep-alive.
"""
import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import Dict, Optional

from aiohttp import web
from aiohttp.web_app import AppKey

from .bots import TelegramBot, BotConfig, BotManager
from .channels import ChannelRegistry, ChannelManager, MessageRouter
from .channels.webhook_manager import WebhookManager
from .channels.channel_adapters import TelegramAdapter, SlackAdapter, WebAdapter
from .masks import MaskRegistry, MaskManager
from .agents.agent_core import Agent, AgentConfig, AgentRole
from .agents.agent_manager import AgentManager
from .agents.memory import MemoryStore
from .plugins.plugin_loader import PluginManager
from .plugins.jewelry_plugin import JewelryPlugin
from .plugins.content_plugin import ContentPlugin
from .plugins.miniapp_plugin import MiniAppPlugin

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# App key for type-safe access
SYSTEM_KEY: AppKey["TelegramBoardSystem"] = AppKey("system", "TelegramBoardSystem")


# ------------------------------------------------------------------
# Health HTTP server (for UptimeRobot / Render keep-alive)
# ------------------------------------------------------------------

async def handle_health(request: web.Request) -> web.Response:
    """GET / — returns 200 OK to keep the service alive."""
    system: TelegramBoardSystem = request.app[SYSTEM_KEY]
    return web.json_response({
        "status": "ok",
        "version": "2.0.0",
        "agents": len(system.agent_manager.list_agents()),
        "plugins": len(system.plugin_manager.list_plugins()),
    })


async def handle_metrics(request: web.Request) -> web.Response:
    """GET /metrics — basic system metrics."""
    system: TelegramBoardSystem = request.app[SYSTEM_KEY]
    return web.json_response(system.get_metrics())


async def start_health_server(system: "TelegramBoardSystem", port: int = 8080) -> web.AppRunner:
    """Start a lightweight HTTP server for health checks."""
    app = web.Application()
    app[SYSTEM_KEY] = system
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/metrics", handle_metrics)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health server listening on :%d", port)
    return runner


# ------------------------------------------------------------------
# Main system
# ------------------------------------------------------------------

class TelegramBoardSystem:
    """
    Production-grade Telegram Board System.

    Integrates:
    - Multi-bot management with masks
    - Channel routing and webhooks
    - Agent framework with tools/skills
    - Plugin system for extensibility
    - Long-term memory store
    - Multi-platform adapters (Telegram, Slack, Web)
    - HTTP health server for UptimeRobot / Render keep-alive
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)

        self.channel_registry = ChannelRegistry(str(self.config_dir / "channels.json"))
        self.mask_registry = MaskRegistry(str(self.config_dir / "masks.json"))

        self.bot_manager = BotManager()
        self.channel_manager = ChannelManager(self.channel_registry)
        self.mask_manager = MaskManager(self.mask_registry)
        self.message_router = MessageRouter(self.channel_registry)

        self.webhook_manager = WebhookManager(str(self.config_dir / "webhooks.json"))
        self.agent_manager = AgentManager()
        self.memory = MemoryStore(str(self.config_dir / "memory.json"))
        self.plugin_manager = PluginManager()

        self._adapters: Dict[str, any] = {}
        self._health_runner: Optional[web.AppRunner] = None

    async def start(self):
        """Start the complete system."""
        logger.info("Starting Telegram Board System v2...")

        self.plugin_manager.load_plugin(Path("plugins/supabase-jewelry")) if Path("plugins/supabase-jewelry").exists() else None
        self.plugin_manager.load_plugin(Path("plugins/content-engine")) if Path("plugins/content-engine").exists() else None
        self.plugin_manager.load_plugin(Path("plugins/caspers-telegram-miniapp")) if Path("plugins/caspers-telegram-miniapp").exists() else None

        await self.agent_manager.start_all()
        await self.bot_manager.start_all()

        # Start health server for UptimeRobot / Render keep-alive
        health_port = int(os.getenv("PORT", "8080"))
        self._health_runner = await start_health_server(self, port=health_port)

        logger.info("System started successfully")
        logger.info("  Agents: %d", len(self.agent_manager.list_agents()))
        logger.info("  Plugins: %d", len(self.plugin_manager.list_plugins()))
        logger.info("  Memory: %d entries", self.memory.get_stats()["total_entries"])

    async def stop(self):
        """Gracefully stop the system."""
        logger.info("Stopping Telegram Board System...")
        if self._health_runner:
            await self._health_runner.cleanup()
        await self.bot_manager.stop_all()
        await self.agent_manager.stop_all()
        for adapter in self._adapters.values():
            await adapter.disconnect()
        logger.info("System stopped")

    def create_agent(self, agent_id: str, name: str, role: AgentRole, business_id: str, **kwargs) -> Agent:
        """Create and register a new agent."""
        config = AgentConfig(
            agent_id=agent_id,
            name=name,
            role=role,
            business_id=business_id,
            **kwargs,
        )
        agent = Agent(config)
        self.agent_manager.register(agent)
        return agent

    def create_bot(self, bot_id: str, token: str, name: str, business_id: str, **kwargs) -> TelegramBot:
        """Create and register a new bot."""
        config = BotConfig(
            token=token,
            bot_id=bot_id,
            name=name,
            business_id=business_id,
            **kwargs,
        )
        bot = TelegramBot(config)
        self.bot_manager.register(bot)
        return bot

    def register_adapter(self, channel_id: str, adapter):
        """Register a channel adapter."""
        self._adapters[channel_id] = adapter

    def get_metrics(self) -> Dict:
        """Get system-wide metrics."""
        return {
            "agents": self.agent_manager.get_status(),
            "memory": self.memory.get_stats(),
            "plugins": self.plugin_manager.list_plugins(),
            "adapters": {k: v.is_connected for k, v in self._adapters.items()},
        }


async def main():
    system = TelegramBoardSystem()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(system.stop()))

    try:
        await system.start()
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
