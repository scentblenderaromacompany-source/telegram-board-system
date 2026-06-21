---
name: search
description: Search the product catalog by name or description
arguments: <query>
---

# /supabase-jewelry:search

Search for products in the Caspers Heritage catalog.

## Instructions

When this command is invoked with `$ARGUMENTS`:

1. Use the search query from arguments
2. Call `plugin.search_products(query)`
3. Display matching products with details

## Example Usage

```
/supabase-jewelry:search ring
```

## Example Output

```
🔍 Search Results for "ring"

1. Gold Diamond Ring - $299.99 (ID: P001)
2. Silver Band Ring - $79.99 (ID: P045)

Found 2 products
```
