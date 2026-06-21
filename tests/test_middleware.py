"""
Comprehensive isolated tests for src/bots/middleware.py.
"""
import asyncio
import time

import pytest

from src.bots.middleware import (
    MiddlewarePipeline,
    RateLimitMiddleware,
    LoggingMiddleware,
    AuthMiddleware,
    MaskMiddleware,
    MetricsMiddleware,
    RetryMiddleware,
    FilterMiddleware,
)


class TestMiddlewarePipeline:
    def test_empty_pipeline(self):
        pipe = MiddlewarePipeline()
        assert len(pipe._middleware) == 0

    def test_add_middleware(self):
        pipe = MiddlewarePipeline()

        async def mw(ctx, next_h):
            return await next_h(ctx)

        pipe.add(mw)
        assert len(pipe._middleware) == 1

    def test_add_returns_self(self):
        pipe = MiddlewarePipeline()

        async def mw(ctx, next_h):
            return await next_h(ctx)

        result = pipe.add(mw)
        assert result is pipe

    def test_remove_middleware(self):
        pipe = MiddlewarePipeline()

        async def mw(ctx, next_h):
            return await next_h(ctx)

        pipe.add(mw)
        pipe.remove(mw)
        assert len(pipe._middleware) == 0

    def test_execute_empty_pipeline(self):
        pipe = MiddlewarePipeline()

        async def handler(ctx):
            return "result"

        result = asyncio.run(
            pipe.execute("context", handler)
        )
        assert result == "result"

    def test_execute_with_middleware(self):
        pipe = MiddlewarePipeline()

        async def mw(ctx, next_h):
            return await next_h(ctx)

        pipe.add(mw)

        async def handler(ctx):
            return "result"

        result = asyncio.run(
            pipe.execute("context", handler)
        )
        assert result == "result"

    def test_execute_middleware_order(self):
        pipe = MiddlewarePipeline()
        order = []

        async def mw1(ctx, next_h):
            order.append("mw1_before")
            result = await next_h(ctx)
            order.append("mw1_after")
            return result

        async def mw2(ctx, next_h):
            order.append("mw2_before")
            result = await next_h(ctx)
            order.append("mw2_after")
            return result

        pipe.add(mw1).add(mw2)

        async def handler(ctx):
            order.append("handler")
            return "done"

        asyncio.run(
            pipe.execute("ctx", handler)
        )
        assert order == ["mw1_before", "mw2_before", "handler", "mw2_after", "mw1_after"]

    def test_middleware_can_shortcircuit(self):
        pipe = MiddlewarePipeline()

        async def blocking_mw(ctx, next_h):
            return "blocked"

        pipe.add(blocking_mw)

        async def handler(ctx):
            return "should not run"

        result = asyncio.run(
            pipe.execute("ctx", handler)
        )
        assert result == "blocked"


class TestRateLimitMiddleware:
    def test_allows_under_limit(self):
        rl = RateLimitMiddleware(max_per_second=5)

        class Ctx:
            chat_id = "chat1"

        async def handler(ctx):
            return "ok"

        result = asyncio.run(
            rl(Ctx(), handler)
        )
        assert result == "ok"

    def test_blocks_over_limit(self):
        rl = RateLimitMiddleware(max_per_second=2)

        class Ctx:
            chat_id = "chat1"

        async def handler(ctx):
            return "ok"

        asyncio.run(rl(Ctx(), handler))
        asyncio.run(rl(Ctx(), handler))
        result = asyncio.run(rl(Ctx(), handler))
        assert result is None

    def test_different_chats_independent(self):
        rl = RateLimitMiddleware(max_per_second=1)

        class Ctx1:
            chat_id = "chat1"

        class Ctx2:
            chat_id = "chat2"

        async def handler(ctx):
            return "ok"

        asyncio.run(rl(Ctx1(), handler))
        result = asyncio.run(rl(Ctx2(), handler))
        assert result == "ok"


class TestLoggingMiddleware:
    def test_logging_calls_next(self):
        lm = LoggingMiddleware()

        class Ctx:
            chat_id = "chat1"
            user_id = 123
            text = "hello"
            message_type = "text"

        async def handler(ctx):
            return "logged"

        result = asyncio.run(lm(Ctx(), handler))
        assert result == "logged"

    def test_logging_handles_string_msg_type(self):
        lm = LoggingMiddleware()

        class Ctx:
            chat_id = "chat1"
            user_id = 123
            text = "hello"
            message_type = "unknown"

        async def handler(ctx):
            return "ok"

        result = asyncio.run(lm(Ctx(), handler))
        assert result == "ok"

    def test_logging_handles_enum_msg_type(self):
        from src.bots.bot_core import MessageType
        lm = LoggingMiddleware()

        class Ctx:
            chat_id = "chat1"
            user_id = 123
            text = "hello"
            message_type = MessageType.TEXT

        async def handler(ctx):
            return "ok"

        result = asyncio.run(lm(Ctx(), handler))
        assert result == "ok"


