"""
Webhook manager for Telegram and other channel integrations.
"""
import hashlib
import hmac
import logging
from typing import Dict, Optional, Callable, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class WebhookManager:
    """
    Manages webhooks for Telegram Bot API and other integrations.
    """
    
    def __init__(self, state_file: str = "config/webhooks.json"):
        self._webhooks: Dict[str, Dict] = {}
        self._handlers: Dict[str, Callable] = {}
        self._state_file = Path(state_file)
        self._load()
    
    def _load(self):
        if self._state_file.exists():
            self._webhooks = json.loads(self._state_file.read_text())
    
    def _save(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps(self._webhooks, indent=2))
    
    def register_webhook(self, bot_id: str, url: str, secret: Optional[str] = None, allowed_updates: list = None):
        """Register a webhook URL for a bot."""
        self._webhooks[bot_id] = {
            "url": url,
            "secret": secret,
            "allowed_updates": allowed_updates or ["message", "callback_query", "inline_query"],
            "active": True,
        }
        self._save()
        logger.info(f"Registered webhook for {bot_id}: {url}")
    
    def remove_webhook(self, bot_id: str):
        """Remove a webhook."""
        self._webhooks.pop(bot_id, None)
        self._save()
    
    def get_webhook(self, bot_id: str) -> Optional[Dict]:
        """Get webhook config for a bot."""
        return self._webhooks.get(bot_id)
    
    def verify_secret(self, bot_id: str, secret: str) -> bool:
        """Verify webhook secret."""
        wh = self._webhooks.get(bot_id)
        if not wh or not wh.get("secret"):
            return True
        return hmac.compare_digest(wh["secret"], secret)
    
    def register_handler(self, bot_id: str, handler: Callable):
        """Register update handler for a bot."""
        self._handlers[bot_id] = handler
    
    async def handle_update(self, bot_id: str, update: Dict) -> Any:
        """Process an incoming update."""
        handler = self._handlers.get(bot_id)
        if handler:
            return await handler(update)
        logger.warning(f"No handler for bot {bot_id}")
    
    def list_webhooks(self) -> Dict:
        """List all webhooks."""
        return dict(self._webhooks)
