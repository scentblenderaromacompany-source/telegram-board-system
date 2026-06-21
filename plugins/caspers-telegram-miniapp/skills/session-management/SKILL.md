---
name: session-management
description: Manage Telegram Mini App user sessions. Use when creating, viewing, or closing user sessions.
---

# Session Management Skill

Handle user sessions for the Caspers Heritage Telegram Mini App.

## Capabilities

- Create new user sessions
- View active sessions
- Get session data
- Close sessions
- Track session activity

## Usage

When the user asks about mini app sessions:

```python
plugin.create_session(user_id=12345, data={"cart": []})
plugin.get_session(12345)
plugin.get_web_app_data(12345)
plugin.close_session(12345)
```

## Session Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | int | Yes | Telegram user ID |
| data | dict | No | Session data (cart, preferences) |
| active | bool | Yes | Session status |
| created_at | string | No | ISO timestamp |
