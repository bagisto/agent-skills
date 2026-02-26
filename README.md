# bagisto/agent-skills

Agent skills for [Bagisto](https://bagisto.com) — a Laravel-based open-source e-commerce platform.

These skills provide domain-specific, reusable context for AI agents (Claude Code, Cursor, Windsurf, etc.) working inside a Bagisto codebase.

## Available Skills

### `pest-testing`

Tests applications using the Pest 3 PHP framework.

**Activates when:** writing tests, creating unit or feature tests, adding assertions, testing Livewire components, architecture testing, debugging test failures, working with datasets or mocking — or when the user mentions `test`, `spec`, `TDD`, `expects`, `assertion`, `coverage`, or needs to verify functionality works.

---

### `payment-method-development`

Payment gateway development in Bagisto.

**Activates when:** creating payment methods, integrating payment gateways like Stripe, PayPal, or any third-party payment processor — or when the user mentions `payment`, `payment gateway`, `payment method`, `Stripe`, `PayPal`, or needs to add a new payment option to the checkout.

---

### `shipping-method-development`

Shipping method development in Bagisto.

**Activates when:** creating shipping methods, integrating shipping carriers like FedEx, UPS, DHL, or any third-party shipping provider — or when the user mentions `shipping`, `shipping method`, `shipping carrier`, `delivery`, or needs to add a new shipping option to checkout.

---

### `package-development`

Package development in Bagisto.

**Activates when:** creating packages, migrations, models, repositories, routes, controllers, views, localization, DataGrid, menus, ACL, or system configuration — or when the user mentions `package`, `migration`, `model`, `repository`, `controller`, `DataGrid`, `menu`, or `ACL`.

---

### `product-type-development`

Product type development in Bagisto.

**Activates when:** creating custom product types, defining product behaviors, or implementing specialized product logic — or when the user mentions `product type`, `custom product`, or needs to implement product-specific behavior.

---

## Install

Install all skills from this repo into your AI agent:

```bash
npx skills add bagisto/agent-skills
```

Install a specific skill only:

```bash
npx skills add bagisto/agent-skills --skill "pest-testing"
npx skills add bagisto/agent-skills --skill "payment-method-development"
npx skills add bagisto/agent-skills --skill "shipping-method-development"
npx skills add bagisto/agent-skills --skill "package-development"
npx skills add bagisto/agent-skills --skill "product-type-development"
```

Install for a specific agent:

```bash
npx skills add bagisto/agent-skills -a claude-code
npx skills add bagisto/agent-skills -a cursor
```

## Repository Structure

```
agent-skills/
├── skills/
│   ├── pest-testing/
│   │   └── SKILL.md
│   ├── payment-method-development/
│   │   └── SKILL.md
│   ├── shipping-method-development/
│   │   └── SKILL.md
│   ├── package-development/
│   │   └── SKILL.md
│   └── product-type-development/
│       └── SKILL.md
├── AGENTS.md
└── README.md
```

Each skill folder contains a SKILL.md file with agent-readable instructions and a YAML frontmatter block that defines when the skill activates.
