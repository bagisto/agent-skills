---
name: bagisto-product-type-development
description: Use when creating or changing a Bagisto product type — the product_types config, an AbstractType subclass, or type-specific cart, pricing and inventory behaviour. Trigger phrases include "product type", "AbstractType", "configurable", "bundle", "grouped", "downloadable", "virtual product", "subscription product", "prepareForCart".
requires: bagisto-package-development
license: MIT
---

# Product Type Development in Bagisto

## Overview

Creating custom product types in Bagisto allows you to define specialized product behaviors that match your business needs. Whether you need subscription products, rental items, digital services, or complex product variations, custom product types provide the flexibility to create exactly what your store requires.

## When to Apply

Activate this skill when:
- Creating new product types in Bagisto
- Building subscription or service-based products
- Implementing custom product behaviors
- Adding type-specific validation and pricing
- Modifying inventory/stock handling

---

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [configuration.md](configuration.md) | The product_types config and how Bagisto reads it |
| [abstract-type.md](abstract-type.md) | AbstractType and the methods worth overriding |
| [building-a-type.md](building-a-type.md) | A complete worked implementation, testing, pitfalls |

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