class TestAuthMiddleware:
    def test_allows_all_when_no_restrictions(self):
        am = AuthMiddleware()

        class Ctx:
            user_id = 123
            chat_id = "chat1"

        async def handler(ctx):
            return "allowed"

        result = asyncio.run(am(Ctx(), handler))
        assert result == "allowed"

    def test_allows_authorized_user(self):
        am = AuthMiddleware(allowed_users=[123, 456])

        class Ctx:
            user_id = 123
            chat_id = "chat1"

        async def handler(ctx):
            return "allowed"

        result = asyncio.run(am(Ctx(), handler))
        assert result == "allowed"

    def test_blocks_unauthorized_user(self):
        am = AuthMiddleware(allowed_users=[123])

        class Ctx:
            user_id = 999
            chat_id = "chat1"

        async def handler(ctx):
            return "should not run"

        result = asyncio.run(am(Ctx(), handler))
        assert result is None

    def test_allows_authorized_chat(self):
        am = AuthMiddleware(allowed_chats=["chat1"])

        class Ctx:
            user_id = 123
            chat_id = "chat1"

        async def handler(ctx):
            return "allowed"

        result = asyncio.run(am(Ctx(), handler))
        assert result == "allowed"

    def test_blocks_unauthorized_chat(self):
        am = AuthMiddleware(allowed_chats=["chat1"])

        class Ctx:
            user_id = 123
            chat_id = "other_chat"

        async def handler(ctx):
            return "should not run"

        result = asyncio.run(am(Ctx(), handler))
        assert result is None


class TestMetricsMiddleware:
    def test_counts_messages(self):
        mm = MetricsMiddleware()

        class Ctx:
            pass

        async def handler(ctx):
            return "ok"

        asyncio.run(mm(Ctx(), handler))
        asyncio.run(mm(Ctx(), handler))
        assert mm.total_messages == 2

    def test_counts_errors(self):
        mm = MetricsMiddleware()

        class Ctx:
            pass

        async def handler(ctx):
            raise ValueError("error")

        with pytest.raises(ValueError):
            asyncio.run(mm(Ctx(), handler))
        assert mm.total_errors == 1

    def test_get_stats(self):
        mm = MetricsMiddleware()

        class Ctx:
            pass

        async def handler(ctx):
            return "ok"

        asyncio.run(mm(Ctx(), handler))
        stats = mm.get_stats()
        assert stats["total_messages"] == 1
        assert stats["total_errors"] == 0
        assert stats["avg_duration_ms"] >= 0
        assert stats["uptime_seconds"] >= 0


class TestRetryMiddleware:
    def test_no_retry_on_success(self):
        rm = RetryMiddleware(max_retries=3, base_delay=0.01)
        call_count = 0

        class Ctx:
            pass

        async def handler(ctx):
            nonlocal call_count
            call_count += 1
            return "ok"

        result = asyncio.run(rm(Ctx(), handler))
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_failure(self):
        rm = RetryMiddleware(max_retries=3, base_delay=0.01)
        call_count = 0

        class Ctx:
            pass

        async def handler(ctx):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("error")
            return "ok"

        result = asyncio.run(rm(Ctx(), handler))
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        rm = RetryMiddleware(max_retries=2, base_delay=0.01)

        class Ctx:
            pass

        async def handler(ctx):
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            asyncio.run(rm(Ctx(), handler))


class TestFilterMiddleware:
    def test_passes_filter(self):
        fm = FilterMiddleware(lambda ctx: True)

        class Ctx:
            pass

        async def handler(ctx):
            return "ok"

        result = asyncio.run(fm(Ctx(), handler))
        assert result == "ok"

    def test_blocks_filter(self):
        fm = FilterMiddleware(lambda ctx: False)

        class Ctx:
            pass

        async def handler(ctx):
            return "should not run"

        result = asyncio.run(fm(Ctx(), handler))
        assert result is None

    def test_default_filter(self):
        fm = FilterMiddleware()

        class Ctx:
            pass

        async def handler(ctx):
            return "ok"

        result = asyncio.run(fm(Ctx(), handler))
        assert result == "ok"


class TestMaskMiddleware:
    def test_no_mask_manager(self):
        mm = MaskMiddleware()

        class Ctx:
            pass

        async def handler(ctx):
            return "hello"

        result = asyncio.run(mm(Ctx(), handler))
        assert result == "hello"

    def test_applies_persona(self):
        from src.masks.mask_registry import MaskRegistry, Mask, MaskType
        from src.masks.mask_manager import MaskManager
        registry = MaskRegistry()
        manager = MaskManager(registry)
        mask = Mask(
            mask_id="test_mask",
            name="Test",
            mask_type=MaskType.SUPPORT,
            business_id="biz",
            display_name="SupportBot",
            response_style="professional",
            restricted_words=["badword"],
        )
        registry.register(mask)
        manager.assign_mask("bot1", "test_mask")

        mm = MaskMiddleware(manager)

        class Ctx:
            metadata = {"bot_id": "bot1"}

        async def handler(ctx):
            return "message with badword"

        result = asyncio.run(mm(Ctx(), handler))
        assert "badword" not in result
        assert "***" in result
