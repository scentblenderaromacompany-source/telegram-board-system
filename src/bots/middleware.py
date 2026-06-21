"""
Middleware pipeline for Telegram bots.
"""
import asyncio
import logging
import time
from typing import Callable, Awaitable, Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

MiddlewareFunc = Callable[..., Awaitable[Any]]

class MiddlewarePipeline:
    """Composable middleware pipeline for message processing."""

    def __init__(self):
        self._middleware: list = []

    def add(self, middleware: MiddlewareFunc):
        """Add middleware to the pipeline."""
        self._middleware.append(middleware)
        return self

    def remove(self, middleware: MiddlewareFunc):
        """Remove middleware from the pipeline."""
        self._middleware.remove(middleware)

    async def execute(self, context: Any, handler: Callable) -> Any:
        """Execute the middleware pipeline."""
        pipeline = handler
        for mw in reversed(self._middleware):
            next_handler = pipeline
            async def chain(ctx, next_h=next_handler, m=mw):
                return await m(ctx, next_h)
            pipeline = chain
        return await pipeline(context)


class RateLimitMiddleware:
    """Rate limiting middleware."""

    def __init__(self, max_per_second: int = 5, max_per_chat: int = 30):
        self._max_per_second = max_per_second
        self._max_per_chat = max_per_chat
        self._timestamps: Dict[str, list] = {}
        self._chat_counts: Dict[str, int] = {}

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        chat_id = getattr(context, "chat_id", "unknown")
        now = time.time()

        if chat_id not in self._timestamps:
            self._timestamps[chat_id] = []

        self._timestamps[chat_id] = [
            t for t in self._timestamps[chat_id] if now - t < 1.0
        ]

        if len(self._timestamps[chat_id]) >= self._max_per_second:
            logger.warning(f"Rate limit exceeded for chat {chat_id}")
            return None

        self._timestamps[chat_id].append(now)
        return await next_handler(context)


class LoggingMiddleware:
    """Logging middleware for debugging."""

    def __init__(self, log_level: int = logging.INFO):
        self._log_level = log_level

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        chat_id = getattr(context, "chat_id", "unknown")
        user_id = getattr(context, "user_id", "unknown")
        text = getattr(context, "text", None)
        msg_type = getattr(context, "message_type", "unknown")
        msg_type_str = msg_type.value if hasattr(msg_type, "value") else str(msg_type)

        logger.log(self._log_level, f"[{msg_type_str}] chat={chat_id} user={user_id} text={text!r}")

        start = time.time()
        result = await next_handler(context)
        duration = time.time() - start

        logger.log(self._log_level, f"[DONE] chat={chat_id} duration={duration:.3f}s")
        return result


class AuthMiddleware:
    """Authentication middleware for access control."""

    def __init__(self, allowed_users: list = None, allowed_chats: list = None):
        self._allowed_users = set(allowed_users or [])
        self._allowed_chats = set(allowed_chats or [])

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        user_id = getattr(context, "user_id", 0)
        chat_id = getattr(context, "chat_id", "")

        if self._allowed_users and user_id not in self._allowed_users:
            logger.warning(f"Unauthorized user: {user_id}")
            return None

        if self._allowed_chats and chat_id not in self._allowed_chats:
            logger.warning(f"Unauthorized chat: {chat_id}")
            return None

        return await next_handler(context)


class MaskMiddleware:
    """Apply bot mask to responses."""

    def __init__(self, mask_manager=None):
        self._mask_manager = mask_manager

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        result = await next_handler(context)

        if self._mask_manager and hasattr(context, "metadata"):
            bot_id = context.metadata.get("bot_id")
            if bot_id and isinstance(result, str):
                result = self._mask_manager.apply_persona(bot_id, result)

        return result


class MetricsMiddleware:
    """Collect metrics on message processing."""

    def __init__(self):
        self.total_messages = 0
        self.total_errors = 0
        self.total_duration = 0.0
        self._start_time = time.time()

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        self.total_messages += 1
        start = time.time()
        try:
            result = await next_handler(context)
            self.total_duration += time.time() - start
            return result
        except Exception as e:
            self.total_errors += 1
            raise

    def get_stats(self) -> Dict:
        uptime = time.time() - self._start_time
        return {
            "total_messages": self.total_messages,
            "total_errors": self.total_errors,
            "avg_duration_ms": (self.total_duration / max(self.total_messages, 1)) * 1000,
            "messages_per_second": self.total_messages / max(uptime, 1),
            "uptime_seconds": uptime,
        }


class RetryMiddleware:
    """Retry failed operations with exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 0.5):
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                return await next_handler(context)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{self._max_retries} after {delay}s: {e}")
                    await asyncio.sleep(delay)
        raise last_error


class FilterMiddleware:
    """Filter messages based on conditions."""

    def __init__(self, filter_func: Callable = None):
        self._filter_func = filter_func or (lambda ctx: True)

    async def __call__(self, context: Any, next_handler: Callable) -> Any:
        if self._filter_func(context):
            return await next_handler(context)
        return None
