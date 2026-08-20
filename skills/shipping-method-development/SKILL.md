---
name: shipping-method-development
description: Use when creating or changing a Bagisto shipping method — a carrier class, shipping rates, the carriers config, or integrating a courier such as FedEx, UPS or DHL. Trigger phrases include "shipping", "shipping method", "carrier", "delivery", "shipping rate", "FedEx", "UPS", "DHL", "free shipping", "flat rate".
requires: package-development
license: MIT
---

# Shipping Method Development

## Overview

Creating custom shipping methods in Bagisto allows you to tailor delivery options to meet your specific business needs. Whether you need special handling for fragile items, express delivery options, or region-specific shipping rules, custom shipping methods provide the flexibility your e-commerce store requires.

For our tutorial, we'll create a **Custom Express Shipping** method that demonstrates all the essential concepts you need to build any type of shipping solution.

## When to Apply

Activate this skill when:
- Creating new shipping methods
- Integrating shipping carriers (FedEx, UPS, DHL, USPS, etc.)
- Adding shipping options to checkout
- Modifying existing shipping configurations
- Creating admin configuration for shipping methods
- Implementing rate calculation logic

## Bagisto Shipping Architecture

Bagisto's shipping system is built around a flexible carrier-based architecture that separates configuration from business logic.

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Carriers Configuration** | Defines shipping method properties | `Config/carriers.php` |
| **Carrier Classes** | Contains rate calculation logic | `Carriers/ClassName.php` |
| **System Configuration** | Admin interface forms | `Config/system.php` |
| **Service Provider** | Registers shipping method | `Providers/ServiceProvider.php` |
| **Shipping Facade** | Collects and manages rates | `Webkul\Shipping\Shipping` |

### Key Features

- **Flexible Rate Calculation**: Support for per-unit, per-order, weight-based, or custom pricing.
- **Configuration Management**: Admin-friendly settings interface.
- **Multi-channel Support**: Different rates and settings per sales channel.
- **Localization Ready**: Full translation support.
- **Extensible Architecture**: Easy integration with third-party APIs.

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [implementation.md](implementation.md) | Building a carrier — the step-by-step guide |
| [carrier-api.md](carrier-api.md) | The base carrier class and the CartShippingRate model |
| [reference.md](reference.md) | Built-in carriers, pricing examples, the Shipping facade, package layout, testing, pitfalls |

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
