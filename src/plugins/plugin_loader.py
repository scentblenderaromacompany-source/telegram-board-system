"""
Plugin loader and manager for Telegram Board System.

Supports both:
- Internal Python plugins (src/plugins/*.py)
- External plugins following Claude Code / Open Plugin spec (plugins/*/)

External plugin structure:
    plugin-name/
    ├── .claude-plugin/
    │   └── plugin.json      # Manifest
    ├── skills/
    │   └── skill-name/
    │       └── SKILL.md
    ├── commands/
    │   └── command-name.md
    ├── hooks/
    │   └── hooks.json
    ├── .mcp.json
    ├── plugin.py             # Python implementation (optional)
    └── README.md
"""
import importlib
import importlib.util
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import PluginInterface

logger = logging.getLogger(__name__)


class Plugin:
    """
    Represents a loaded external plugin directory.

    Supports both legacy plugin.py and new .claude-plugin/plugin.json manifests.
    """

    def __init__(self, name: str, path: Path, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.path = path
        self.config = config or {}
        self._loaded = False
        self._module = None
        self._manifest: Optional[Dict[str, Any]] = None
        self._skills: List[str] = []
        self._commands: List[str] = []

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def manifest(self) -> Optional[Dict[str, Any]]:
        return self._manifest

    @property
    def skills(self) -> List[str]:
        return list(self._skills)

    @property
    def commands(self) -> List[str]:
        return list(self._commands)

    def load(self) -> None:
        """
        Load the plugin.

        Tries in order:
        1. .claude-plugin/plugin.json manifest (new spec)
        2. .plugin/plugin.json manifest (vendor-neutral spec)
        3. plugin.py module (legacy)
        """
        # Try .claude-plugin/plugin.json first
        manifest_path = self.path / ".claude-plugin" / "plugin.json"
        if manifest_path.exists():
            self._load_manifest(manifest_path)
            self._discover_components()
            self._loaded = True
            logger.info("Loaded plugin (manifest): %s", self.name)
            return

        # Try .plugin/plugin.json (vendor-neutral)
        manifest_path = self.path / ".plugin" / "plugin.json"
        if manifest_path.exists():
            self._load_manifest(manifest_path)
            self._discover_components()
            self._loaded = True
            logger.info("Loaded plugin (manifest): %s", self.name)
            return

        # Fallback to plugin.py (legacy)
        plugin_file = self.path / "plugin.py"
        if plugin_file.exists():
            self._load_module(plugin_file)
            self._loaded = True
            logger.info("Loaded plugin (module): %s", self.name)
            return

        logger.warning("Plugin %s has no manifest or plugin.py – treating as config-only", self.name)
        self._loaded = True

    def _load_manifest(self, manifest_path: Path) -> None:
        """Load and parse the plugin manifest."""
        try:
            with open(manifest_path) as f:
                self._manifest = json.load(f)
            # Use manifest name if available
            if self._manifest.get("name"):
                self.name = self._manifest["name"]
        except Exception as exc:
            logger.error("Failed to parse manifest for %s: %s", self.name, exc)
            raise

    def _discover_components(self) -> None:
        """Discover skills and commands from the plugin directory."""
        # Discover skills
        skills_dir = self.path / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    self._skills.append(skill_dir.name)

        # Discover commands
        commands_dir = self.path / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                self._commands.append(cmd_file.stem)

    def _load_module(self, plugin_file: Path) -> None:
        """Load the plugin.py module (legacy)."""
        try:
            spec = importlib.util.spec_from_file_location(self.name, str(plugin_file))
            if spec and spec.loader:
                self._module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self._module)
        except Exception as exc:
            logger.error("Failed to load module for %s: %s", self.name, exc)
            raise

    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get an attribute from the loaded module."""
        if self._module:
            return getattr(self._module, name, default)
        return default

    def get_skill_content(self, skill_name: str) -> Optional[str]:
        """Read the SKILL.md content for a skill."""
        skill_path = self.path / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text()
        return None

    def get_command_content(self, command_name: str) -> Optional[str]:
        """Read the .md content for a command."""
        cmd_path = self.path / "commands" / f"{command_name}.md"
        if cmd_path.exists():
            return cmd_path.read_text()
        return None


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.

    Supports both internal Python plugins and external spec-compliant plugins.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_dirs: List[Path] = []

    # ------------------------------------------------------------------
    # Directory management
    # ------------------------------------------------------------------

    def add_plugin_dir(self, path: Path) -> None:
        """Add a directory to search for plugins."""
        self._plugin_dirs.append(path)

    # ------------------------------------------------------------------
    # Plugin operations
    # ------------------------------------------------------------------

    def load_plugin(self, path: Path, config: Optional[Dict[str, Any]] = None) -> Optional[Plugin]:
        """Load a plugin from a directory."""
        if not path.exists():
            logger.warning("Plugin path does not exist: %s", path)
            return None

        name = path.name
        if name in self._plugins:
            logger.info("Plugin %s already loaded", name)
            return self._plugins[name]

        plugin = Plugin(name, path, config)
        try:
            plugin.load()
            self._plugins[name] = plugin
            return plugin
        except Exception as exc:
            logger.error("Failed to load plugin %s: %s", name, exc)
            return None

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin by name."""
        if name in self._plugins:
            del self._plugins[name]
            logger.info("Unloaded plugin: %s", name)
            return True
        return False

    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin by name."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin._loaded = False
            plugin.load()
            return True
        return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """List all loaded plugin names."""
        return list(self._plugins.keys())

    def get_all_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins as ``{name: Plugin}``."""
        return dict(self._plugins)

    def get_all_skills(self) -> Dict[str, str]:
        """Get all skills across all plugins as ``{plugin:skill_name: skill_content}``."""
        skills = {}
        for plugin in self._plugins.values():
            for skill_name in plugin.skills:
                content = plugin.get_skill_content(skill_name)
                if content:
                    skills[f"{plugin.name}:{skill_name}"] = content
        return skills

    def get_all_commands(self) -> Dict[str, str]:
        """Get all commands across all plugins as ``{plugin:command_name: command_content}``."""
        commands = {}
        for plugin in self._plugins.values():
            for cmd_name in plugin.commands:
                content = plugin.get_command_content(cmd_name)
                if content:
                    commands[f"{plugin.name}:{cmd_name}"] = content
        return commands
