"""
Telegram webhook manager with secret verification.
"""
import hashlib
import hmac
import logging
from typing import Dict, Optional, Callable, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class TelegramWebhookManager:
    """
    Manages Telegram webhook configuration and verification.
    """
    
    def __init__(self, state_file: str = "config/telegram_webhooks.json"):
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
    
    def register(self, bot_id: str, url: str, secret_token: str = None, allowed_updates: list = None):
        self._webhooks[bot_id] = {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": allowed_updates or ["message", "callback_query", "inline_query", "my_chat_member"],
            "active": True,
            "created_at": __import__("time").time(),
        }
        self._save()
        logger.info(f"Registered webhook for {bot_id}: {url}")
    
    def remove(self, bot_id: str):
        self._webhooks.pop(bot_id, None)
        self._save()
    
    def get(self, bot_id: str) -> Optional[Dict]:
        return self._webhooks.get(bot_id)
    
    def verify_secret(self, bot_id: str, secret: str) -> bool:
        wh = self._webhooks.get(bot_id)
        if not wh or not wh.get("secret_token"):
            return True
        return hmac.compare_digest(wh["secret_token"], secret)
    
    def register_handler(self, bot_id: str, handler: Callable):
        self._handlers[bot_id] = handler
    
    async def handle_update(self, bot_id: str, update: Dict) -> Any:
        handler = self._handlers.get(bot_id)
        if handler:
            return await handler(update)
        logger.warning(f"No handler for bot {bot_id}")
    
    def list_webhooks(self) -> Dict:
        return dict(self._webhooks)
    
    def get_webhook_info(self, bot_id: str) -> Dict:
        wh = self._webhooks.get(bot_id, {})
        return {
            "url": wh.get("url", ""),
            "has_secret": bool(wh.get("secret_token")),
            "allowed_updates": wh.get("allowed_updates", []),
            "active": wh.get("active", False),
        }
