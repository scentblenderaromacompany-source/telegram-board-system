# Caspers Telegram Mini App Plugin

Telegram Mini App integration for Caspers Heritage.

## Features

- Web-app hosting configuration
- User session lifecycle management
- Payment processing hooks
- Deep-link handling

## Installation

```bash
/plugin install caspers-telegram-miniapp
```

## Commands

| Command | Description |
|---------|-------------|
| `/caspers-telegram-miniapp:miniapp` | Open the Mini App |
| `/caspers-telegram-miniapp:sessions` | List active sessions |

## Skills

- **session-management** - Manage user sessions
- **payment-processing** - Handle payments

## Configuration

```json
{
  "app_url": "https://t.me/caspersheritagebot/app",
  "payment_provider_token": "YOUR_PAYMENT_TOKEN"
}
```

## License

MIT
