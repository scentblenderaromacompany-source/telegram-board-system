"""
Telegram platform adapter, networking, and bot management.

Provides production-ready Telegram integration with DNS-over-HTTPS fallback,
managed bot onboarding, message formatting, media handling, and webhooks.
"""
from .adapter import TelegramPlatformAdapter
from .commands import TelegramCommandRegistry
from .forum import TelegramForumManager
from .managed_bot import TelegramManagedBot, TelegramPairing
from .media_handler import TelegramMediaHandler
from .message_formatter import TelegramMessageFormatter
from .network import TelegramFallbackTransport, discover_fallback_ips
from .webhook import TelegramWebhookManager

__all__ = [
    "TelegramPlatformAdapter",
    "TelegramFallbackTransport",
    "discover_fallback_ips",
    "TelegramManagedBot",
    "TelegramPairing",
    "TelegramMessageFormatter",
    "TelegramMediaHandler",
    "TelegramWebhookManager",
    "TelegramForumManager",
    "TelegramCommandRegistry",
]
