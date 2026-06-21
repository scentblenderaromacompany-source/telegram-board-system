"""
Comprehensive isolated tests for src/telegram/commands.py.
"""
import pytest

from src.telegram.commands import TelegramCommandRegistry, TelegramCommand


class TestTelegramCommand:
    def test_command_creation(self):
        cmd = TelegramCommand(
            name="start",
            description="Start the bot",
            category="General",
        )
        assert cmd.name == "start"
        assert cmd.description == "Start the bot"
        assert cmd.category == "General"
        assert cmd.aliases == ()
        assert cmd.args_hint == ""
        assert cmd.handler is None

    def test_command_with_aliases(self):
        cmd = TelegramCommand(
            name="mask",
            description="Switch mask",
            aliases=("m", "masks"),
        )
        assert "m" in cmd.aliases
        assert "masks" in cmd.aliases

    def test_command_with_handler(self):
        async def my_handler():
            pass
        cmd = TelegramCommand(name="test", description="test", handler=my_handler)
        assert cmd.handler is my_handler


class TestCommandRegistry:
    def test_empty_registry(self):
        reg = TelegramCommandRegistry()
        assert reg.list_commands() == []

    def test_register_command(self):
        reg = TelegramCommandRegistry()
        cmd = TelegramCommand(name="start", description="Start")
        reg.register(cmd)
        assert len(reg.list_commands()) == 1
        assert reg.list_commands()[0].name == "start"

    def test_register_multiple(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="start", description="Start"))
        reg.register(TelegramCommand(name="help", description="Help"))
        assert len(reg.list_commands()) == 2

    def test_register_with_handler(self):
        reg = TelegramCommandRegistry()
        async def handler():
            pass
        cmd = TelegramCommand(name="test", description="test", handler=handler)
        reg.register(cmd)
        assert reg.get_handler("test") is handler

    def test_register_with_aliases(self):
        reg = TelegramCommandRegistry()
        cmd = TelegramCommand(name="mask", description="mask", aliases=("m",))
        reg.register(cmd)
        assert reg.get_handler("m") is None
        assert reg.resolve("m") == "mask"


class TestResolve:
    def test_resolve_direct_handler(self):
        reg = TelegramCommandRegistry()
        async def handler():
            pass
        cmd = TelegramCommand(name="start", description="Start", handler=handler)
        reg.register(cmd)
        assert reg.resolve("start") == "start"

    def test_resolve_alias(self):
        reg = TelegramCommandRegistry()
        cmd = TelegramCommand(name="mask", description="mask", aliases=("m",))
        reg.register(cmd)
        assert reg.resolve("m") == "mask"

    def test_resolve_unregistered(self):
        reg = TelegramCommandRegistry()
        assert reg.resolve("nonexistent") is None

    def test_resolve_no_handler(self):
        reg = TelegramCommandRegistry()
        cmd = TelegramCommand(name="start", description="Start")
        reg.register(cmd)
        assert reg.resolve("start") == "start"


class TestGetHandler:
    def test_get_handler_registered(self):
        reg = TelegramCommandRegistry()
        async def handler():
            pass
        cmd = TelegramCommand(name="test", description="test", handler=handler)
        reg.register(cmd)
        assert reg.get_handler("test") is handler

    def test_get_handler_alias(self):
        reg = TelegramCommandRegistry()
        async def handler():
            pass
        cmd = TelegramCommand(name="mask", description="mask", aliases=("m",), handler=handler)
        reg.register(cmd)
        assert reg.get_handler("m") is handler

    def test_get_handler_not_registered(self):
        reg = TelegramCommandRegistry()
        assert reg.get_handler("nonexistent") is None

    def test_get_handler_no_handler_set(self):
        reg = TelegramCommandRegistry()
        cmd = TelegramCommand(name="test", description="test")
        reg.register(cmd)
        assert reg.get_handler("test") is None


class TestGetBotCommands:
    def test_empty(self):
        reg = TelegramCommandRegistry()
        assert reg.get_bot_commands() == []

    def test_commands_format(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="start", description="Start"))
        reg.register(TelegramCommand(name="help", description="Help"))
        cmds = reg.get_bot_commands()
        assert len(cmds) == 2
        assert all("command" in c and "description" in c for c in cmds)

    def test_max_commands(self):
        reg = TelegramCommandRegistry()
        for i in range(20):
            reg.register(TelegramCommand(name=f"cmd{i}", description=f"Command {i}"))
        cmds = reg.get_bot_commands(max_commands=5)
        assert len(cmds) == 5


class TestGetHelpText:
    def test_empty_help(self):
        reg = TelegramCommandRegistry()
        help_text = reg.get_help_text()
        assert "Commands" in help_text

    def test_help_with_commands(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="start", description="Start", category="General"))
        reg.register(TelegramCommand(name="help", description="Help", category="General"))
        help_text = reg.get_help_text()
        assert "start" in help_text
        assert "help" in help_text

    def test_help_filtered_by_category(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="start", description="Start", category="General"))
        reg.register(TelegramCommand(name="ban", description="Ban user", category="Admin"))
        help_text = reg.get_help_text(category="Admin")
        assert "ban" in help_text
        assert "start" not in help_text

    def test_help_with_aliases(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="mask", description="Switch mask", aliases=("m",)))
        help_text = reg.get_help_text()
        assert "/m" in help_text

    def test_help_with_args_hint(self):
        reg = TelegramCommandRegistry()
        reg.register(TelegramCommand(name="ban", description="Ban user", args_hint="<user_id>"))
        help_text = reg.get_help_text()
        assert "<user_id>" in help_text


class TestDefaultCommands:
    def test_register_defaults(self):
        reg = TelegramCommandRegistry()
        reg.register_default_commands()
        assert len(reg.list_commands()) >= 5

    def test_default_command_names(self):
        reg = TelegramCommandRegistry()
        reg.register_default_commands()
        names = [c.name for c in reg.list_commands()]
        assert "start" in names
        assert "help" in names
        assert "status" in names
        assert "ping" in names
        assert "mask" in names
        assert "channel" in names
        assert "agent" in names

    def test_default_commands_have_categories(self):
        reg = TelegramCommandRegistry()
        reg.register_default_commands()
        for cmd in reg.list_commands():
            assert cmd.category != ""

    def test_default_commands_have_aliases(self):
        reg = TelegramCommandRegistry()
        reg.register_default_commands()
        mask_cmd = [c for c in reg.list_commands() if c.name == "mask"][0]
        assert "m" in mask_cmd.aliases

    def test_default_commands_resolve(self):
        reg = TelegramCommandRegistry()
        reg.register_default_commands()
        assert reg.resolve("start") == "start"
        assert reg.resolve("m") == "mask"
        assert reg.resolve("ch") == "channel"
        assert reg.resolve("a") == "agent"
