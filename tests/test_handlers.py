"""
Comprehensive isolated tests for src/bots/handlers.py.
"""
import asyncio
import re

import pytest

from src.bots.handlers import (
    HandlerRegistry,
    ConversationHandler,
    InlineQueryHandler,
    MatchType,
)


class TestMatchType:
    def test_values(self):
        assert MatchType.EXACT.value == "exact"
        assert MatchType.CONTAINS.value == "contains"
        assert MatchType.STARTS_WITH.value == "starts_with"
        assert MatchType.ENDS_WITH.value == "ends_with"
        assert MatchType.REGEX.value == "regex"
        assert MatchType.FUZZY.value == "fuzzy"


class TestHandlerRegistry:
    def test_empty_registry(self):
        reg = HandlerRegistry()
        assert reg.match_message("anything") is None
        assert reg.match_callback("anything") is None

    def test_on_command(self):
        reg = HandlerRegistry()

        @reg.on_command("start", "Start bot")
        async def start(ctx):
            pass

        assert "start" in reg._handlers
        assert reg._handlers["start"]["description"] == "Start bot"

    def test_on_pattern_contains(self):
        reg = HandlerRegistry()

        @reg.on_pattern("hello", MatchType.CONTAINS)
        async def hello(ctx):
            pass

        assert len(reg._pattern_handlers) == 1
        handler = reg.match_message("say hello world")
        assert handler is not None

    def test_on_pattern_exact(self):
        reg = HandlerRegistry()

        @reg.on_pattern("hello", MatchType.EXACT)
        async def hello(ctx):
            pass

        assert reg.match_message("hello") is not None
        assert reg.match_message("hello world") is None

    def test_on_pattern_starts_with(self):
        reg = HandlerRegistry()

        @reg.on_pattern("hello", MatchType.STARTS_WITH)
        async def hello(ctx):
            pass

        assert reg.match_message("hello world") is not None
        assert reg.match_message("world hello") is None

    def test_on_pattern_ends_with(self):
        reg = HandlerRegistry()

        @reg.on_pattern("world", MatchType.ENDS_WITH)
        async def world(ctx):
            pass

        assert reg.match_message("hello world") is not None
        assert reg.match_message("world hello") is None

    def test_on_pattern_regex(self):
        reg = HandlerRegistry()

        @reg.on_pattern(r"^\d+$", MatchType.REGEX)
        async def numbers(ctx):
            pass

        assert reg.match_message("12345") is not None
        assert reg.match_message("abc") is None

    def test_on_keyword(self):
        reg = HandlerRegistry()

        @reg.on_keyword("help", "support")
        async def help_handler(ctx):
            pass

        assert reg.match_message("I need help") is not None
        assert reg.match_message("support please") is not None

    def test_on_regex(self):
        reg = HandlerRegistry()

        @reg.on_regex(r"\bhello\b")
        async def hello(ctx):
            pass

        assert reg.match_message("say hello world") is not None
        assert reg.match_message("hello!") is not None
        assert reg.match_message("shello") is None

    def test_priority_ordering(self):
        reg = HandlerRegistry()
        high_called = []
        low_called = []

        @reg.on_pattern("test", MatchType.CONTAINS, priority=10)
        async def high_priority(ctx):
            high_called.append(True)

        @reg.on_pattern("test", MatchType.CONTAINS, priority=1)
        async def low_priority(ctx):
            low_called.append(True)

        handler = reg.match_message("test message")
        assert handler is not None

    def test_on_callback(self):
        reg = HandlerRegistry()

        @reg.on_callback("^action:.*")
        async def action_handler(ctx):
            pass

        handler = reg.match_callback("action:buy")
        assert handler is not None

    def test_on_callback_no_match(self):
        reg = HandlerRegistry()

        @reg.on_callback("^action:.*")
        async def action_handler(ctx):
            pass

        handler = reg.match_callback("other:data")
        assert handler is None

    def test_on_fallback(self):
        reg = HandlerRegistry()

        @reg.on_fallback()
        async def fallback(ctx):
            pass

        assert reg.match_message("anything") is not None

    def test_fallback_not_used_when_match(self):
        reg = HandlerRegistry()

        @reg.on_pattern("hello", MatchType.CONTAINS)
        async def hello(ctx):
            pass

        @reg.on_fallback()
        async def fallback(ctx):
            pass

        assert reg.match_message("hello") is not None

    def test_case_insensitive_contains(self):
        reg = HandlerRegistry()

        @reg.on_pattern("hello", MatchType.CONTAINS)
        async def hello(ctx):
            pass

        assert reg.match_message("HELLO world") is not None
        assert reg.match_message("HeLLo") is not None

    def test_get_help(self):
        reg = HandlerRegistry()

        @reg.on_command("start", "Start bot")
        async def start(ctx):
            pass

        @reg.on_command("help", "Show help")
        async def help_cmd(ctx):
            pass

        help_list = reg.get_help()
        assert len(help_list) == 2
        assert any(c["command"] == "start" for c in help_list)


