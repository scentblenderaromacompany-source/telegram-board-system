---
name: catalog
description: Display the full product catalog with prices and availability
---

# /supabase-jewelry:catalog

Display the complete product catalog for Caspers Heritage.

## Instructions

When this command is invoked:

1. Load the SupabaseJewelryPlugin
2. Call `plugin.get_catalog()` to retrieve all products
3. Format the output as a readable list showing:
   - Product name
   - Price
   - SKU (if available)
   - Inventory status

## Example Output

```
📦 Caspers Heritage Catalog

1. Gold Diamond Ring - $299.99 (SKU: GDR-001) ✅ In Stock
2. Silver Necklace - $149.99 (SKU: SN-002) ✅ In Stock
3. Pearl Earrings - $89.99 (SKU: PE-003) ⚠️ Low Stock
```
