---
name: schedule
description: Schedule content for publishing across platforms
arguments: <title> <platforms> <datetime>
---

# /content-engine:schedule

Schedule content for publishing.

## Instructions

When this command is invoked with `$ARGUMENTS`:

1. Parse the title, platforms, and datetime from arguments
2. Create a content object with the provided details
3. Call `plugin.schedule_content()` to schedule it
4. Confirm with scheduling details

## Example Usage

```
/content-engine:schedule "Summer Sale" "telegram,instagram" "2025-06-01T10:00:00Z"
```

## Example Output

```
📅 Content Scheduled

Title: Summer Sale
Platforms: telegram, instagram
Scheduled for: June 1, 2025 at 10:00 AM UTC
Status: scheduled
```
