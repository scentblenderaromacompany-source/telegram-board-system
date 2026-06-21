---
name: content-scheduling
description: Schedule and manage content publishing. Use when creating, scheduling, or canceling content across platforms.
---

# Content Scheduling Skill

Schedule and manage content publishing across platforms.

## Capabilities

- Schedule content for future publishing
- Cancel scheduled content
- View upcoming scheduled content
- Track published content history
- Manage content templates

## Usage

When the user asks to schedule content:

```python
plugin.schedule_content({
    "title": "Summer Collection Launch",
    "body": "Discover our new summer jewelry collection...",
    "platforms": ["telegram", "instagram"],
    "scheduled_for": "2025-06-01T10:00:00Z"
})
plugin.get_scheduled()
plugin.cancel_scheduled(0)
```

## Content Status Flow

```
draft → scheduled → published
           ↓
        cancelled
```
