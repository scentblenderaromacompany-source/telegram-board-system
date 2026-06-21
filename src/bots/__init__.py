"""
Telegram bot framework with middleware, handlers, and metrics.

Provides a production-ready bot core with decorator-based routing,
middleware pipelines, and conversation management.
"""
from .bot_core import BotConfig, TelegramBot
from .bot_manager import BotManager

__all__ = [
    "TelegramBot",
    "BotConfig",
    "BotManager",
]
