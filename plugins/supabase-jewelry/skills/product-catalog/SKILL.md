---
name: product-catalog
description: Manage the jewelry product catalog. Use when adding, updating, searching, or listing products in the Caspers Heritage inventory.
---

# Product Catalog Skill

Manage the jewelry product catalog for Caspers Heritage.

## Capabilities

- Add new products with name, description, price, and images
- Update product details and pricing
- Search products by name, description, or category
- List all products or filter by category
- Delete products from the catalog

## Usage

When the user asks to manage products, use the JewelryPlugin methods:

```python
plugin.add_product({"id": "P001", "name": "Gold Ring", "price": 299.99})
plugin.search_products("ring")
plugin.get_catalog()
plugin.update_product("P001", {"price": 249.99})
plugin.delete_product("P001")
```

## Product Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique product identifier |
| name | string | Yes | Product name |
| description | string | No | Product description |
| price | float | Yes | Price in USD |
| category | string | No | Product category |
| images | list | No | List of image URLs |
| sku | string | No | Stock keeping unit |
| inventory | int | No | Stock count |
