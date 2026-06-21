"""
Advanced handler system with decorators and pattern matching.
"""
import re
import logging
from typing import Dict, List, Optional, Callable, Any, Pattern
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class MatchType(Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    FUZZY = "fuzzy"


class HandlerRegistry:
    """Registry for message handlers with pattern matching."""

    def __init__(self):
        self._handlers: Dict[str, Dict] = {}
        self._pattern_handlers: List[Dict] = []
        self._callback_handlers: Dict[str, Callable] = {}
        self._fallback: Optional[Callable] = None

    def on_command(self, command: str, description: str = ""):
        """Decorator for command handlers."""
        def decorator(func):
            self._handlers[command] = {
                "handler": func,
                "description": description,
                "type": "command",
            }
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def on_pattern(self, pattern: str, match_type: MatchType = MatchType.CONTAINS, **kwargs):
        """Decorator for pattern-based handlers."""
        def decorator(func):
            entry = {
                "handler": func,
                "pattern": pattern,
                "match_type": match_type,
                "flags": kwargs.get("flags", 0),
                "priority": kwargs.get("priority", 0),
            }
            self._pattern_handlers.append(entry)
            self._pattern_handlers.sort(key=lambda x: -x["priority"])
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def on_keyword(self, *keywords, priority: int = 0):
        """Decorator for keyword-based handlers."""
        def decorator(func):
            for kw in keywords:
                entry = {
                    "handler": func,
                    "pattern": kw,
                    "match_type": MatchType.CONTAINS,
                    "priority": priority,
                }
                self._pattern_handlers.append(entry)
            self._pattern_handlers.sort(key=lambda x: -x["priority"])
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def on_regex(self, regex: str, flags: int = 0, priority: int = 0):
        """Decorator for regex handlers."""
        def decorator(func):
            entry = {
                "handler": func,
                "pattern": regex,
                "match_type": MatchType.REGEX,
                "flags": flags,
                "priority": priority,
            }
            self._pattern_handlers.append(entry)
            self._pattern_handlers.sort(key=lambda x: -x["priority"])
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def on_callback(self, pattern: str = ".*"):
        """Decorator for callback query handlers."""
        def decorator(func):
            self._callback_handlers[pattern] = func
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def on_fallback(self):
        """Decorator for fallback handler."""
        def decorator(func):
            self._fallback = func
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def match_message(self, text: str) -> Optional[Callable]:
        """Find matching handler for a message."""
        for entry in self._pattern_handlers:
            if self._matches(text, entry["pattern"], entry["match_type"], entry.get("flags", 0)):
                return entry["handler"]
        return self._fallback

    def match_callback(self, data: str) -> Optional[Callable]:
        """Find matching handler for callback data."""
        for pattern, handler in self._callback_handlers.items():
            if re.match(pattern, data):
                return handler
        return None

    def _matches(self, text: str, pattern: str, match_type: MatchType, flags: int = 0) -> bool:
        """Check if text matches pattern."""
        if match_type == MatchType.EXACT:
            return text.lower() == pattern.lower()
        elif match_type == MatchType.CONTAINS:
            return pattern.lower() in text.lower()
        elif match_type == MatchType.STARTS_WITH:
            return text.lower().startswith(pattern.lower())
        elif match_type == MatchType.ENDS_WITH:
            return text.lower().endswith(pattern.lower())
        elif match_type == MatchType.REGEX:
            return bool(re.search(pattern, text, flags))
        return False

    def get_help(self) -> List[Dict]:
        """Get list of all registered commands."""
        return [
            {"command": cmd, "description": info.get("description", "")}
            for cmd, info in self._handlers.items()
            if info["type"] == "command"
        ]


class ConversationHandler:
    """State machine for multi-step conversations."""

    def __init__(self):
        self._states: Dict[str, Dict] = {}
        self._user_states: Dict[int, Dict] = {}

    def state(self, state_name: str, **kwargs):
        """Decorator for conversation state handler."""
        def decorator(func):
            self._states[state_name] = {
                "handler": func,
                "next": kwargs.get("next"),
                "fallback": kwargs.get("fallback"),
            }
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def get_user_state(self, user_id: int) -> Optional[str]:
        """Get current state for a user."""
        state_info = self._user_states.get(user_id)
        return state_info.get("state") if state_info else None

    def set_user_state(self, user_id: int, state: str, data: Dict = None):
        """Set state for a user."""
        self._user_states[user_id] = {
            "state": state,
            "data": data or {},
        }

    def clear_user_state(self, user_id: int):
        """Clear state for a user."""
        self._user_states.pop(user_id, None)

    async def handle(self, user_id: int, message) -> Any:
        """Handle message in current conversation state."""
        state_name = self.get_user_state(user_id)
        if not state_name or state_name not in self._states:
            return None

        state_info = self._states[state_name]
        result = await state_info["handler"](user_id, message, self._user_states.get(user_id, {}).get("data", {}))

        if state_info.get("next"):
            self.set_user_state(user_id, state_info["next"])
        elif result is None:
            self.clear_user_state(user_id)

        return result


class InlineQueryHandler:
    """Handle inline queries."""

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def on_inline(self, pattern: str = ".*"):
        """Decorator for inline query handler."""
        def decorator(func):
            self._handlers[pattern] = func
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def match(self, query: str) -> Optional[Callable]:
        """Find matching handler for inline query."""
        for pattern, handler in self._handlers.items():
            if re.match(pattern, query):
                return handler
        return None
