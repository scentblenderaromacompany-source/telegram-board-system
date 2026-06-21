---
name: order-management
description: Manage customer orders. Use when creating, tracking, or processing orders for Caspers Heritage jewelry.
---

# Order Management Skill

Handle customer orders for Caspers Heritage.

## Capabilities

- Create new orders with customer and product details
- Track order status (pending, processing, shipped, delivered)
- Update order information
- Cancel orders
- View order history

## Usage

When the user asks about orders, use the order management methods:

```python
plugin.create_order({
    "id": "ORD-001",
    "customer_id": "C123",
    "products": [{"id": "P001", "quantity": 1}],
    "total": 299.99
})
plugin.get_order("ORD-001")
```

## Order Status Flow

```
pending → processing → shipped → delivered
    ↓
  cancelled
```

## Order Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique order identifier |
| customer_id | string | Yes | Customer identifier |
| products | list | Yes | List of ordered products |
| total | float | Yes | Order total in USD |
| status | string | No | Order status (default: pending) |
| created_at | string | No | ISO timestamp |
| shipping_address | object | No | Shipping details |
