# bagisto/agent-skills

Agent skills for [Bagisto](https://bagisto.com) — a Laravel-based open-source e-commerce platform.

These skills provide domain-specific, reusable context for AI agents (Claude Code, Cursor, Windsurf, etc.) working inside a Bagisto codebase.

## Available Skills

### `package-development`

Package development in Bagisto.

**Activates when:** creating packages, migrations, models, repositories, routes, controllers, views, localization, DataGrid, menus, ACL, or system configuration — or when the user mentions `package`, `migration`, `model`, `repository`, `controller`, `DataGrid`, `menu`, or `ACL`.

---

### `shipping-method-development`

Shipping method development in Bagisto.

**Activates when:** creating shipping methods, integrating shipping carriers like FedEx, UPS, DHL, or any third-party shipping provider — or when the user mentions `shipping`, `shipping method`, `shipping carrier`, `delivery`, or needs to add a new shipping option to checkout.

---

### `payment-method-development`

Payment gateway development in Bagisto.

**Activates when:** creating payment methods, integrating payment gateways like Stripe, PayPal, or any third-party payment processor — or when the user mentions `payment`, `payment gateway`, `payment method`, `Stripe`, `PayPal`, or needs to add a new payment option to the checkout.

---

### `product-type-development`

Product type development in Bagisto.

**Activates when:** creating custom product types, defining product behaviors, or implementing specialized product logic — or when the user mentions `product type`, `custom product`, or needs to implement product-specific behavior.

---

### `shop-theme-development`

Shop theme development in Bagisto.

**Activates when:** creating custom storefront themes, modifying shop layouts, building theme packages, or working with Vite-powered assets for the customer-facing side of the application.

---

### `shop-advance-theme-development`

Shop Advance Theme Development in Bagisto — an advanced, end-to-end storefront theme workflow that ships design references, scaffolding scripts, templates, and full Playwright commerce coverage.

**Activates when:** creating, redesigning, extending, debugging, validating, packaging, testing, or upgrading production Bagisto storefront themes — UI/UX design direction, design tokens and commerce design systems, Shop theme registration and resource overlays, Blade/Vue components, Vite/Tailwind assets, dynamic admin-controlled and theme-customization content, channels, localization/RTL, accessibility, performance, distributable packages, or resolving theme inheritance and asset-manifest failures.

---

### `admin-theme-development`

Admin theme development in Bagisto.

**Activates when:** creating custom admin themes, modifying admin layouts, building admin theme packages, or working with admin panel styling and interface customization.

---

### `pest-testing`

Tests applications using the Pest 3 PHP framework.

**Activates when:** writing tests, creating unit or feature tests, adding assertions, testing Livewire components, architecture testing, debugging test failures, working with datasets or mocking — or when the user mentions `test`, `spec`, `TDD`, `expects`, `assertion`, `coverage`, or needs to verify functionality works.

---

### `blade-conventions`

Blade template conventions for any Bagisto package — Admin, Shop, or a custom Webkul-style module.

**Activates when:** creating or editing Blade views, building anonymous `@props` or Vue-backed `x-template` components, wiring forms, datagrids, modals, layouts, or slots — or when matching the project's markup, attribute-binding (`:` vs `::`), indentation, comment, and formatting style.

---

## API Platform Skills

These cover the **Bagisto API Platform** package — the REST + GraphQL API layer (storefront + admin). They're grouped under `skills/api-platform-development/`, and each ships a `reference/` tree of per-feature guides and checklists (the skills above are single `SKILL.md` files).

### `bagisto-api-develop`

Install / remove / extend the `bagisto-api` package.

**Activates when:** installing or removing the package, or adding/changing a REST or GraphQL endpoint, a resource, or an admin menu's API — or when the user mentions `ApiResource`, `Provider`, `Processor`, `DTO`, "install the package", or "add an endpoint". (Install and removal run only on explicit request.)

---

### `bagisto-api-shop`

Build a storefront app or UI on the **Shop API** (`/api/shop/*` + `/api/graphql`).

**Activates when:** building a customer-facing storefront, catalog/cart/checkout flow, customer account, or mobile shopping app — or when the user mentions products, cart, checkout, coupons, wishlist, or customer login/account.

---

### `bagisto-api-admin`

Build an admin app or UI on the **Admin API** (`/api/admin/*` + `/api/admin/graphql`).

**Activates when:** building an admin dashboard, back-office panel, or an order/catalog/customer/marketing/CMS/settings management screen — or when the user mentions admin orders, products, customers, reporting, or "admin panel on the API".

---

## Install

Install all skills from this repo into your AI agent:

```bash
npx skills add bagisto/agent-skills
```

Install a specific skill only:

```bash
npx skills add bagisto/agent-skills --skill "package-development"
npx skills add bagisto/agent-skills --skill "shipping-method-development"
npx skills add bagisto/agent-skills --skill "payment-method-development"
npx skills add bagisto/agent-skills --skill "product-type-development"
npx skills add bagisto/agent-skills --skill "shop-theme-development"
npx skills add bagisto/agent-skills --skill "shop-advance-theme-development"
npx skills add bagisto/agent-skills --skill "admin-theme-development"
npx skills add bagisto/agent-skills --skill "pest-testing"
npx skills add bagisto/agent-skills --skill "blade-conventions"
```

Install an API Platform skill (grouped under `skills/api-platform-development/`):

```bash
npx skills add bagisto/agent-skills --skill "bagisto-api-develop"
npx skills add bagisto/agent-skills --skill "bagisto-api-shop"
npx skills add bagisto/agent-skills --skill "bagisto-api-admin"
```

> The API skills are grouped under `skills/api-platform-development/` and carry `reference/` subfolders. The `skills` CLI discovers grouped skills automatically (it walks subfolders under `skills/`), so `npx skills add bagisto/agent-skills` and the `--skill <name>` commands pick them up. To install one manually instead, copy it in: `cp -r skills/api-platform-development/bagisto-api-shop ~/.claude/skills/` (user-wide) or into a project's `.claude/skills/`.

Install for a specific agent:

```bash
npx skills add bagisto/agent-skills -a claude-code
npx skills add bagisto/agent-skills -a cursor
```

## Repository Structure

```
agent-skills/
├── skills/
│   ├── package-development/
│   │   └── SKILL.md
│   ├── shipping-method-development/
│   │   └── SKILL.md
│   ├── payment-method-development/
│   │   └── SKILL.md
│   ├── product-type-development/
│   │   └── SKILL.md
│   ├── shop-theme-development/
│   │   └── SKILL.md
│   ├── shop-advance-theme-development/
│   │   ├── SKILL.md
│   │   ├── references/              # architecture, UI/UX, commerce, testing + bagisto-theme-testing/
│   │   ├── scripts/                 # scaffold, inspect, validate, diff, snapshot (+ tests)
│   │   ├── assets/                  # brief, baseline, smoke, contract templates
│   │   └── data/                    # bagisto-ui-ux.json
│   ├── admin-theme-development/
│   │   └── SKILL.md
│   ├── pest-testing/
│   │   └── SKILL.md
│   ├── blade-conventions/
│   │   └── SKILL.md
│   └── api-platform-development/        # REST + GraphQL API skills (grouped)
│       ├── bagisto-api-develop/
│       │   ├── SKILL.md
│       │   └── reference/               # install, structure, conventions, …
│       ├── bagisto-api-shop/
│       │   ├── SKILL.md
│       │   └── reference/               # flows/, features/
│       └── bagisto-api-admin/
│           ├── SKILL.md
│           └── reference/               # flows/, menus/
├── AGENTS.md
└── README.md
```

Each skill folder contains a `SKILL.md` with agent-readable instructions and a YAML frontmatter block that defines when the skill activates. The API Platform skills additionally carry a `reference/` folder of per-feature guides and checklists that their `SKILL.md` links to.
