"""
Comprehensive isolated tests for src/utils/ module.
"""
import asyncio
import time

import pytest

from src.utils.rate_limiter import RateLimiter
from src.utils.security import SecurityManager
from src.utils.metrics import MetricsCollector, HealthChecker
from src.utils.message_queue import MessageQueue, Message, Priority


class TestRateLimiter:
    def test_init(self):
        rl = RateLimiter()
        assert rl._default_limit == 30
        assert rl._default_window == 1

    def test_custom_limits(self):
        rl = RateLimiter(default_limit=10, window_seconds=5)
        assert rl._default_limit == 10
        assert rl._default_window == 5

    def test_can_proceed_under_limit(self):
        rl = RateLimiter(default_limit=5)
        assert rl.can_proceed("key") is True

    def test_can_proceed_at_limit(self):
        rl = RateLimiter(default_limit=2)
        rl.can_proceed("key")
        rl._timestamps["key"].append(time.time())
        rl._timestamps["key"].append(time.time())
        assert rl.can_proceed("key") is False

    def test_set_limit(self):
        rl = RateLimiter()
        rl.set_limit("special", 5, 10)
        assert rl._limits["special"] == 5
        assert rl._windows["special"] == 10

    def test_cleanup_old_timestamps(self):
        rl = RateLimiter(default_limit=5, window_seconds=1)
        rl._timestamps["key"] = [time.time() - 10]
        rl._cleanup("key")
        assert len(rl._timestamps["key"]) == 0

    def test_get_remaining(self):
        rl = RateLimiter(default_limit=5)
        assert rl.get_remaining("key") == 5
        rl._timestamps["key"].append(time.time())
        assert rl.get_remaining("key") == 4

    def test_acquire(self):
        rl = RateLimiter(default_limit=5)
        asyncio.run(rl.acquire("key"))
        assert len(rl._timestamps["key"]) == 1


