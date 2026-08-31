# Bagisto Guidelines

Bagisto is a Laravel-based e-commerce platform. These guidelines are specifically curated for developing with Bagisto and its package-based architecture.

## Foundational Context

This application is a **Bagisto** e-commerce platform built on Laravel. You must be familiar with both Laravel and Bagisto's modular package architecture.

### Technology Stack

Read the versions from the checkout rather than assuming them — `composer.json`
for PHP, Laravel, Pest and PHPUnit, `packages/Webkul/Shop/package.json` for
Tailwind and Vite, and `Webkul\Core\Core::BAGISTO_VERSION` for the Bagisto line
itself.

Common to every line: Vue.js for admin interactivity, Tailwind CSS for styling,
Vite for bundling, Laravel Octane v2, Sanctum v4, Socialite v5, Boost v2, Pint
v1, and Laravel MCP v0 pulled in transitively by Boost.

### Bagisto Core Packages

Bagisto uses a modular package structure in `packages/Webkul/`. The table names the ones you will touch most; run `ls packages/Webkul` for the full list rather than assuming a package is absent:

| Package | Purpose |
|---------|---------|
| **Admin** | Admin panel functionality |
| **Shop** | Customer storefront |
| **Core** | Common utilities and helpers |
| **Product** | Product management |
| **Category** | Category management |
| **Checkout** | Cart and checkout process |
| **Payment** | Payment methods (CashOnDelivery, MoneyTransfer) |
| **Paypal** | PayPal integration |
| **Shipping** | Shipping methods |
| **Sales** | Order management |
| **Customer** | Customer management |
| **Attribute** | Product attributes |
| **Inventory** | Stock management |
| **CartRule** | Cart promotions |
| **CatalogRule** | Catalog promotions |
| **DataGrid** | Admin data tables |
| **Tax** | Tax calculation |
| **CMS** | Content management |
| **Theme** | Theme management |

## Skills Activation

This project has domain-specific skills available. You MUST activate the relevant skill whenever you work in that domain—don't wait until you're stuck.

- `bagisto-coding-standards` — Use when writing, changing or reviewing any Bagisto PHP or Blade — the conventions this codebase holds to, covering Laravel idiom, code style, comments and docblocks, database access, Blade, security and localization. Trigger phrases include "standards", "conventions", "code style", "docblock", "comments", "repository pattern", "blade", "component", "binding", "event", "migration", "security", "XSS", "authorization", "escaping", "is this safe", "best practice".

- `bagisto-package-development` — Use when creating or changing a Bagisto package — service providers, migrations, models, contracts, proxies, repositories, routes, controllers, Blade views, localization, admin menus, ACL or system configuration. Trigger phrases include "new package", "service provider", "migration", "model", "repository", "controller", "route", "ACL", "admin menu", "system config", "concord".

- `bagisto-shipping-method-development` — Use when creating or changing a Bagisto shipping method — a carrier class, shipping rates, the carriers config, or integrating a courier such as FedEx, UPS or DHL. Trigger phrases include "shipping", "shipping method", "carrier", "delivery", "shipping rate", "FedEx", "UPS", "DHL", "free shipping", "flat rate".

- `bagisto-payment-method-development` — Use when creating or changing a Bagisto payment method — a payment class, the payment methods config, the checkout redirect and callback flow, or integrating a gateway such as Stripe or PayPal. Trigger phrases include "payment", "payment method", "payment gateway", "Stripe", "PayPal", "Razorpay", "checkout payment", "redirect", "webhook".

- `bagisto-product-type-development` — Use when creating or changing a Bagisto product type — the product_types config, an AbstractType subclass, or type-specific cart, pricing and inventory behaviour. Trigger phrases include "product type", "AbstractType", "configurable", "bundle", "grouped", "downloadable", "virtual product", "subscription product", "prepareForCart".

- `bagisto-shop-theme-development` — Use when creating or changing a Bagisto storefront theme — a theme package, shop layouts, Blade component overrides, or the Vite asset pipeline for the customer-facing side. Trigger phrases include "shop theme", "storefront theme", "shop layout", "theme package", "vite", "tailwind", "publish views", "custom layout".

