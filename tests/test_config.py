"""
Comprehensive isolated tests for src/config.py.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from src.config import Config, load_config, get_env, require_env


class TestConfigInit:
    def test_default_config_dir(self):
        c = Config()
        assert c._config_dir == Path("config")

    def test_custom_config_dir(self):
        c = Config("/tmp/test_config")
        assert c._config_dir == Path("/tmp/test_config")

    def test_empty_data_on_init(self):
        c = Config()
        assert c._data == {}
        assert c._loaded is False


class TestConfigLoad:
    def test_load_existing_file(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"key": "value", "nested": {"a": 1}}))
        c = Config(str(tmp_path))
        result = c.load("test.json")
        assert result is c
        assert c._loaded is True
        assert c.get("key") == "value"
        assert c.get("nested.a") == 1

    def test_load_missing_file(self, tmp_path):
        c = Config(str(tmp_path))
        result = c.load("nonexistent.json")
        assert result is c
        assert c._loaded is True
        assert c._data == {}

    def test_load_empty_json(self, tmp_path):
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")
        c = Config(str(tmp_path))
        c.load("empty.json")
        assert c._data == {}

    def test_load_nested_json(self, tmp_path):
        data = {
            "system": {"name": "test", "version": "1.0"},
            "database": {"host": "localhost", "port": 5432},
        }
        config_file = tmp_path / "nested.json"
        config_file.write_text(json.dumps(data))
        c = Config(str(tmp_path))
        c.load("nested.json")
        assert c.get("system.name") == "test"
        assert c.get("database.port") == 5432


class TestEnvOverrides:
    def test_env_override_simple(self, tmp_path, monkeypatch):
        config_file = tmp_path / "default.json"
        config_file.write_text(json.dumps({"name": "original"}))
        monkeypatch.setenv("TBS_NAME", "overridden")
        c = Config(str(tmp_path))
        c.load("default.json")
        assert c.get("name") == "overridden"

    def test_env_override_nested(self, tmp_path, monkeypatch):
        config_file = tmp_path / "default.json"
        config_file.write_text(json.dumps({"db": {"host": "localhost"}}))
        monkeypatch.setenv("TBS_DB__HOST", "remotehost")
        c = Config(str(tmp_path))
        c.load("default.json")
        assert c.get("db.host") == "remotehost"

    def test_env_override_creates_new_key(self, tmp_path, monkeypatch):
        config_file = tmp_path / "default.json"
        config_file.write_text(json.dumps({}))
        monkeypatch.setenv("TBS_NEW_KEY", "new_value")
        c = Config(str(tmp_path))
        c.load("default.json")
        assert c.get("new_key") == "new_value"

    def test_no_env_override(self, tmp_path):
        config_file = tmp_path / "default.json"
        config_file.write_text(json.dumps({"name": "original"}))
        c = Config(str(tmp_path))
        c.load("default.json")
        assert c.get("name") == "original"


class TestConfigGetSet:
    def test_get_existing_key(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"a": {"b": {"c": 42}}}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert c.get("a.b.c") == 42

    def test_get_missing_key_returns_default(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"a": 1}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert c.get("nonexistent") is None
        assert c.get("nonexistent", "fallback") == "fallback"

    def test_get_nested_missing_returns_default(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"a": 1}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert c.get("a.b.c", "fallback") == "fallback"

    def test_set_new_key(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({}))
        c = Config(str(tmp_path))
        c.load("test.json")
        c.set("new.key", "value")
        assert c.get("new.key") == "value"

    def test_set_overwrite(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"key": "old"}))
        c = Config(str(tmp_path))
        c.load("test.json")
        c.set("key", "new")
        assert c.get("key") == "new"

    def test_set_nested_creates_path(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({}))
        c = Config(str(tmp_path))
        c.load("test.json")
        c.set("a.b.c.d", 100)
        assert c.get("a.b.c.d") == 100


class TestConfigMagicMethods:
    def test_getitem_existing(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"key": "value"}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert c["key"] == "value"

    def test_getitem_missing_raises(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({}))
        c = Config(str(tmp_path))
        c.load("test.json")
        with pytest.raises(KeyError):
            c["nonexistent"]

    def test_contains_existing(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"key": "value"}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert "key" in c

    def test_contains_missing(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({}))
        c = Config(str(tmp_path))
        c.load("test.json")
        assert "nonexistent" not in c


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        config_file = tmp_path / "output.json"
        c = Config(str(tmp_path))
        c.set("key", "value")
        c.save("output.json")
        assert config_file.exists()
        loaded = json.loads(config_file.read_text())
        assert loaded["key"] == "value"

    def test_save_preserves_structure(self, tmp_path):
        config_file = tmp_path / "output.json"
        c = Config(str(tmp_path))
        c.set("a.b", 1)
        c.set("a.c", 2)
        c.save("output.json")
        loaded = json.loads(config_file.read_text())
        assert loaded["a"]["b"] == 1
        assert loaded["a"]["c"] == 2

    def test_save_overwrites(self, tmp_path):
        config_file = tmp_path / "output.json"
        c = Config(str(tmp_path))
        c.set("key", "old")
        c.save("output.json")
        c.set("key", "new")
        c.save("output.json")
        loaded = json.loads(config_file.read_text())
        assert loaded["key"] == "new"

    def test_to_dict(self, tmp_path):
        config_file = tmp_path / "test.json"
        config_file.write_text(json.dumps({"a": 1, "b": 2}))
        c = Config(str(tmp_path))
        c.load("test.json")
        d = c.to_dict()
        assert d == {"a": 1, "b": 2}


class TestLoadConfig:
    def test_load_config_helper(self, tmp_path):
        config_file = tmp_path / "default.json"
        config_file.write_text(json.dumps({"helper": True}))
        c = load_config(str(tmp_path))
        assert c.get("helper") is True


class TestGetEnv:
    def test_get_env_existing(self, monkeypatch):
        monkeypatch.setenv("TEST_ENV_VAR", "test_value")
        assert get_env("TEST_ENV_VAR") == "test_value"

    def test_get_env_missing(self):
        assert get_env("NONEXISTENT_ENV_VAR_12345") is None

    def test_get_env_default(self):
        assert get_env("NONEXISTENT_ENV_VAR_12345", "default") == "default"


class TestRequireEnv:
    def test_require_env_existing(self, monkeypatch):
        monkeypatch.setenv("TEST_REQUIRED_VAR", "value")
        assert require_env("TEST_REQUIRED_VAR") == "value"

    def test_require_env_missing_raises(self):
        with pytest.raises(EnvironmentError):
            require_env("NONEXISTENT_REQUIRED_12345")
