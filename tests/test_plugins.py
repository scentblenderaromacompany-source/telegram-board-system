"""
Comprehensive isolated tests for src/plugins/ module.
"""
import asyncio
from pathlib import Path

import pytest

from src.plugins.plugin_loader import PluginManager, Plugin
from src.plugins.jewelry_plugin import JewelryPlugin
from src.plugins.content_plugin import ContentPlugin
from src.plugins.miniapp_plugin import MiniAppPlugin


class TestPlugin:
    def test_init(self, tmp_path):
        p = Plugin("test", tmp_path)
        assert p.name == "test"
        assert p.path == tmp_path
        assert p.config == {}
        assert p.is_loaded is False

    def test_load_nonexistent_plugin_py(self, tmp_path):
        p = Plugin("test", tmp_path)
        p.load()
        assert p.is_loaded is True

    def test_get_attribute_no_module(self, tmp_path):
        p = Plugin("test", tmp_path)
        assert p.get_attribute("anything") is None
        assert p.get_attribute("anything", "default") == "default"

    def test_load_with_plugin_py(self, tmp_path):
        plugin_dir = tmp_path / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.py").write_text("VALUE = 42\n")
        p = Plugin("myplugin", plugin_dir)
        p.load()
        assert p.is_loaded is True
        assert p.get_attribute("VALUE") == 42