- `bagisto-shop-advance-theme-development` — Use when building a storefront feature against the advanced shop theme workflow — the non-negotiable rules and the end-to-end procedure for delivering one. Trigger phrases include "shop advance theme", "advanced theme", "storefront feature", "theme workflow", "definition of done".

- `bagisto-admin-theme-development` — Use when creating or changing a Bagisto admin theme — a theme package, admin layouts, Blade component overrides, or the Vite asset pipeline for the admin panel. Trigger phrases include "admin theme", "admin layout", "admin panel styling", "theme package", "vite", "tailwind", "publish views", "custom layout".

- `bagisto-pest-testing` — Use when writing or changing a Bagisto Pest test — feature or unit tests, assertions, datasets, mocking, architecture tests, or registering a new package's suite. Trigger phrases include "pest", "test", "unit test", "feature test", "assertion", "dataset", "mock", "testsuite", "TDD", "coverage".

- `bagisto-data-transfer` — Use when adding or changing a Bagisto import — an Importer class, a file source, the importers registry, the queued import pipeline, or a stuck or failing import job. Trigger phrases include "import", "importer", "data transfer", "CSV", "XLSX", "XML", "bulk upload", "import batch", "queued import", "validate rows".

- `bagisto-theme-sections` — Use when working on the Bagisto Appearance area — theme sections, the section editor and its storefront preview, draft and publish behaviour, section media, or the theme gallery. Trigger phrases include "section", "theme section", "appearance", "preview", "draft", "publish", "unsaved changes", "storefront layout", "theme gallery", "customize theme".

- `bagisto-attribute-development` — Use when working with Bagisto's EAV attribute system — adding or changing an attribute, attribute family or group, reading or writing a product attribute value, or debugging a value that reads back empty or from the wrong locale or channel. Trigger phrases include "attribute", "EAV", "attribute family", "attribute group", "attribute option", "custom attribute", "value_per_locale", "value_per_channel", "product_flat", "swatch".

- `bagisto-datagrid-development` — Use when building or changing a Bagisto admin listing page — a DataGrid class with columns, search, filters, sorting, row actions, mass actions or export, and the controller and Blade view that render it. Trigger phrases include "datagrid", "admin listing", "add a column", "mass action", "prepareQueryBuilder", "listing page", "grid filter", "export grid".

- `bagisto-playwright-testing` — Use when writing, changing or debugging a Bagisto end-to-end test — Playwright specs, page objects, ACL role coverage, fixtures, or a failing E2E run in CI. Trigger phrases include "playwright", "e2e", "end to end", "spec.ts", "page object", "browser test", "flaky test", "shard".

- `bagisto-code-review` — Use when reviewing Bagisto code changes or a pull request for correctness, convention compliance or quality, or when asked whether a change is ready to merge. Trigger phrases include "review", "code review", "PR review", "is this correct", "conventions", "violations", "code quality", "ready to merge".

- `bagisto-git-workflow` — Use when branching, committing, writing a CHANGELOG entry or opening a pull request against a Bagisto repository. Trigger phrases include "branch", "commit", "commit message", "PR", "pull request", "changelog", "merge", "conventional commits", "release notes".

- `bagisto-change-verification` — Use when a Bagisto change is about to be called done, or when asked to run the verification gates — code style, tests, end-to-end tests and translation completeness. Trigger phrases include "verify", "is this done", "run the gates", "pint", "pest", "playwright", "translations check", "ready to commit".

- `bagisto-documentation` — Use when writing or updating any Bagisto documentation site — the developer documentation, the merchant user guide, or any other Bagisto docs repository — covering page content, code samples, screenshots, the sidebar, image naming, and moving or deleting pages. Trigger phrases include "docs", "documentation", "user guide", "developer documentation", "dev docs", "merchant documentation", "marketplace docs", "document this", "update the docs", "add a doc page", "screenshot", "ImagePopup", "redirect a doc page".

