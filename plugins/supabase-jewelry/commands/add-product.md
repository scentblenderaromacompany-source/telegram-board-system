---
name: add-product
description: Add a new product to the jewelry catalog
arguments: <name> <price> [sku]
---

# /supabase-jewelry:add-product

Add a new product to the Caspers Heritage catalog.

## Instructions

When this command is invoked with `$ARGUMENTS`:

1. Parse the product name and price from arguments
2. Optionally extract SKU if provided
3. Generate a unique product ID
4. Call `plugin.add_product()` with the product data
5. Confirm the addition with product details

## Example Usage

```
/supabase-jewelry:add-product Gold Ring 299.99 GDR-001
```

## Example Output

```
✅ Product Added

Name: Gold Ring
Price: $299.99
SKU: GDR-001
ID: P-1717200000
```
