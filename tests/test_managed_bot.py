"""
Comprehensive isolated tests for src/telegram/managed_bot.py.
"""
import pytest

from src.telegram.managed_bot import (
    TelegramManagedBot,
    TelegramPairing,
    TelegramBotSetupResult,
    is_valid_telegram_bot_token,
    DEFAULT_API_URL,
    DEFAULT_MANAGER_BOT,
    DEFAULT_BOT_NAME,
    DEFAULT_POLL_TIMEOUT,
    POLL_INTERVAL,
)


class TestTokenValidation:
    def test_valid_token(self):
        assert is_valid_telegram_bot_token("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890") is True

    def test_valid_token_long(self):
        assert is_valid_telegram_bot_token("9999999999:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij") is True

    def test_invalid_token_no_colon(self):
        assert is_valid_telegram_bot_token("1234567890ABCdef") is False

    def test_invalid_token_too_short(self):
        assert is_valid_telegram_bot_token("1:abc") is False

    def test_invalid_token_empty(self):
        assert is_valid_telegram_bot_token("") is False

    def test_invalid_token_none(self):
        assert is_valid_telegram_bot_token(None) is False

    def test_invalid_token_integer(self):
        assert is_valid_telegram_bot_token(12345) is False

    def test_invalid_token_special_chars(self):
        assert is_valid_telegram_bot_token("1234567890:ABC!@#$%^&*()") is False

    def test_valid_token_underscores(self):
        assert is_valid_telegram_bot_token("1234567890:ABC_def_GHI_jkl_MNO_pqr_stu_vwx_yz_12345678") is True

    def test_valid_token_hyphens(self):
        assert is_valid_telegram_bot_token("1234567890:ABC-def-GHI-jkl-MNO-pqr-stu-vwx-yz-12345678") is True


class TestTelegramPairing:
    def test_pairing_creation(self):
        p = TelegramPairing(
            pairing_id="abc123",
            poll_token="xyz789",
            suggested_username="test_bot",
            deep_link="https://t.me/Bot?start=abc123",
            qr_payload="https://t.me/Bot?start=abc123",
        )
        assert p.pairing_id == "abc123"
        assert p.poll_token == "xyz789"
        assert p.suggested_username == "test_bot"
        assert p.deep_link == "https://t.me/Bot?start=abc123"
        assert p.qr_payload == "https://t.me/Bot?start=abc123"

    def test_pairing_frozen(self):
        p = TelegramPairing(
            pairing_id="abc",
            poll_token="xyz",
            suggested_username="bot",
            deep_link="link",
            qr_payload="qr",
        )
        with pytest.raises(AttributeError):
            p.pairing_id = "new"

    def test_pairing_optional_expiry(self):
        p = TelegramPairing(
            pairing_id="abc",
            poll_token="xyz",
            suggested_username="bot",
            deep_link="link",
            qr_payload="qr",
        )
        assert p.expires_at is None


class TestTelegramBotSetupResult:
    def test_result_creation(self):
        r = TelegramBotSetupResult(
            token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890",
            bot_username="test_bot",
            owner_user_id=12345,
        )
        assert r.token.startswith("12345")
        assert r.bot_username == "test_bot"
        assert r.owner_user_id == 12345

    def test_result_optional_fields(self):
        r = TelegramBotSetupResult(token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890")
        assert r.bot_username is None
        assert r.owner_user_id is None

    def test_result_frozen(self):
        r = TelegramBotSetupResult(token="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890")
        with pytest.raises(AttributeError):
            r.token = "new"


class TestTelegramManagedBot:
    def test_default_api_url(self):
        bot = TelegramManagedBot()
        assert bot._api_url == DEFAULT_API_URL

    def test_custom_api_url(self):
        bot = TelegramManagedBot("https://custom.api.com")
        assert bot._api_url == "https://custom.api.com"

    def test_strips_trailing_slash(self):
        bot = TelegramManagedBot("https://custom.api.com/")
        assert bot._api_url == "https://custom.api.com"

    def test_create_pairing(self):
        import asyncio
        bot = TelegramManagedBot()
        pairing = asyncio.run(bot.create_pairing())
        assert isinstance(pairing, TelegramPairing)
        assert len(pairing.pairing_id) > 0
        assert len(pairing.poll_token) > 0
        assert pairing.suggested_username.startswith("hermes_")
        assert pairing.deep_link.startswith("https://t.me/")
        assert pairing.qr_payload == pairing.deep_link

    def test_create_pairing_custom_manager(self):
        import asyncio
        bot = TelegramManagedBot()
        pairing = asyncio.run(bot.create_pairing("MySetupBot"))
        assert "MySetupBot" in pairing.deep_link

    def test_render_qr_terminal_no_qrcode(self):
        bot = TelegramManagedBot()
        result = bot.render_qr_terminal("https://example.com")
        assert "[QR:" in result or "example.com" in result


class TestConstants:
    def test_default_api_url(self):
        assert DEFAULT_API_URL == "https://setup.hermes-agent.nousresearch.com"

    def test_default_manager_bot(self):
        assert DEFAULT_MANAGER_BOT == "HermesSetupBot"

    def test_default_bot_name(self):
        assert DEFAULT_BOT_NAME == "Hermes Agent"

    def test_default_poll_timeout(self):
        assert DEFAULT_POLL_TIMEOUT == 180

    def test_poll_interval(self):
        assert POLL_INTERVAL == 2
