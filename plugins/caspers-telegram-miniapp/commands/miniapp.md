---
name: miniapp
description: Open the Caspers Heritage Telegram Mini App
---

# /caspers-telegram-miniapp:miniapp

Launch the Caspers Heritage Telegram Mini App.

## Instructions

When this command is invoked:

1. Get the app URL from `plugin.get_app_url()`
2. If URL is configured, provide the deep link to open the Mini App
3. If not configured, show setup instructions

## Example Output (Configured)

```
🛍️ Opening Caspers Heritage Mini App

Click to browse our collection:
https://t.me/caspersheritagebot/app
```

## Example Output (Not Configured)

```
⚠️ Mini App Not Configured

The app URL has not been set. Run:
/caspers-telegram-miniapp:config <app-url>
```
