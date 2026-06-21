"""
Base plugin interface for Telegram Board System.

All plugins must implement this interface to be loaded by the PluginManager.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PluginInterface(ABC):
    """
    Abstract base class for all plugins.

    Every plugin MUST define:
        - PLUGIN_NAME: str
        - VERSION: str
        - initialize() / shutdown() lifecycle
        - get_stats() for status reporting
    """

    PLUGIN_NAME: str = ""
    VERSION: str = "0.0.0"

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize plugin resources (connections, state)."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Release plugin resources."""
        ...

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics for this plugin."""
        ...

    @property
    def is_initialized(self) -> bool:
        """Whether the plugin has been initialized."""
        return getattr(self, "_initialized", False)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.PLUGIN_NAME!r} v{self.VERSION}>"
