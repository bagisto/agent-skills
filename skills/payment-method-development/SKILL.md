---
name: payment-method-development
description: Use when creating or changing a Bagisto payment method — a payment class, the payment methods config, the checkout redirect and callback flow, or integrating a gateway such as Stripe or PayPal. Trigger phrases include "payment", "payment method", "payment gateway", "Stripe", "PayPal", "Razorpay", "checkout payment", "redirect", "webhook".
requires: package-development, coding-standards
license: MIT
---

# Payment Method Development

## Overview

Creating custom payment methods in Bagisto allows you to integrate any payment gateway or processor with your store. Whether you need local payment methods, cryptocurrency payments, or specialized payment flows, custom payment methods provide the flexibility your business requires.

For our tutorial, we'll create a **Custom Stripe Payment** method that demonstrates all the essential concepts you need to build any type of payment solution.

## When to Apply

Activate this skill when:
- Creating new payment methods
- Integrating payment gateways (Stripe, PayPal, Razorpay, etc.)
- Adding payment options to checkout
- Modifying existing payment configurations
- Creating admin configuration for payment methods

## Bagisto Payment Architecture

Bagisto's payment system is built around a flexible method-based architecture that separates configuration from business logic.

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Payment Methods Configuration** | Defines payment method properties | `Config/payment-methods.php` |
| **Payment Classes** | Contains payment processing logic | `Payment/ClassName.php` |
| **System Configuration** | Admin interface forms | `Config/system.php` |
| **Service Provider** | Registers payment method | `Providers/ServiceProvider.php` |

### Key Features

- **Flexible Payment Processing**: Support for redirects, APIs, webhooks, or custom flows.
- **Configuration Management**: Admin-friendly settings interface.
- **Multi-channel Support**: Different settings per sales channel.
- **Security Ready**: Built-in CSRF protection and secure handling.
- **Extensible Architecture**: Easy integration with third-party gateways.

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [implementation.md](implementation.md) | Building a payment method — the step-by-step guide |
| [payment-api.md](payment-api.md) | The base payment class and the methods to override |
| [reference.md](reference.md) | Built-in methods, best practices, a complex integration example, package layout, testing, pitfalls |

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
