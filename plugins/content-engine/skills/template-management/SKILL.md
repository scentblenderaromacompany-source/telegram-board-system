---
name: template-management
description: Manage content templates. Use when creating, updating, or using reusable content templates.
---

# Template Management Skill

Create and manage reusable content templates.

## Capabilities

- Create content templates with variables
- List available templates
- Get template by name
- Delete templates
- Use templates for content generation

## Usage

When the user asks about templates:

```python
plugin.add_template("product-announce", {
    "title": "New Product: {{name}}",
    "body": "Introducing {{name}} - {{description}}. Price: ${{price}}",
    "variables": ["name", "description", "price"]
})
plugin.get_template("product-announce")
plugin.list_templates()
```

## Template Variables

Use `{{variable}}` syntax for dynamic content. Variables are replaced at publish time.

## Template Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Template name (unique) |
| title | string | Yes | Title template |
| body | string | Yes | Body template |
| variables | list | No | List of variable names |
| metadata | object | No | Additional template data |
