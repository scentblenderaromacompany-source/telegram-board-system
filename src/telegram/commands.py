"""
Telegram bot command registry.
Based on Hermes hermes_cli/commands.py pattern.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

@dataclass
class TelegramCommand:
    name: str
    description: str
    category: str = "General"
    aliases: tuple = ()
    args_hint: str = ""
    handler: Optional[Callable] = None

class TelegramCommandRegistry:
    """
    Central registry for Telegram bot commands.
    Generates BotCommand menus and handles dispatch.
    """
    
    def __init__(self):
        self._commands: List[TelegramCommand] = []
        self._handlers: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
    
    def register(self, command: TelegramCommand):
        self._commands.append(command)
        if command.handler:
            self._handlers[command.name] = command.handler
        for alias in command.aliases:
            self._aliases[alias] = command.name
    
    def resolve(self, name: str) -> Optional[str]:
        if name in self._handlers:
            return name
        alias_target = self._aliases.get(name)
        if alias_target and alias_target in self._handlers:
            return alias_target
        for cmd in self._commands:
            if cmd.name == name:
                return cmd.name
        return alias_target
    
    def get_handler(self, name: str) -> Optional[Callable]:
        resolved = self.resolve(name)
        return self._handlers.get(resolved) if resolved else None
    
    def get_bot_commands(self, max_commands: int = 100) -> List[Dict[str, str]]:
        commands = []
        for cmd in self._commands[:max_commands]:
            commands.append({"command": cmd.name, "description": cmd.description})
        return commands
    
    def get_help_text(self, category: str = None) -> str:
        lines = ["<b>Available Commands:</b>", ""]
        commands = self._commands
        if category:
            commands = [c for c in commands if c.category == category]
        
        current_cat = None
        for cmd in commands:
            if cmd.category != current_cat:
                current_cat = cmd.category
                lines.append(f"<b>{current_cat}:</b>")
            args = f" {cmd.args_hint}" if cmd.args_hint else ""
            lines.append(f"/{cmd.name}{args} — {cmd.description}")
            if cmd.aliases:
                lines.append(f"  Aliases: {', '.join('/' + a for a in cmd.aliases)}")
        
        return "\n".join(lines)
    
    def list_commands(self) -> List[TelegramCommand]:
        return list(self._commands)
    
    def register_default_commands(self):
        self.register(TelegramCommand("start", "Start the bot", "General"))
        self.register(TelegramCommand("help", "Show help", "General"))
        self.register(TelegramCommand("status", "Show bot status", "Info"))
        self.register(TelegramCommand("ping", "Check connectivity", "Info"))
        self.register(TelegramCommand("mask", "Switch bot mask", "Configuration", aliases=("m",)))
        self.register(TelegramCommand("channel", "Channel management", "Management", aliases=("ch",)))
        self.register(TelegramCommand("agent", "Agent operations", "Management", aliases=("a",)))
