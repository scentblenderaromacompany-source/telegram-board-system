"""
Security manager for API keys, tokens, and access control.
"""
import os
import hashlib
import hmac
import logging
from typing import Dict, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Manages security credentials and access control.
    """
    
    def __init__(self, config_file: str = "config/security.json"):
        self._config_file = Path(config_file)
        self._secrets: Dict[str, str] = {}
        self._api_keys: Dict[str, Dict] = {}
        self._allowed_users: Dict[str, List[int]] = {}
        self._load()
    
    def _load(self):
        if self._config_file.exists():
            data = json.loads(self._config_file.read_text())
            self._api_keys = data.get("api_keys", {})
            self._allowed_users = data.get("allowed_users", {})
    
    def _save(self):
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "api_keys": self._api_keys,
            "allowed_users": self._allowed_users,
        }
        self._config_file.write_text(json.dumps(data, indent=2))
    
    def get_env(self, name: str, default: str = None) -> Optional[str]:
        return os.environ.get(name, default)
    
    def set_secret(self, key: str, value: str):
        self._secrets[key] = value
    
    def get_secret(self, key: str) -> Optional[str]:
        return self._secrets.get(key)
    
    def generate_api_key(self, name: str, scopes: List[str] = None) -> str:
        import secrets
        api_key = secrets.token_urlsafe(32)
        self._api_keys[name] = {
            "key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
            "scopes": scopes or [],
        }
        self._save()
        return api_key
    
    def verify_api_key(self, name: str, api_key: str) -> bool:
        stored = self._api_keys.get(name)
        if not stored:
            return False
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return hmac.compare_digest(stored["key_hash"], key_hash)
    
    def check_access(self, service: str, user_id: int) -> bool:
        allowed = self._allowed_users.get(service, [])
        return not allowed or user_id in allowed
    
    def generate_webhook_secret(self) -> str:
        import secrets
        return secrets.token_hex(32)
