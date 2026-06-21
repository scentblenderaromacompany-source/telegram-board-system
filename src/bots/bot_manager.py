"""
Bot manager for handling multiple Telegram bots.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from .bot_core import TelegramBot, BotConfig

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self._bots: Dict[str, TelegramBot] = {}
        self._running = False
    
    def register(self, bot: TelegramBot):
        """Register a bot with the manager."""
        self._bots[bot.config.bot_id] = bot
        logger.info(f"Registered bot: {bot.config.name} ({bot.config.bot_id})")
    
    def unregister(self, bot_id: str):
        """Unregister a bot."""
        self._bots.pop(bot_id, None)
    
    def get(self, bot_id: str) -> Optional[TelegramBot]:
        """Get a bot by ID."""
        return self._bots.get(bot_id)
    
    def list_bots(self) -> List[str]:
        """List all registered bot IDs."""
        return list(self._bots.keys())
    
    async def start_all(self):
        """Start all registered bots."""
        self._running = True
        for bot_id, bot in self._bots.items():
            try:
                await bot.start()
                logger.info(f"Started bot: {bot_id}")
            except Exception as e:
                logger.error(f"Failed to start bot {bot_id}: {e}")
    
    async def stop_all(self):
        """Stop all running bots."""
        self._running = False
        for bot_id, bot in self._bots.items():
            try:
                await bot.stop()
                logger.info(f"Stopped bot: {bot_id}")
            except Exception as e:
                logger.error(f"Failed to stop bot {bot_id}: {e}")
    
    async def start_bot(self, bot_id: str):
        """Start a specific bot."""
        bot = self._bots.get(bot_id)
        if bot:
            await bot.start()
    
    async def stop_bot(self, bot_id: str):
        """Stop a specific bot."""
        bot = self._bots.get(bot_id)
        if bot:
            await bot.stop()
