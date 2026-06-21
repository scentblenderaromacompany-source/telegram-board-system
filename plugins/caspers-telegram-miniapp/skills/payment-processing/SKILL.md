---
name: payment-processing
description: Handle payment processing for the Telegram Mini App. Use when processing payments or managing payment tokens.
---

# Payment Processing Skill

Handle payments for Caspers Heritage Telegram Mini App.

## Capabilities

- Process payments via Telegram's payment system
- Manage payment provider tokens
- Handle payment confirmations
- Process refunds
- Track payment history

## Usage

When the user asks about payments:

```python
# Check if payment is configured
stats = plugin.get_stats()
if stats["payment_configured"]:
    # Process payment
    pass
```

## Payment Flow

```
1. User selects products in Mini App
2. User confirms order
3. Bot sends invoice via Telegram
4. User provides payment details
5. Telegram processes payment
6. Bot receives payment confirmation
7. Order is fulfilled
```

## Configuration

Set `payment_provider_token` in the plugin config to enable payments:

```json
{
  "payment_provider_token": "YOUR_PAYMENT_PROVIDER_TOKEN"
}
```
