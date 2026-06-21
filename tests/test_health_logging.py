"""
Comprehensive isolated tests for src/health.py and src/logging_config.py.
"""
import asyncio
import logging

import pytest

from src.health import HealthDashboard, HealthCheck


class TestHealthCheck:
    def test_creation(self):
        hc = HealthCheck(name="test")
        assert hc.name == "test"
        assert hc.status == "unknown"
        assert hc.message == ""
        assert hc.latency_ms == 0


class TestHealthDashboard:
    def test_init(self):
        hd = HealthDashboard()
        assert hd._checks == {}
        assert hd._start_time > 0

    def test_register_check(self):
        hd = HealthDashboard()

        async def check():
            return {"ok": True}

        hd.register_check("test", check)
        assert "test" in hd._checks

    def test_run_checks_empty(self):
        hd = HealthDashboard()
        result = asyncio.run(hd.run_checks())
        assert "system" in result
        assert result["system"]["status"] == "healthy"
        assert "overall" in result

    def test_run_checks_with_custom(self):
        hd = HealthDashboard()

        async def check():
            return {"version": "1.0"}

        hd.register_check("version", check)
        result = asyncio.run(hd.run_checks())
        assert result["version"]["status"] == "healthy"
        assert result["version"]["latency_ms"] >= 0

    def test_run_checks_failing(self):
        hd = HealthDashboard()

        async def check():
            raise RuntimeError("broken")

        hd.register_check("broken", check)
        result = asyncio.run(hd.run_checks())
        assert result["broken"]["status"] == "unhealthy"
        assert "broken" in result["broken"]["error"]

    def test_get_status_summary(self):
        hd = HealthDashboard()

        async def check():
            return {}

        hd.register_check("test", check)
        asyncio.run(hd.run_checks())
        summary = hd.get_status_summary()
        assert "test" in summary
        assert "healthy" in summary.lower() or "✅" in summary


class TestLoggingConfig:
    def test_setup_logging(self):
        from src.logging_config import setup_logging
        logger = setup_logging(level="DEBUG", log_dir="/tmp/tbs_test_logs")
        assert logger is not None
        assert logger.level == logging.DEBUG

    def test_json_formatter(self):
        from src.logging_config import JSONFormatter
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert "test message" in output
        assert "INFO" in output

    def test_human_readable_formatter(self):
        from src.logging_config import HumanReadableFormatter
        formatter = HumanReadableFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert "test message" in output
        assert "INFO" in output

    def test_json_formatter_with_exception(self):
        from src.logging_config import JSONFormatter
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=1, msg="error occurred", args=(), exc_info=exc_info,
        )
        output = formatter.format(record)
        assert "error occurred" in output
        assert "ValueError" in output
