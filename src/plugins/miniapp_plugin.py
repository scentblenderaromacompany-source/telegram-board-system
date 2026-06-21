"""
Telegram Mini App plugin for Caspers Heritage.

Provides web-app hosting configuration, user session management,
payment processing hooks, and deep-link handling.
"""
import logging
from typing import Any, Dict, Optional

from .base import PluginInterface

logger = logging.getLogger(__name__)


class MiniAppPlugin(PluginInterface):
    """
    Plugin for Telegram Mini App integration.

    Features:
        - Web-app hosting configuration
        - User session lifecycle management
        - Payment processing hooks
        - Deep-link handling
    """

    PLUGIN_NAME = "miniapp"
    VERSION = "1.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._initialized = False
        self._app_url: str = self.config.get("app_url", "")
        self._payment_provider_token: str = self.config.get("payment_provider_token", "")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Initialize the plugin."""
        self._initialized = True
        logger.info("MiniApp plugin initialized (v%s)", self.VERSION)

    async def shutdown(self) -> None:
        """Release resources and clear sessions."""
        self._initialized = False
        self._sessions.clear()
        logger.info("MiniApp plugin shut down")

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def create_session(self, user_id: int, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a user session for the mini app."""
        session: Dict[str, Any] = {
            "user_id": user_id,
            "data": data or {},
            "active": True,
        }
        self._sessions[user_id] = session
        logger.info("Created mini app session for user %d", user_id)
        return session

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a user session by user_id."""
        return self._sessions.get(user_id)

    def close_session(self, user_id: int) -> bool:
        """Close and remove a user session."""
        if user_id in self._sessions:
            self._sessions[user_id]["active"] = False
            del self._sessions[user_id]
            return True
        return False

    # ------------------------------------------------------------------
    # App data
    # ------------------------------------------------------------------

    def get_app_url(self) -> str:
        """Return the mini-app URL."""
        return self._app_url

    def get_web_app_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return web-app data for *user_id*, or ``None``."""
        session = self.get_session(user_id)
        if session:
            return session.get("data")
        return None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return plugin runtime statistics."""
        return {
            "name": self.PLUGIN_NAME,
            "version": self.VERSION,
            "initialized": self._initialized,
            "active_sessions": len(self._sessions),
            "app_url": self._app_url,
            "payment_configured": bool(self._payment_provider_token),
        }
