"""
Telegram Integration Layer.
Connects all modules: Telegram adapter, agents, masks, channels, memory, plugins.
This is the main orchestration layer for Telegram operations.
"""
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .telegram.adapter import TelegramPlatformAdapter, TelegramConfig, TelegramMessage
from .telegram.commands import TelegramCommandRegistry, TelegramCommand
from .telegram.forum import TelegramForumManager
from .telegram.webhook import TelegramWebhookManager
from .telegram.media_handler import TelegramMediaHandler
from .telegram.message_formatter import TelegramMessageFormatter

from .agents.agent_core import Agent, AgentConfig, AgentRole
from .agents.agent_manager import AgentManager
from .agents.memory import MemoryStore, MemoryEntry, MemoryCategory

from .masks.mask_registry import MaskRegistry, Mask, MaskType
from .masks.mask_manager import MaskManager
from .masks.persona_engine import PersonaEngine
from .masks.mask_templates import MaskTemplateLibrary

from .channels.channel_registry import ChannelRegistry, Channel, ChannelType
from .channels.channel_manager import ChannelManager
from .channels.message_router import MessageRouter

logger = logging.getLogger(__name__)


class TelegramIntegration:
    """
    Central integration layer for Telegram operations.
    
    Connects:
    - TelegramPlatformAdapter (polling/webhooks)
    - AgentManager (multi-agent orchestration)
    - MaskManager (bot identities)
    - ChannelManager (channel routing)
    - MemoryStore (long-term memory)
    - TelegramCommandRegistry (command dispatch)
    - TelegramForumManager (forum topics)
    - PersonaEngine (response formatting)
    
    Usage:
        integration = TelegramIntegration.from_config("config/")
        await integration.start()
        # System is now running with all bots, agents, and handlers active
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        
        self.mask_registry = MaskRegistry(str(self.config_dir / "masks.json"))
        self.channel_registry = ChannelRegistry(str(self.config_dir / "channels.json"))
        self.memory = MemoryStore(str(self.config_dir / "memory.json"))
        
        self.agent_manager = AgentManager()
        self.mask_manager = MaskManager(self.mask_registry)
        self.channel_manager = ChannelManager(self.channel_registry)
        self.message_router = MessageRouter(self.channel_registry)
        
        self.command_registry = TelegramCommandRegistry()
        self.command_registry.register_default_commands()
        
        self.formatter = TelegramMessageFormatter()
        self.media_handler = TelegramMediaHandler()
        
        self._adapters: Dict[str, TelegramPlatformAdapter] = {}
        self._forum_managers: Dict[str, TelegramForumManager] = {}
        self._webhook_manager = TelegramWebhookManager(str(self.config_dir / "webhooks.json"))
        
        self._running = False
        self._start_time = 0.0
    
    @classmethod
    def from_config(cls, config_dir: str = "config") -> "TelegramIntegration":
        """Create integration from config directory."""
        return cls(config_dir)
    
    async def start(self):
        """Start the complete Telegram integration."""
        logger.info("Starting Telegram Integration...")
        self._running = True
        self._start_time = time.time()
        
        await self.agent_manager.start_all()
        
        for bot_id, adapter in self._adapters.items():
            try:
                await adapter.connect()
                logger.info(f"Connected bot: {bot_id}")
            except Exception as e:
                logger.error(f"Failed to connect bot {bot_id}: {e}")
        
        logger.info(f"Telegram Integration started: {len(self._adapters)} bots, {len(self.agent_manager.list_agents())} agents")
    
    async def stop(self):
        """Stop the Telegram integration."""
        logger.info("Stopping Telegram Integration...")
        self._running = False
        
        for bot_id, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {bot_id}: {e}")
        
        await self.agent_manager.stop_all()
        logger.info("Telegram Integration stopped")
    
    def create_bot(self, bot_id: str, token: str, business_id: str, mask_id: str = None, **kwargs) -> TelegramPlatformAdapter:
        """Create and register a Telegram bot."""
        config = TelegramConfig(
            token=token,
            bot_id=bot_id,
            business_id=business_id,
            **kwargs,
        )
        adapter = TelegramPlatformAdapter(config)
        self._adapters[bot_id] = adapter
        
        if mask_id:
            self.mask_manager.assign_mask(bot_id, mask_id)
        
        self._register_bot_handlers(bot_id, adapter)
        
        logger.info(f"Created bot: {bot_id} (business: {business_id})")
        return adapter
    
    def _register_bot_handlers(self, bot_id: str, adapter: TelegramPlatformAdapter):
        """Register default handlers for a bot."""
        
        @adapter.on_command("start")
        async def handle_start(msg: TelegramMessage, context):
            mask = self.mask_manager.get_mask_for_bot(bot_id)
            greeting = "Hello! I'm ready to help." if not mask else self.mask_manager.persona_engine.get_greeting(mask)
            await adapter.send_message(msg.chat_id, greeting)
        
        @adapter.on_command("help")
        async def handle_help(msg: TelegramMessage, context):
            help_text = self.command_registry.get_help_text()
            await adapter.send_message(msg.chat_id, help_text)
        
        @adapter.on_command("status")
        async def handle_status(msg: TelegramMessage, context):
            metrics = adapter.get_metrics()
            status_text = self.formatter.table(
                ["Metric", "Value"],
                [
                    ["Messages Received", str(metrics["messages_received"])],
                    ["Messages Sent", str(metrics["messages_sent"])],
                    ["Errors", str(metrics["errors"])],
                    ["Callbacks", str(metrics["callbacks_received"])],
                    ["Media Sent", str(metrics["media_sent"])],
                ]
            )
            await adapter.send_message(msg.chat_id, status_text)
        
        @adapter.on_command("ping")
        async def handle_ping(msg: TelegramMessage, context):
            await adapter.send_message(msg.chat_id, "pong")
        
        @adapter.on_message
        async def handle_message(msg: TelegramMessage, context):
            if msg.is_bot_mentioned or msg.chat_type.value == "private":
                agent = self.agent_manager.resolve_agent(
                    self._get_business_for_bot(bot_id)
                )
                if agent:
                    response = await agent.process_message(
                        str(msg.chat_id), str(msg.user_id), msg.text or ""
                    )
                    if response:
                        mask = self.mask_manager.get_mask_for_bot(bot_id)
                        if mask:
                            response = self.mask_manager.apply_persona(bot_id, response)
                        await adapter.send_message(msg.chat_id, response)
    
    def _get_business_for_bot(self, bot_id: str) -> str:
        adapter = self._adapters.get(bot_id)
        return adapter.config.business_id if adapter else ""
    
    def create_agent(self, agent_id: str, name: str, role: AgentRole, business_id: str, **kwargs) -> Agent:
        """Create and register an agent."""
        config = AgentConfig(agent_id=agent_id, name=name, role=role, business_id=business_id, **kwargs)
        agent = Agent(config)
        self.agent_manager.register(agent)
        return agent
    
    def get_adapter(self, bot_id: str) -> Optional[TelegramPlatformAdapter]:
        return self._adapters.get(bot_id)
    
    def get_forum_manager(self, bot_id: str) -> Optional[TelegramForumManager]:
        return self._forum_managers.get(bot_id)
    
    def get_metrics(self) -> Dict:
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "running": self._running,
            "uptime_seconds": uptime,
            "bots": {bid: a.get_metrics() for bid, a in self._adapters.items()},
            "agents": self.agent_manager.get_status(),
            "memory": self.memory.get_stats(),
            "masks": len(self.mask_registry._masks),
            "channels": len(self.channel_registry._channels),
        }
    
    async def send_to_all(self, text: str, business_id: str = None):
        """Send a message to all bots for a business."""
        for bot_id, adapter in self._adapters.items():
            if business_id and adapter.config.business_id != business_id:
                continue
            if adapter.is_connected:
                try:
                    for chat_id in adapter.config.allowed_chat_ids:
                        await adapter.send_message(chat_id, text)
                except Exception as e:
                    logger.error(f"Failed to send via {bot_id}: {e}")
