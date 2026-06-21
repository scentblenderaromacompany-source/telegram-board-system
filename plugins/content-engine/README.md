# Content Engine Plugin

Content creation, scheduling, and multi-platform publishing engine.

## Features

- Content scheduling with priority queues
- Template management (CRUD)
- Multi-platform publishing (Telegram, Slack, Web)
- Analytics tracking

## Installation

```bash
/plugin install content-engine
```

## Commands

| Command | Description |
|---------|-------------|
| `/content-engine:schedule` | Schedule content for publishing |
| `/content-engine:scheduled` | View all scheduled content |

## Skills

- **content-scheduling** - Schedule and manage content publishing
- **template-management** - Create and manage reusable templates

## Template Example

```python
plugin.add_template("product-announce", {
    "title": "New Product: {{name}}",
    "body": "Introducing {{name}} - {{description}}. Price: ${{price}}",
    "variables": ["name", "description", "price"]
})
```

## License

MIT
