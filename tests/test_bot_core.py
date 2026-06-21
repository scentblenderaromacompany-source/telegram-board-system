"""
Tests for bot core framework.
"""
import asyncio
import pytest
from src.bots.bot_core import TelegramBot, BotConfig, BotState, MessageType, BotMetrics

def test_bot_config():
    config = BotConfig(
        token="test-token",
        bot_id="test-bot",
        name="Test Bot",
        business_id="test-business",
    )
    assert config.bot_id == "test-bot"
    assert config.rate_limit == 30

def test_bot_state():
    assert BotState.IDLE.value == "idle"
    assert BotState.RUNNING.value == "running"

def test_message_type():
    assert MessageType.TEXT.value == "text"
    assert MessageType.PHOTO.value == "photo"

def test_bot_metrics():
    metrics = BotMetrics()
    metrics.record_response(0.1)
    metrics.record_response(0.2)
    assert abs(metrics.avg_response_time - 0.15) < 1e-9
    assert metrics.messages_received == 0

def test_bot_init():
    config = BotConfig(
        token="test",
        bot_id="test",
        name="Test",
        business_id="test",
    )
    bot = TelegramBot(config)
    assert bot.state == BotState.IDLE
    assert bot.config.bot_id == "test"