class TestPluginManager:
    def test_init(self):
        pm = PluginManager()
        assert pm.list_plugins() == []

    def test_load_plugin(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        plugin = pm.load_plugin(plugin_dir)
        assert plugin is not None
        assert plugin.name == "test_plugin"
        assert "test_plugin" in pm.list_plugins()

    def test_load_plugin_nonexistent(self, tmp_path):
        pm = PluginManager()
        plugin = pm.load_plugin(tmp_path / "nonexistent")
        assert plugin is None

    def test_load_plugin_already_loaded(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        p1 = pm.load_plugin(plugin_dir)
        p2 = pm.load_plugin(plugin_dir)
        assert p1 is p2

    def test_unload_plugin(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        pm.load_plugin(plugin_dir)
        assert pm.unload_plugin("test_plugin") is True
        assert pm.get_plugin("test_plugin") is None

    def test_unload_nonexistent(self):
        pm = PluginManager()
        assert pm.unload_plugin("nonexistent") is False

    def test_get_plugin(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        pm.load_plugin(plugin_dir)
        assert pm.get_plugin("test_plugin") is not None

    def test_get_plugin_nonexistent(self):
        pm = PluginManager()
        assert pm.get_plugin("nonexistent") is None

    def test_list_plugins(self, tmp_path):
        pm = PluginManager()
        for name in ["a", "b", "c"]:
            d = tmp_path / name
            d.mkdir()
            pm.load_plugin(d)
        assert sorted(pm.list_plugins()) == ["a", "b", "c"]

    def test_get_all_plugins(self, tmp_path):
        pm = PluginManager()
        for name in ["a", "b"]:
            d = tmp_path / name
            d.mkdir()
            pm.load_plugin(d)
        all_plugins = pm.get_all_plugins()
        assert len(all_plugins) == 2
        assert "a" in all_plugins
        assert "b" in all_plugins

    def test_reload_plugin(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        pm.load_plugin(plugin_dir)
        assert pm.reload_plugin("test_plugin") is True

    def test_reload_nonexistent(self):
        pm = PluginManager()
        assert pm.reload_plugin("nonexistent") is False

    def test_add_plugin_dir(self):
        pm = PluginManager()
        p = Path("/tmp/plugins")
        pm.add_plugin_dir(p)
        assert p in pm._plugin_dirs

    def test_load_plugin_with_config(self, tmp_path):
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        pm = PluginManager()
        plugin = pm.load_plugin(plugin_dir, {"key": "value"})
        assert plugin.config == {"key": "value"}


class TestJewelryPlugin:
    def test_init(self):
        p = JewelryPlugin()
        assert p.PLUGIN_NAME == "jewelry"
        assert p.is_initialized is False
        assert p._products == []

    def test_init_with_config(self):
        p = JewelryPlugin({"supabase_url": "https://example.com"})
        assert p._supabase_url == "https://example.com"

    def test_initialize_shutdown(self):
        p = JewelryPlugin()
        asyncio.run(p.initialize())
        assert p.is_initialized is True
        asyncio.run(p.shutdown())
        assert p.is_initialized is False

    def test_add_product(self):
        p = JewelryPlugin()
        product = {"id": "1", "name": "Ring", "price": 99.99}
        result = p.add_product(product)
        assert result == product
        assert len(p.get_catalog()) == 1

    def test_get_product(self):
        p = JewelryPlugin()
        p.add_product({"id": "1", "name": "Ring"})
        assert p.get_product("1") is not None
        assert p.get_product("nonexistent") is None

    def test_update_product(self):
        p = JewelryPlugin()
        p.add_product({"id": "1", "name": "Ring"})
        updated = p.update_product("1", {"price": 149.99})
        assert updated["price"] == 149.99

    def test_update_nonexistent(self):
        p = JewelryPlugin()
        assert p.update_product("nonexistent", {"price": 100}) is None

    def test_delete_product(self):
        p = JewelryPlugin()
        p.add_product({"id": "1", "name": "Ring"})
        assert p.delete_product("1") is True
        assert len(p.get_catalog()) == 0

    def test_delete_nonexistent(self):
        p = JewelryPlugin()
        assert p.delete_product("nonexistent") is False

    def test_search_products(self):
        p = JewelryPlugin()
        p.add_product({"id": "1", "name": "Gold Ring"})
        p.add_product({"id": "2", "name": "Silver Necklace"})
        p.add_product({"id": "3", "name": "Gold Bracelet"})
        results = p.search_products("gold")
        assert len(results) == 2

    def test_get_stats(self):
        p = JewelryPlugin()
        stats = p.get_stats()
        assert stats["name"] == "jewelry"
        assert stats["products"] == 0
        assert stats["initialized"] is False


class TestContentPlugin:
    def test_init(self):
        p = ContentPlugin()
        assert p.PLUGIN_NAME == "content"
        assert p.is_initialized is False

    def test_initialize_shutdown(self):
        p = ContentPlugin()
        asyncio.run(p.initialize())
        assert p.is_initialized is True
        asyncio.run(p.shutdown())
        assert p.is_initialized is False

    def test_add_template(self):
        p = ContentPlugin()
        template = {"body": "Hello {name}!"}
        result = p.add_template("greeting", template)
        assert result == template
        assert "greeting" in p.list_templates()

    def test_get_template(self):
        p = ContentPlugin()
        p.add_template("greeting", {"body": "Hi!"})
        assert p.get_template("greeting") is not None
        assert p.get_template("nonexistent") is None

    def test_delete_template(self):
        p = ContentPlugin()
        p.add_template("greeting", {"body": "Hi!"})
        assert p.delete_template("greeting") is True
        assert "greeting" not in p.list_templates()

    def test_delete_nonexistent_template(self):
        p = ContentPlugin()
        assert p.delete_template("nonexistent") is False

    def test_schedule_content(self):
        p = ContentPlugin()
        content = {"title": "Post 1", "body": "Hello!"}
        result = p.schedule_content(content)
        assert result["status"] == "scheduled"
        assert len(p.get_scheduled()) == 1

    def test_cancel_scheduled(self):
        p = ContentPlugin()
        p.schedule_content({"title": "Post 1"})
        assert p.cancel_scheduled(0) is True
        assert len(p.get_scheduled()) == 0

    def test_cancel_scheduled_out_of_range(self):
        p = ContentPlugin()
        assert p.cancel_scheduled(0) is False

    def test_get_stats(self):
        p = ContentPlugin()
        stats = p.get_stats()
        assert stats["name"] == "content"
        assert stats["templates"] == 0
        assert stats["scheduled"] == 0


class TestMiniAppPlugin:
    def test_init(self):
        p = MiniAppPlugin()
        assert p.PLUGIN_NAME == "miniapp"
        assert p.is_initialized is False

    def test_init_with_config(self):
        p = MiniAppPlugin({"app_url": "https://app.example.com"})
        assert p._app_url == "https://app.example.com"

    def test_initialize_shutdown(self):
        p = MiniAppPlugin()
        asyncio.run(p.initialize())
        assert p.is_initialized is True
        asyncio.run(p.shutdown())
        assert p.is_initialized is False

    def test_create_session(self):
        p = MiniAppPlugin()
        session = p.create_session(123, {"key": "value"})
        assert session["user_id"] == 123
        assert session["data"]["key"] == "value"
        assert session["active"] is True

    def test_get_session(self):
        p = MiniAppPlugin()
        p.create_session(123)
        assert p.get_session(123) is not None
        assert p.get_session(999) is None

    def test_close_session(self):
        p = MiniAppPlugin()
        p.create_session(123)
        assert p.close_session(123) is True
        assert p.get_session(123) is None

    def test_close_nonexistent_session(self):
        p = MiniAppPlugin()
        assert p.close_session(999) is False

    def test_get_app_url(self):
        p = MiniAppPlugin({"app_url": "https://app.example.com"})
        assert p.get_app_url() == "https://app.example.com"

    def test_get_web_app_data(self):
        p = MiniAppPlugin()
        p.create_session(123, {"item": "ring"})
        data = p.get_web_app_data(123)
        assert data["item"] == "ring"

    def test_get_web_app_data_nonexistent(self):
        p = MiniAppPlugin()
        assert p.get_web_app_data(999) is None

    def test_get_stats(self):
        p = MiniAppPlugin()
        stats = p.get_stats()
        assert stats["name"] == "miniapp"
        assert stats["active_sessions"] == 0
        assert stats["initialized"] is False
