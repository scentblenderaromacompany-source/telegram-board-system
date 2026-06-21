"""
Comprehensive isolated tests for src/bots/bot_core.py.
"""
import time

import pytest

from src.bots.bot_core import (
    TelegramBot,
    BotConfig,
    BotState,
    MessageType,
    BotMetrics,
    MessageContext,
)


class TestBotConfig:
    def test_creation(self):
        c = BotConfig(
            token="tok",
            bot_id="bid",
            name="Name",
            business_id="biz",
        )
        assert c.token == "tok"
        assert c.bot_id == "bid"
        assert c.name == "Name"
        assert c.business_id == "biz"
        assert c.mask_id is None
        assert c.webhook_url is None
        assert c.rate_limit == 30
        assert c.max_message_length == 4096
        assert c.parse_mode == "HTML"

    def test_defaults(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        assert c.allowed_chat_ids == []
        assert c.allowed_user_ids == []
        assert c.disable_web_page_preview is False
        assert c.disable_notification is False
        assert c.settings == {}


class TestBotState:
    def test_values(self):
        assert BotState.IDLE.value == "idle"
        assert BotState.STARTING.value == "starting"
        assert BotState.RUNNING.value == "running"
        assert BotState.PROCESSING.value == "processing"
        assert BotState.WAITING.value == "waiting"
        assert BotState.STOPPING.value == "stopping"
        assert BotState.ERROR.value == "error"

    def test_count(self):
        assert len(BotState) == 7


class TestMessageType:
    def test_values(self):
        assert MessageType.TEXT.value == "text"
        assert MessageType.PHOTO.value == "photo"
        assert MessageType.VIDEO.value == "video"
        assert MessageType.DOCUMENT.value == "document"
        assert MessageType.AUDIO.value == "audio"
        assert MessageType.VOICE.value == "voice"
        assert MessageType.STICKER.value == "sticker"
        assert MessageType.CALLBACK.value == "callback"
        assert MessageType.INLINE.value == "inline"
        assert MessageType.UNKNOWN.value == "unknown"

    def test_count(self):
        assert len(MessageType) == 10


class TestBotMetrics:
    def test_defaults(self):
        m = BotMetrics()
        assert m.messages_received == 0
        assert m.messages_sent == 0
        assert m.errors == 0
        assert m.avg_response_time == 0
        assert m._response_times == []

    def test_record_response(self):
        m = BotMetrics()
        m.record_response(0.1)
        m.record_response(0.2)
        assert abs(m.avg_response_time - 0.15) < 1e-9

    def test_record_response_trimming(self):
        m = BotMetrics()
        for i in range(1001):
            m.record_response(0.001)
        assert len(m._response_times) == 500

    def test_uptime(self):
        m = BotMetrics()
        time.sleep(0.01)
        assert m.uptime > 0

    def test_to_dict(self):
        m = BotMetrics()
        d = m.to_dict()
        assert "messages_received" in d
        assert "messages_sent" in d
        assert "errors" in d
        assert "uptime_seconds" in d
        assert "avg_response_time_ms" in d


class TestTelegramBotInit:
    def test_init(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)
        assert bot.state == BotState.IDLE
        assert bot.config.bot_id == "b"
        assert bot._handlers == {}
        assert bot._middleware == []
        assert bot._error_handlers == []

    def test_command_decorator(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        @bot.command("start", "Start the bot")
        async def start_handler(ctx):
            pass

        assert "start" in bot._handlers
        assert bot._custom_commands["start"] == "Start the bot"

    def test_on_message_decorator(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        @bot.on_message
        async def handler(ctx):
            pass

        assert "__message__" in bot._handlers

    def test_on_callback_decorator(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        @bot.on_callback
        async def handler(ctx):
            pass

        assert "__callback__" in bot._handlers

    def test_use_middleware(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        async def mw(ctx, next_h):
            return await next_h(ctx)

        result = bot.use(mw)
        assert result is bot
        assert mw in bot._middleware

    def test_on_error(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        async def err_handler(update, context):
            pass

        result = bot.on_error(err_handler)
        assert result is bot
        assert err_handler in bot._error_handlers

    def test_before_send(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        async def hook(chat_id, text, kwargs):
            return kwargs

        result = bot.before_send(hook)
        assert result is bot
        assert hook in bot._before_send_hooks

    def test_after_send(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)

        async def hook(chat_id, text, result):
            pass

        result = bot.after_send(hook)
        assert result is bot
        assert hook in bot._after_send_hooks


class TestSplitMessage:
    def test_short_message(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)
        assert bot._split_message("hello") == ["hello"]

    def test_long_message(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz", max_message_length=100)
        bot = TelegramBot(c)
        text = "a" * 200
        chunks = bot._split_message(text)
        assert len(chunks) > 1

    def test_split_prefers_newline(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz", max_message_length=20)
        bot = TelegramBot(c)
        text = "aaaa\nbbbb\ncccc\ndddd\neeee\nffff"
        chunks = bot._split_message(text)
        assert len(chunks) > 1
        assert "\n" in chunks[0]


class TestGetHelpText:
    def test_custom_commands(self):
        c = BotConfig(token="t", bot_id="b", name="TestBot", business_id="biz")
        bot = TelegramBot(c)
        bot._custom_commands["start"] = "Start the bot"
        text = bot._get_help_text()
        assert "TestBot" in text
        assert "start" in text

    def test_default_commands(self):
        c = BotConfig(token="t", bot_id="b", name="TestBot", business_id="biz")
        bot = TelegramBot(c)
        text = bot._get_help_text()
        assert "/start" in text
        assert "/help" in text
        assert "/status" in text
        assert "/ping" in text


class TestGetStatusText:
    def test_status_text(self):
        c = BotConfig(token="t", bot_id="b", name="TestBot", business_id="biz")
        bot = TelegramBot(c)
        text = bot._get_status_text()
        assert "idle" in text
        assert "Uptime" in text


class TestGetMetrics:
    def test_metrics_dict(self):
        c = BotConfig(token="t", bot_id="b", name="n", business_id="biz")
        bot = TelegramBot(c)
        metrics = bot.get_metrics()
        assert "messages_received" in metrics
        assert "messages_sent" in metrics
        assert "errors" in metrics
