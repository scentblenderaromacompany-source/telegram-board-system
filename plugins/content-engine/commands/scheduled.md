---
name: scheduled
description: List all scheduled content
---

# /content-engine:scheduled

View all scheduled content.

## Instructions

When this command is invoked:

1. Call `plugin.get_scheduled()` to get all scheduled items
2. Display each item with its title, platforms, and scheduled time
3. Show total count

## Example Output

```
📅 Scheduled Content (3 items)

1. Summer Sale - telegram, instagram - June 1, 2025 10:00 AM
2. Product Launch - telegram - June 5, 2025 2:00 PM
3. Weekly Newsletter - web - Every Monday 9:00 AM
```
