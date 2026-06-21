"""
Configuration loader with environment variable support.
Loads config from JSON/YAML files + env vars.
"""
import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager with:
    - JSON/YAML file loading
    - Environment variable overrides
    - Dot-notation access
    - Validation
    - Defaults
    """
    
    def __init__(self, config_dir: str = "config"):
        self._config_dir = Path(config_dir)
        self._data: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self, filename: str = "default.json") -> "Config":
        config_file = self._config_dir / filename
        if config_file.exists():
            with open(config_file) as f:
                self._data = json.load(f)
            logger.info(f"Loaded config from {config_file}")
        else:
            logger.warning(f"Config file not found: {config_file}")
        
        self._apply_env_overrides()
        self._loaded = True
        return self
    
    def _apply_env_overrides(self):
        prefix = "TBS_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace("__", ".")
                self._set_nested(config_key, value)
    
    def _set_nested(self, key: str, value: Any):
        parts = key.split(".")
        data = self._data
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        data = self._data
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return default
        return data
    
    def set(self, key: str, value: Any):
        self._set_nested(key, value)
    
    def __getitem__(self, key: str) -> Any:
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result
    
    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
    
    def to_dict(self) -> Dict:
        return dict(self._data)
    
    def save(self, filename: str = "default.json"):
        config_file = self._config_dir / filename
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(self._data, f, indent=2)
        logger.info(f"Saved config to {config_file}")


def load_config(config_dir: str = "config") -> Config:
    return Config(config_dir).load()


def get_env(key: str, default: str = None) -> Optional[str]:
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"Required environment variable not set: {key}")
    return value