class TestConversationHandler:
    def test_empty_handler(self):
        ch = ConversationHandler()
        assert ch.get_user_state(123) is None

    def test_set_and_get_state(self):
        ch = ConversationHandler()
        ch.set_user_state(123, "waiting_input")
        assert ch.get_user_state(123) == "waiting_input"

    def test_set_state_with_data(self):
        ch = ConversationHandler()
        ch.set_user_state(123, "step1", {"key": "value"})
        state = ch._user_states[123]
        assert state["state"] == "step1"
        assert state["data"]["key"] == "value"

    def test_clear_state(self):
        ch = ConversationHandler()
        ch.set_user_state(123, "step1")
        ch.clear_user_state(123)
        assert ch.get_user_state(123) is None

    def test_clear_nonexistent(self):
        ch = ConversationHandler()
        ch.clear_user_state(999)

    def test_state_decorator(self):
        ch = ConversationHandler()

        @ch.state("step1", next="step2")
        async def step1(user_id, message, data):
            return "step1_response"

        assert "step1" in ch._states
        assert ch._states["step1"]["next"] == "step2"

    def test_handle_no_state(self):
        ch = ConversationHandler()

        async def handler(user_id, message, data):
            return "response"

        result = asyncio.run(ch.handle(123, "message"))
        assert result is None

    def test_handle_with_state(self):
        ch = ConversationHandler()

        @ch.state("step1")
        async def step1(user_id, message, data):
            return f"Got: {message}"

        ch.set_user_state(123, "step1")
        result = asyncio.run(ch.handle(123, "hello"))
        assert result == "Got: hello"

    def test_handle_advances_state(self):
        ch = ConversationHandler()

        @ch.state("step1", next="step2")
        async def step1(user_id, message, data):
            return "step1 done"

        @ch.state("step2")
        async def step2(user_id, message, data):
            return "step2 done"

        ch.set_user_state(123, "step1")
        asyncio.run(ch.handle(123, "go"))
        assert ch.get_user_state(123) == "step2"


class TestInlineQueryHandler:
    def test_empty(self):
        ih = InlineQueryHandler()
        assert ih.match("anything") is None

    def test_register_and_match(self):
        ih = InlineQueryHandler()

        @ih.on_inline("^search:.*")
        async def search(query):
            return "results"

        handler = ih.match("search:hello")
        assert handler is not None

    def test_no_match(self):
        ih = InlineQueryHandler()

        @ih.on_inline("^search:.*")
        async def search(query):
            return "results"

        handler = ih.match("other:data")
        assert handler is None

    def test_default_pattern(self):
        ih = InlineQueryHandler()

        @ih.on_inline()
        async def catch_all(query):
            return "results"

        handler = ih.match("anything")
        assert handler is not None
