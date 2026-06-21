"""
Plugins package for Telegram Board System.

Exports the base interface, loader, and built-in plugins.
"""
from .base import PluginInterface
from .content_plugin import ContentPlugin
from .jewelry_plugin import JewelryPlugin
from .miniapp_plugin import MiniAppPlugin
from .plugin_loader import Plugin, PluginManager

__all__ = [
    "PluginInterface",
    "Plugin",
    "PluginManager",
    "JewelryPlugin",
    "ContentPlugin",
    "MiniAppPlugin",
]
