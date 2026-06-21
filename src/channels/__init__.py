"""
Channel management, routing, and platform adapters.

Provides a registry of messaging channels with adapters for Telegram,
Slack, and Web, plus message routing and webhook management.
"""
from .channel_adapters import SlackAdapter, TelegramAdapter, WebAdapter
from .channel_manager import ChannelManager
from .channel_registry import Channel, ChannelStatus, ChannelType, ChannelRegistry
from .message_router import MessageRouter
from .webhook_manager import WebhookManager

__all__ = [
    "ChannelRegistry",
    "Channel",
    "ChannelType",
    "ChannelStatus",
    "ChannelManager",
    "MessageRouter",
    "WebhookManager",
    "TelegramAdapter",
    "SlackAdapter",
    "WebAdapter",
]
