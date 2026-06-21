"""
CLI interface for Telegram Board System v2.
"""
import asyncio
import argparse
import logging
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.integration import TelegramIntegration
from src.config import load_config
from src.logging_config import setup_logging
from src.health import HealthDashboard
from src.agents.agent_core import AgentRole
from src.masks.mask_templates import MaskTemplateLibrary
from src.channels.channel_registry import ChannelType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def cmd_init(args):
    """Initialize a new Telegram Board System project."""
    config_dir = Path(args.config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    for filename in ["channels.json", "masks.json", "memory.json", "webhooks.json"]:
        filepath = config_dir / filename
        if not filepath.exists():
            if filename == "channels.json":
                filepath.write_text(json.dumps({"channels": []}, indent=2))
            elif filename == "masks.json":
                filepath.write_text(json.dumps({"masks": []}, indent=2))
            elif filename == "memory.json":
                filepath.write_text(json.dumps({"entries": []}, indent=2))
            elif filename == "webhooks.json":
                filepath.write_text(json.dumps({}, indent=2))
    
    default_config = {
        "system": {"name": "Telegram Board System", "version": "2.0.0"},
        "businesses": {
            "openclaw": {"id": "openclaw", "name": "OpenClaw"},
            "hermes": {"id": "hermes", "name": "Hermes"},
            "caspers_heritage": {"id": "caspers_heritage", "name": "Caspers Heritage Jewelry"},
            "content_business": {"id": "content_business", "name": "Content Business"},
        },
        "defaults": {"rate_limit": 30, "max_message_length": 4096},
    }
    (config_dir / "default.json").write_text(json.dumps(default_config, indent=2))
    print(f"Initialized Telegram Board System in {config_dir}")

def cmd_status(args):
    """Show system status."""
    config = load_config(args.config_dir)
    integration = TelegramIntegration(args.config_dir)
    
    print("=== Telegram Board System Status ===")
    print(f"Config: {args.config_dir}")
    print(f"Businesses: {list(config.get('businesses', {}).keys())}")
    print(f"Channels: {len(integration.channel_registry._channels)}")
    print(f"Masks: {len(integration.mask_registry._masks)}")
    print(f"Agents: {len(integration.agent_manager.list_agents())}")

def cmd_run(args):
    """Run the Telegram Board System."""
    setup_logging(level=args.log_level, log_dir=args.log_dir)
    
    async def _run():
        integration = TelegramIntegration(args.config_dir)
        
        if args.token:
            business_id = args.business or "openclaw"
            adapter = integration.create_bot(
                bot_id=args.bot_id or "main-bot",
                token=args.token,
                business_id=business_id,
            )
        
        health = HealthDashboard()
        
        loop = asyncio.get_event_loop()
        import signal
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(integration.stop()))
        
        await integration.start()
        print("System started. Press Ctrl+C to stop.")
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await integration.stop()
    
    asyncio.run(_run())

def cmd_bot_setup(args):
    """Interactive bot setup wizard."""
    print("=== Telegram Bot Setup Wizard ===")
    print()
    
    token = input("Enter bot token (from @BotFather): ").strip()
    if not token:
        print("Error: Token required")
        return
    
    from src.telegram.managed_bot import is_valid_telegram_bot_token
    if not is_valid_telegram_bot_token(token):
        print("Error: Invalid token format")
        return
    
    bot_id = input(f"Bot ID [{token.split(':')[0]}]: ").strip() or token.split(':')[0]
    name = input("Bot name: ").strip() or "My Bot"
    business_id = input("Business ID [openclaw]: ").strip() or "openclaw"
    
    print()
    print("Available mask templates:")
    for i, template in enumerate(MaskTemplateLibrary.list_templates(), 1):
        print(f"  {i}. {template}")
    
    mask_choice = input("Select mask template (number): ").strip()
    templates = MaskTemplateLibrary.list_templates()
    if mask_choice.isdigit() and 1 <= int(mask_choice) <= len(templates):
        mask_template = templates[int(mask_choice) - 1]
    else:
        mask_template = "customer_support"
    
    print()
    print(f"Bot: {name} ({bot_id})")
    print(f"Business: {business_id}")
    print(f"Mask: {mask_template}")
    
    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("Cancelled")
        return
    
    config_dir = Path(args.config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    bots_file = config_dir / "bots.json"
    bots = json.loads(bots_file.read_text()) if bots_file.exists() else {"bots": []}
    bots["bots"].append({
        "bot_id": bot_id,
        "name": name,
        "business_id": business_id,
        "mask_template": mask_template,
        "token_env": f"TELEGRAM_BOT_TOKEN_{bot_id.upper()}",
    })
    bots_file.write_text(json.dumps(bots, indent=2))
    
    env_file = config_dir / ".env"
    env_lines = [f"TELEGRAM_BOT_TOKEN_{bot_id.upper()}={token}"]
    if env_file.exists():
        existing = env_file.read_text()
        if f"TELEGRAM_BOT_TOKEN_{bot_id.upper()}" not in existing:
            env_file.write_text(existing + "\n" + "\n".join(env_lines))
    else:
        env_file.write_text("\n".join(env_lines))
    
    print(f"\nBot configuration saved to {config_dir}")
    print(f"Token saved to {config_dir}/.env")
    print(f"Run with: python cli.py run --token {bot_id.upper()}")

def cmd_mask_list(args):
    """List available mask templates."""
    print("=== Mask Templates ===")
    for template in MaskTemplateLibrary.list_templates():
        t = MaskTemplateLibrary.get_template(template)
        print(f"  {template}: {t.get('bio', 'N/A')}")

def cmd_health(args):
    """Run health checks."""
    async def _health():
        integration = TelegramIntegration(args.config_dir)
        dashboard = HealthDashboard()
        results = await dashboard.run_checks(integration)
        print(json.dumps(results, indent=2))
    asyncio.run(_health())

def main():
    parser = argparse.ArgumentParser(description="Telegram Board System CLI", prog="telegram-board")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    init_p = subparsers.add_parser("init", help="Initialize project")
    init_p.add_argument("--config-dir", default="config")
    init_p.set_defaults(func=cmd_init)
    
    status_p = subparsers.add_parser("status", help="Show status")
    status_p.add_argument("--config-dir", default="config")
    status_p.set_defaults(func=cmd_status)
    
    run_p = subparsers.add_parser("run", help="Run system")
    run_p.add_argument("--config-dir", default="config")
    run_p.add_argument("--token", help="Bot token")
    run_p.add_argument("--bot-id", help="Bot ID")
    run_p.add_argument("--business", default="openclaw", help="Business ID")
    run_p.add_argument("--log-level", default="INFO")
    run_p.add_argument("--log-dir", default="logs")
    run_p.set_defaults(func=cmd_run)
    
    setup_p = subparsers.add_parser("bot-setup", help="Interactive bot setup")
    setup_p.add_argument("--config-dir", default="config")
    setup_p.set_defaults(func=cmd_bot_setup)
    
    mask_p = subparsers.add_parser("masks", help="List mask templates")
    mask_p.set_defaults(func=cmd_mask_list)
    
    health_p = subparsers.add_parser("health", help="Run health checks")
    health_p.add_argument("--config-dir", default="config")
    health_p.set_defaults(func=cmd_health)
    
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
