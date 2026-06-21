"""
Tests for Telegram-specific components.
"""
import pytest
from src.telegram.message_formatter import TelegramMessageFormatter
from src.telegram.media_handler import TelegramMediaHandler
from src.telegram.managed_bot import is_valid_telegram_bot_token, TelegramManagedBot
from src.telegram.commands import TelegramCommandRegistry, TelegramCommand
from src.telegram.webhook import TelegramWebhookManager


def test_formatter_escape_html():
    f = TelegramMessageFormatter()
    assert f.escape_html("<b>test</b>") == "&lt;b&gt;test&lt;/b&gt;"


def test_formatter_bold():
    f = TelegramMessageFormatter()
    assert f.bold("hello") == "<b>hello</b>"


def test_formatter_truncate():
    f = TelegramMessageFormatter()
    assert len(f.truncate("x" * 5000, 4096)) == 4096


def test_formatter_split():
    f = TelegramMessageFormatter()
    text = "\n".join([f"Line {i}" for i in range(100)])
    chunks = f.split(text, 500)
    assert len(chunks) > 1


def test_formatter_progress_bar():
    f = TelegramMessageFormatter()
    bar = f.progress_bar(50, 100)
    assert "50%" in bar


def test_formatter_table():
    f = TelegramMessageFormatter()
    result = f.table(["Name", "Value"], [["a", "1"], ["b", "2"]])
    assert "Name" in result


def test_media_handler_detect_type():
    h = TelegramMediaHandler()
    assert h.detect_type("photo.jpg") == "photo"
    assert h.detect_type("video.mp4") == "video"
    assert h.detect_type("doc.pdf") == "document"
    assert h.detect_type("audio.mp3") == "audio"


def test_media_handler_mime():
    h = TelegramMediaHandler()
    assert h.get_mime_type("test.png") == "image/png"
    assert h.get_mime_type("test.mp4") == "video/mp4"


def test_media_handler_caption():
    h = TelegramMediaHandler()
    assert len(h.format_caption("x" * 2000, 1024)) == 1024


def test_token_validation():
    assert is_valid_telegram_bot_token("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890")
    assert not is_valid_telegram_bot_token("invalid-token")
    assert not is_valid_telegram_bot_token("")
    assert not is_valid_telegram_bot_token(None)


def test_command_registry():
    reg = TelegramCommandRegistry()
    reg.register_default_commands()
    assert len(reg.list_commands()) >= 5
    assert reg.resolve("start") == "start"
    assert reg.resolve("m") == "mask"


def test_command_help_text():
    reg = TelegramCommandRegistry()
    reg.register_default_commands()
    help_text = reg.get_help_text()
    assert "Commands" in help_text


def test_command_bot_commands():
    reg = TelegramCommandRegistry()
    reg.register_default_commands()
    cmds = reg.get_bot_commands()
    assert len(cmds) >= 5
    assert all("command" in c and "description" in c for c in cmds)
