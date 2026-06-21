# Telegram Board System v2

Multi-bot, multi-channel Telegram management system with mask support, agent framework, and plugin architecture.

## Architecture

```
telegram-board-system/
├── src/
│   ├── agents/           # Agent framework (TRAPAGENT/Eve inspired)
│   │   ├── agent_core.py      # Agent with tools, skills, memory
│   │   ├── agent_manager.py   # Multi-agent orchestration
│   │   └── memory.py          # Long-term memory store
│   ├── bots/             # Telegram bot framework
│   │   ├── bot_core.py        # Production bot with middleware
│   │   ├── bot_manager.py     # Multi-bot lifecycle
│   │   ├── middleware.py       # Rate limit, auth, logging, retry
│   │   └── handlers.py        # Pattern matching, conversations
│   ├── channels/         # Multi-platform channel management
│   │   ├── channel_registry.py    # Channel CRUD
│   │   ├── channel_manager.py     # Channel operations
│   │   ├── message_router.py      # Priority routing
│   │   ├── webhook_manager.py     # Webhook management
│   │   └── channel_adapters.py    # Telegram, Slack, Web adapters
│   ├── masks/            # Bot identity/mask system
│   │   ├── mask_registry.py       # Mask CRUD
│   │   ├── persona_engine.py      # Context-aware personas
│   │   ├── mask_manager.py        # Mask assignment
│   │   └── mask_templates.py      # Pre-built templates
│   ├── plugins/          # Extensible plugin system
│   │   ├── plugin_loader.py       # Plugin lifecycle
│   │   ├── jewelry_plugin.py      # Caspers Heritage tools
│   │   ├── content_plugin.py      # Content creation tools
│   │   └── miniapp_plugin.py      # Telegram Mini App
│   ├── utils/            # Shared utilities
│   │   ├── rate_limiter.py        # API compliance
│   │   ├── message_queue.py       # Async queue
│   │   ├── metrics.py             # Metrics + health checks
│   │   └── security.py            # Credentials + access
│   └── main.py           # System entry point
├── config/               # Configuration files
│   ├── default.json      # System config
│   ├── channels.json     # Channel definitions
│   ├── masks.json        # Mask definitions
│   └── bots.json         # Bot definitions
├── tests/                # Test suite
├── plugins/              # External plugins
├── cli.py                # CLI interface
└── README.md
```

## Features

### Agent Framework (TRAPAGENT-inspired)
- Multi-role agents (Executive, Jewelry, Content, Research, Support)
- Tool registration and invocation
- Skill-based capabilities
- Long-term memory with categories
- Inter-agent delegation

### Bot System
- Middleware pipeline (rate limit, auth, logging, retry, mask)
- Pattern matching handlers
- Conversation state machines
- Inline keyboard support
- Webhook + polling modes
- Media handling (photo, video, document, audio)

### Channel Management
- Multi-business channel registry
- Channel types: Broadcast, Support, Internal, Monitoring
- Priority-based message routing
- Webhook management
- Multi-platform adapters (Telegram, Slack, Web)

### Mask System
- Bot identity profiles (name, avatar, bio)
- Context-aware persona engine
- Sentiment detection
- Pre-built templates (Jewelry Expert, Support, Sales, etc.)
- A/B testing support

### Plugin Architecture
- Plugin loader with lifecycle hooks
- Jewelry plugin (Supabase inventory, eBay, Shopify)
- Content plugin (idea generation, scheduling)
- Mini App plugin (push notifications, subscribers)

### Security
- API key management
- Webhook secret verification
- Access control lists
- Environment variable management

## Quick Start

```bash
# Initialize
python cli.py init --config-dir config

# Check status
python cli.py status

# Create channel
python cli.py channel create openclaw-support "OpenClaw Support" --business openclaw --type support

# Create mask
python cli.py mask create exec-mask "Executive" --type custom --business openclaw

# List plugins
python cli.py plugin list

# Run system
python cli.py run
```

## Configuration

### Businesses
- **openclaw**: OpenClaw AI Agent System
- **hermes**: Hermes Agent System
- **caspers_heritage**: Caspers Heritage Jewelry
- **content_business**: Automated content creation

### Agents
- **executive**: Executive AI Chief of Staff
- **jewelry**: Jewelry operations specialist
- **content**: Content creation engine
- **research**: Research and analysis
- **support**: Customer support

### Mask Templates
- customer_support, sales_rep, jewelry_expert, content_creator, tech_support, monitor_bot

## Integration with Existing Systems

### Hermes Agent
- Uses Hermes Telegram adapter for bot communication
- Integrates with Hermes plugin system
- Shares memory via PLMA architecture

### OpenClaw/Trapclaw
- Extends Trapclaw executive operating system
- Adds Telegram channel management
- Multi-bot support for different business functions

### Caspers Heritage Jewelry
- Mini App integration for customer storefront
- Inventory sync with eBay/Shopify
- Push notifications for new arrivals
- Customer inquiry management

## Development

```bash
# Run tests
pytest tests/

# Type check
mypy src/

# Lint
ruff check src/
```
