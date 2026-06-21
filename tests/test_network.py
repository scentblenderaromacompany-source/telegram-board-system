"""
Comprehensive isolated tests for src/telegram/network.py.
"""
import pytest

from src.telegram.network import (
    TelegramFallbackTransport,
    discover_fallback_ips,
    _normalize_fallback_ips,
    _SEED_FALLBACK_IPS,
    _TELEGRAM_API_HOST,
)


class TestNormalizeFallbackIps:
    def test_normalize_valid_ips(self):
        ips = ["149.154.167.220", "149.154.167.221"]
        result = _normalize_fallback_ips(ips)
        assert result == ["149.154.167.220", "149.154.167.221"]

    def test_normalize_deduplicates(self):
        ips = ["149.154.167.220", "149.154.167.220", "149.154.167.221"]
        result = _normalize_fallback_ips(ips)
        assert len(result) == 2

    def test_normalize_invalid_ips(self):
        ips = ["invalid", "also_invalid", "149.154.167.220"]
        result = _normalize_fallback_ips(ips)
        assert result == ["149.154.167.220"]

    def test_normalize_empty(self):
        assert _normalize_fallback_ips([]) == []

    def test_normalize_ipv6_filtered(self):
        ips = ["::1", "149.154.167.220"]
        result = _normalize_fallback_ips(ips)
        assert result == ["149.154.167.220"]


class TestConstants:
    def test_seed_ips(self):
        assert len(_SEED_FALLBACK_IPS) == 3
        assert "149.154.167.220" in _SEED_FALLBACK_IPS

    def test_api_host(self):
        assert _TELEGRAM_API_HOST == "api.telegram.org"


class TestTelegramFallbackTransport:
    def test_default_init(self):
        t = TelegramFallbackTransport()
        assert t._fallback_ips == _SEED_FALLBACK_IPS
        assert t._proxy_url is None
        assert t._sticky_ip is None

    def test_custom_fallback_ips(self):
        custom_ips = ["1.2.3.4", "5.6.7.8"]
        t = TelegramFallbackTransport(fallback_ips=custom_ips)
        assert t._fallback_ips == custom_ips

    def test_proxy_url(self):
        t = TelegramFallbackTransport(proxy_url="http://proxy:8080")
        assert t._proxy_url == "http://proxy:8080"

    def test_get_client_kwargs_no_proxy(self):
        t = TelegramFallbackTransport()
        kwargs = t.get_client_kwargs()
        assert kwargs == {}

    def test_get_client_kwargs_with_proxy(self):
        t = TelegramFallbackTransport(proxy_url="http://proxy:8080")
        kwargs = t.get_client_kwargs()
        assert kwargs["proxy"] == "http://proxy:8080"

    def test_sticky_ip_initial_none(self):
        t = TelegramFallbackTransport()
        assert t._sticky_ip is None

    def test_sticky_lock_created(self):
        t = TelegramFallbackTransport()
        assert t._sticky_lock is not None


class TestDiscoverFallbackIps:
    def test_returns_seed_ips_on_no_httpx(self):
        import asyncio
        result = asyncio.run(discover_fallback_ips())
        assert isinstance(result, list)
        assert len(result) > 0
