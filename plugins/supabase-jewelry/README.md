# Supabase Jewelry Plugin

Supabase-backed jewelry business plugin for Caspers Heritage.

## Features

- Product catalog management (CRUD + search)
- Order management and tracking
- eBay / Shopify marketplace integration
- Supabase database connection

## Installation

```bash
/plugin install supabase-jewelry
```

## Commands

| Command | Description |
|---------|-------------|
| `/supabase-jewelry:catalog` | Display full product catalog |
| `/supabase-jewelry:add-product` | Add a new product |
| `/supabase-jewelry:search` | Search products by name/description |

## Skills

- **product-catalog** - Manage the jewelry product catalog
- **order-management** - Handle customer orders

## Configuration

Set environment variables:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Or configure via plugin config:

```json
{
  "supabase_url": "https://your-project.supabase.co",
  "supabase_key": "your-anon-key",
  "ebay_enabled": true,
  "shopify_enabled": true
}
```

## License

MIT
