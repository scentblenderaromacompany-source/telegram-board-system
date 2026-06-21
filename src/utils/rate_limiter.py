"""
Rate limiter for Telegram API compliance.
"""
import time
import asyncio
from collections import defaultdict
from typing import Dict

class RateLimiter:
    def __init__(self, default_limit: int = 30, window_seconds: int = 1):
        self._limits: Dict[str, int] = {}
        self._windows: Dict[str, int] = {}
        self._timestamps: Dict[str, list] = defaultdict(list)
        self._default_limit = default_limit
        self._default_window = window_seconds
    
    def set_limit(self, key: str, limit: int, window: int = 1):
        self._limits[key] = limit
        self._windows[key] = window
    
    def _cleanup(self, key: str):
        now = time.time()
        window = self._windows.get(key, self._default_window)
        self._timestamps[key] = [t for t in self._timestamps[key] if now - t < window]
    
    def can_proceed(self, key: str) -> bool:
        self._cleanup(key)
        limit = self._limits.get(key, self._default_limit)
        return len(self._timestamps[key]) < limit
    
    async def acquire(self, key: str):
        while not self.can_proceed(key):
            await asyncio.sleep(0.1)
        self._timestamps[key].append(time.time())
    
    def get_remaining(self, key: str) -> int:
        self._cleanup(key)
        limit = self._limits.get(key, self._default_limit)
        return max(0, limit - len(self._timestamps[key]))