- `bagisto-api-develop` — Use when working inside the bagisto-api package — installing or removing it, adding or changing a REST or GraphQL endpoint or resource, building an admin menu's API, or fixing package behaviour. Install and removal happen only on explicit request, never automatically. Trigger phrases include "ApiResource", "Provider", "Processor", "DTO", "resolver", "install the bagisto-api package", "remove the package", "add an endpoint", "extend an endpoint".

- `bagisto-api-shop` — Use when building a storefront app or UI on the Bagisto Shop API — a customer-facing storefront, catalog, cart, checkout, customer account, wishlist, compare, reviews, or any page or component of a shop on the API, whether web, mobile or custom. Ask the client's platform and stack first, and treat the api-docs as the source of truth for exact shapes. Trigger phrases include "products", "cart", "checkout", "coupons", "customer login", "customer account", "wishlist", "storefront on the API".

- `bagisto-api-admin` — Use when building an admin app or UI on the Bagisto Admin API — a back-office dashboard, an order, catalog, customer, marketing, CMS or settings management screen, an admin mobile app, the Create-Order flow, or any admin panel page on the API. Ask the client's platform and stack first, and treat the api-docs as the source of truth for exact shapes. Trigger phrases include "admin orders", "admin products", "customers", "cart rules", "CMS", "settings", "reporting", "admin panel on the API".

## Bagisto Architecture

### Package Structure

A package draws from the layout below, but **most take only part of it**. Only
`Providers/` is universal; roughly 25 of the core packages carry
`Contracts/Models/Repositories`, 14 a `Config/`, 11 `Http/Controllers/` and 8
`Routes/`. A domain package such as `Category`, `CartRule` or `Marketing` is a
data layer only — its admin screens live in `Admin`, its storefront pages in
`Shop`. Check the closest existing package before deciding what yours needs.

```
packages/Webkul/{PackageName}/
├── src/
│   ├── Config/
│   │   ├── admin-menu.php
│   │   └── system.php
│   ├── Database/
│   │   ├── Migrations/
│   │   ├── Seeders/
│   │   └── Factories/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── Admin/
│   │   │   └── Shop/
│   │   ├── Middleware/
│   │   └── Requests/
│   ├── Models/
│   │   └── {Package}Proxy.php
│   ├── Repositories/
│   │   └── {Package}Repository.php
│   ├── Resources/
│   │   ├── views/
│   │   ├── lang/
│   │   └── manifest.php
│   └── Providers/
│       └── {Package}ServiceProvider.php
└── composer.json
```

### Repository Pattern

Bagisto uses the Prettus L5 Repository pattern. Always use repositories for data access:

```php
// Correct way - inject the repository and let the container resolve it.
public function __construct(
    protected ProductRepository $productRepository,
) {}

$products = $this->productRepository->all();

// Outside a constructor, resolve it from the container.
$products = app(ProductRepository::class)->all();

// Avoid reaching for the model directly.
$products = Product::all(); // Less preferred
```

### Service Providers

Service providers must:
- Load routes from `Routes/admin-routes.php` and `Routes/shop-routes.php`
- Load migrations automatically
- Load translations from `Resources/lang`
- Load views from `Resources/views`
- Merge package configuration using `$this->mergeConfigFrom()`

## Conventions

- Always follow existing code conventions used in this application.
- Use descriptive names for variables and methods. For example, `isRegisteredForDiscounts`, not `discount()`.
- Check for existing components to reuse before writing new one.
- Use PHPDoc blocks with proper punctuation for all classes and methods.
- Follow the package structure when creating new packages.
- Use repositories for database operations.

## Verification Scripts

- Do not create verification scripts or tinker when tests cover that functionality and prove they work.
- Unit and feature tests are more important than manual verification.

## Application Structure & Architecture

- Stick to existing directory structure; don't create new base folders without approval.
- Do not change the application's dependencies without approval.
- Custom packages should be placed in `packages/Webkul/`.

## Frontend Bundling

- If the user doesn't see a frontend change reflected in the UI, it could mean they need to run `npm run build`, `npm run dev`, or `composer run dev`. Ask them.

## Documentation Files

- You must only create documentation files if explicitly requested by the user.

## Replies

- Be concise in your explanations - focus on what's important rather than explaining obvious details.