class TestSecurityManager:
    def test_init(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        assert sm._secrets == {}

    def test_set_get_secret(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        sm.set_secret("api_key", "abc123")
        assert sm.get_secret("api_key") == "abc123"

    def test_get_secret_nonexistent(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        assert sm.get_secret("nonexistent") is None

    def test_generate_api_key(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        key = sm.generate_api_key("service1", ["read", "write"])
        assert len(key) > 0
        assert sm.verify_api_key("service1", key) is True

    def test_verify_api_key_wrong(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        sm.generate_api_key("service1")
        assert sm.verify_api_key("service1", "wrong_key") is False

    def test_verify_api_key_nonexistent(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        assert sm.verify_api_key("nonexistent", "key") is False

    def test_check_access_no_restrictions(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        assert sm.check_access("service", 123) is True

    def test_check_access_allowed(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        sm._allowed_users["service"] = [123, 456]
        assert sm.check_access("service", 123) is True

    def test_check_access_denied(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        sm._allowed_users["service"] = [123]
        assert sm.check_access("service", 999) is False

    def test_generate_webhook_secret(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm = SecurityManager(str(config_file))
        secret = sm.generate_webhook_secret()
        assert len(secret) == 64

    def test_persistence(self, tmp_path):
        config_file = tmp_path / "security.json"
        sm1 = SecurityManager(str(config_file))
        key = sm1.generate_api_key("service1")
        sm2 = SecurityManager(str(config_file))
        assert sm2.verify_api_key("service1", key) is True


class TestMetricsCollector:
    def test_init(self):
        mc = MetricsCollector()
        assert mc.get_counter("test") == 0
        assert mc.get_gauge("test") == 0.0

    def test_record(self):
        mc = MetricsCollector()
        mc.record("latency", 0.1)
        mc.record("latency", 0.2)
        assert len(mc._metrics["latency"]) == 2

    def test_record_trimming(self):
        mc = MetricsCollector()
        for i in range(10001):
            mc.record("metric", 1.0)
        assert len(mc._metrics["metric"]) == 5000

    def test_increment(self):
        mc = MetricsCollector()
        mc.increment("count")
        mc.increment("count", 5)
        assert mc.get_counter("count") == 6

    def test_set_gauge(self):
        mc = MetricsCollector()
        mc.set_gauge("cpu", 75.5)
        assert mc.get_gauge("cpu") == 75.5

    def test_observe_histogram(self):
        mc = MetricsCollector()
        mc.observe_histogram("latency", 0.1)
        mc.observe_histogram("latency", 0.2)
        mc.observe_histogram("latency", 0.3)
        stats = mc.get_histogram_stats("latency")
        assert stats["count"] == 3
        assert stats["min"] == 0.1
        assert stats["max"] == 0.3
        assert abs(stats["avg"] - 0.2) < 1e-9

    def test_histogram_empty(self):
        mc = MetricsCollector()
        stats = mc.get_histogram_stats("nonexistent")
        assert stats["count"] == 0

    def test_get_all(self):
        mc = MetricsCollector()
        mc.increment("counter1")
        mc.set_gauge("gauge1", 42.0)
        mc.observe_histogram("hist1", 1.0)
        result = mc.get_all()
        assert "counter1" in result["counters"]
        assert "gauge1" in result["gauges"]
        assert "hist1" in result["histograms"]

    def test_reset(self):
        mc = MetricsCollector()
        mc.increment("counter1")
        mc.set_gauge("gauge1", 42.0)
        mc.reset()
        assert mc.get_counter("counter1") == 0
        assert mc.get_gauge("gauge1") == 0.0

    def test_histogram_trimming(self):
        mc = MetricsCollector()
        for i in range(1001):
            mc.observe_histogram("latency", 1.0)
        assert len(mc._histograms["latency"]) == 500


class TestHealthChecker:
    def test_init(self):
        hc = HealthChecker()
        assert hc.get_status() == "unknown"

    def test_register_and_run(self):
        hc = HealthChecker()

        async def check_ok():
            return {"version": "1.0"}

        hc.register_check("version", check_ok)
        result = asyncio.run(hc.run_checks())
        assert result["version"]["status"] == "healthy"
        assert hc.get_status() == "healthy"

    def test_failing_check(self):
        hc = HealthChecker()

        async def check_fail():
            raise ValueError("check failed")

        hc.register_check("failing", check_fail)
        result = asyncio.run(hc.run_checks())
        assert result["failing"]["status"] == "unhealthy"
        assert hc.get_status() == "degraded"

    def test_get_report(self):
        hc = HealthChecker()

        async def check_ok():
            return {}

        hc.register_check("test", check_ok)
        asyncio.run(hc.run_checks())
        report = hc.get_report()
        assert report["overall"] == "healthy"
        assert report["total_checks"] == 1
        assert report["healthy"] == 1


class TestMessageQueue:
    def test_init(self):
        mq = MessageQueue()
        assert mq._running is False

    def test_enqueue_dequeue(self):
        mq = MessageQueue(max_size=10)
        asyncio.run(
            mq.enqueue(Message(
                priority=Priority.NORMAL,
                chat_id="chat1",
                text="hello",
                bot_id="bot1",
            ))
        )
        assert mq._queue.qsize() == 1

    def test_register_handler(self):
        mq = MessageQueue()
        async def handler(msg):
            pass
        mq.register_handler("bot1", handler)
        assert mq._handlers["bot1"] is handler

    def test_priority_ordering(self):
        mq = MessageQueue()
        asyncio.run(
            mq.enqueue(Message(Priority.LOW, "c", "low", "b"))
        )
        asyncio.run(
            mq.enqueue(Message(Priority.URGENT, "c", "urgent", "b"))
        )
        msg = mq._queue.get_nowait()
        assert msg.priority == Priority.URGENT


class TestPriority:
    def test_values(self):
        assert Priority.LOW.value == 0
        assert Priority.NORMAL.value == 1
        assert Priority.HIGH.value == 2
        assert Priority.URGENT.value == 3
