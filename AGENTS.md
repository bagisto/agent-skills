<bagisto-guidelines>
=== foundation rules ===

# Bagisto Guidelines

Bagisto is a Laravel-based e-commerce platform. These guidelines are specifically curated for developing with Bagisto and its package-based architecture.

## Foundational Context

This application is a **Bagisto** e-commerce platform built on Laravel 12. You must be familiar with both Laravel and Bagisto's modular package architecture.

### Technology Stack

- **PHP**: 8.3+
- **Laravel**: v12
- **Vue.js**: For admin panel interactivity
- **Tailwind CSS**: For styling
- **Laravel Octane**: v2
- **Laravel Sanctum**: v4
- **Laravel Socialite**: v5
- **Laravel Boost**: v2
- **Laravel MCP**: v0
- **Laravel Pint**: v1
- **Pest**: v3
- **PHPUnit**: v11

### Bagisto Core Packages

Bagisto uses a modular package structure in `packages/Webkul/`:

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

- `coding-standards` — Use when writing, changing or reviewing any Bagisto PHP or Blade — the conventions this codebase holds to, covering Laravel idiom, code style, comments and docblocks, database access, Blade, security and localization. Trigger phrases include "standards", "conventions", "code style", "docblock", "comments", "repository pattern", "blade", "component", "binding", "event", "migration", "security", "XSS", "authorization", "escaping", "is this safe", "best practice".
- `package-development` — Use when creating or changing a Bagisto package — service providers, migrations, models, contracts, proxies, repositories, routes, controllers, Blade views, localization, admin menus, ACL or system configuration. Trigger phrases include "new package", "service provider", "migration", "model", "repository", "controller", "route", "ACL", "admin menu", "system config", "concord".

- `shipping-method-development` — Use when creating or changing a Bagisto shipping method — a carrier class, shipping rates, the carriers config, or integrating a courier such as FedEx, UPS or DHL. Trigger phrases include "shipping", "shipping method", "carrier", "delivery", "shipping rate", "FedEx", "UPS", "DHL", "free shipping", "flat rate".

- `payment-method-development` — Use when creating or changing a Bagisto payment method — a payment class, the payment methods config, the checkout redirect and callback flow, or integrating a gateway such as Stripe or PayPal. Trigger phrases include "payment", "payment method", "payment gateway", "Stripe", "PayPal", "Razorpay", "checkout payment", "redirect", "webhook".

- `product-type-development` — Use when creating or changing a Bagisto product type — the product_types config, an AbstractType subclass, or type-specific cart, pricing and inventory behaviour. Trigger phrases include "product type", "AbstractType", "configurable", "bundle", "grouped", "downloadable", "virtual product", "subscription product", "prepareForCart".

- `shop-theme-development` — Use when creating or changing a Bagisto storefront theme — a theme package, shop layouts, Blade component overrides, or the Vite asset pipeline for the customer-facing side. Trigger phrases include "shop theme", "storefront theme", "shop layout", "theme package", "vite", "tailwind", "publish views", "custom layout".

- `shop-advance-theme-development` — Use when building a storefront feature against the advanced shop theme workflow — the non-negotiable rules and the end-to-end procedure for delivering one. Trigger phrases include "shop advance theme", "advanced theme", "storefront feature", "theme workflow", "definition of done".

- `admin-theme-development` — Use when creating or changing a Bagisto admin theme — a theme package, admin layouts, Blade component overrides, or the Vite asset pipeline for the admin panel. Trigger phrases include "admin theme", "admin layout", "admin panel styling", "theme package", "vite", "tailwind", "publish views", "custom layout".

- `pest-testing` — Use when writing or changing a Bagisto Pest test — feature or unit tests, assertions, datasets, mocking, architecture tests, or registering a new package's suite. Trigger phrases include "pest", "test", "unit test", "feature test", "assertion", "dataset", "mock", "testsuite", "TDD", "coverage".

- `data-transfer` — Use when adding or changing a Bagisto import — an Importer class, a file source, the importers registry, the queued import pipeline, or a stuck or failing import job. Trigger phrases include "import", "importer", "data transfer", "CSV", "XLSX", "XML", "bulk upload", "import batch", "queued import", "validate rows".
- `theme-sections` — Use when working on the Bagisto Appearance area — theme sections, the section editor and its storefront preview, draft and publish behaviour, section media, or the theme gallery. Trigger phrases include "section", "theme section", "appearance", "preview", "draft", "publish", "unsaved changes", "storefront layout", "theme gallery", "customize theme".
- `attribute-development` — Use when working with Bagisto's EAV attribute system — adding or changing an attribute, attribute family or group, reading or writing a product attribute value, or debugging a value that reads back empty or from the wrong locale or channel. Trigger phrases include "attribute", "EAV", "attribute family", "attribute group", "attribute option", "custom attribute", "value_per_locale", "value_per_channel", "product_flat", "swatch".
- `datagrid-development` — Use when building or changing a Bagisto admin listing page — a DataGrid class with columns, search, filters, sorting, row actions, mass actions or export, and the controller and Blade view that render it. Trigger phrases include "datagrid", "admin listing", "add a column", "mass action", "prepareQueryBuilder", "listing page", "grid filter", "export grid".
- `playwright-testing` — Use when writing, changing or debugging a Bagisto end-to-end test — Playwright specs, page objects, ACL role coverage, fixtures, or a failing E2E run in CI. Trigger phrases include "playwright", "e2e", "end to end", "spec.ts", "page object", "browser test", "flaky test", "shard".

- `code-review` — Use when reviewing Bagisto code changes or a pull request for correctness, convention compliance or quality, or when asked whether a change is ready to merge. Trigger phrases include "review", "code review", "PR review", "is this correct", "conventions", "violations", "code quality", "ready to merge".
- `git-workflow` — Use when branching, committing, writing a CHANGELOG entry or opening a pull request against a Bagisto repository. Trigger phrases include "branch", "commit", "commit message", "PR", "pull request", "changelog", "merge", "conventional commits", "release notes".
- `change-verification` — Use when a Bagisto change is about to be called done, or when asked to run the verification gates — code style, tests, end-to-end tests and translation completeness. Trigger phrases include "verify", "is this done", "run the gates", "pint", "pest", "playwright", "translations check", "ready to commit".


- `bagisto-api-develop` — Install / remove / extend the `bagisto-api` package (REST + GraphQL). Activates when installing or removing the package, or adding/changing an endpoint, resource, or admin menu's API; or when the user mentions `ApiResource`, `Provider`, `Processor`, `DTO`, "install the package", or "add an endpoint". Install/remove run only on explicit request.

- `bagisto-api-shop` — Build a storefront app/UI on the Shop API (`/api/shop/*` + `/api/graphql`). Activates when building a customer-facing storefront, catalog/cart/checkout flow, customer account, or shopping app; or when the user mentions products, cart, checkout, coupons, wishlist, or customer login/account.

- `bagisto-api-admin` — Build an admin app/UI on the Admin API (`/api/admin/*` + `/api/admin/graphql`). Activates when building an admin dashboard, back-office panel, or an order/catalog/customer/marketing/CMS/settings management screen; or when the user mentions admin orders, products, customers, reporting, or "admin panel on the API".

## Bagisto Architecture

### Package Structure

Every Bagisto package follows a standardized structure:

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

=== boost rules ===

# Laravel Boost

Laravel Boost is an MCP server that comes with powerful tools designed specifically for this application. Use them.

## Artisan

- Use the `list-artisan-commands` tool when you need to call an Artisan command to double-check the available parameters.

## URLs

- Whenever you share a project URL with the user, you should use the `get-absolute-url` tool to ensure you're using the correct scheme, domain/IP, and port.

## Tinker / Debugging

- You should use the `tinker` tool when you need to execute PHP to debug code or query Eloquent models directly.
- Use the `database-query` tool when you only need to read from the database.
- Use the `database-schema` tool to inspect table structure before writing migrations or models.

## Reading Browser Logs With the `browser-logs` Tool

- You can read browser logs, errors, and exceptions using the `browser-logs` tool from Boost.
- Only recent browser logs will be useful - ignore old logs.

## Searching Documentation (Critically Important)

- Boost comes with a powerful `search-docs` tool you should use before trying other approaches when working with Laravel or Laravel ecosystem packages.
- This tool automatically passes a list of installed packages and their versions to the remote Boost API, so it returns only version-specific documentation for your circumstance.
- Search the documentation before making code changes to ensure we are taking the correct approach.
- Use multiple, broad, simple, topic-based queries at once. For example: `['rate limiting', 'routing rate limiting', 'routing']`.
- Do not add package names to queries; package information is already shared.

### Available Search Syntax

1. Simple Word Searches with auto-stemming - query=authentication - finds 'authenticate' and 'auth'.
2. Multiple Words (AND Logic) - query=rate limit - finds knowledge containing both "rate" AND "limit".
3. Quoted Phrases (Exact Position) - query="infinite scroll" - words must be adjacent and in that order.
4. Mixed Queries - query=middleware "rate limit" - "middleware" AND exact phrase "rate limit".
5. Multiple Queries - queries=["authentication", "middleware"] - ANY of these terms.

=== php rules ===

# PHP

- Always use curly braces for control structures, even for single-line bodies.

## Constructors

- Use PHP 8 constructor property promotion in `__construct()`.
    - `public function __construct(public GitHub $github) { }`
- Do not allow empty `__construct()` methods with zero parameters unless the constructor is private.

## Type Declarations

- Always use explicit return type declarations for methods and functions.
- Use appropriate PHP type hints for method parameters.

```php
protected function isAccessible(User $user, ?string $path = null): bool
{
    ...
}
```

## Enums

- Typically, keys in an Enum should be TitleCase. For example: `FavoritePerson`, `BestLake`, `Monthly`.

## Comments

- Prefer PHPDoc blocks over inline comments. Never use comments within the code itself unless the logic is exceptionally complex.

## PHPDoc Blocks

- Add useful array shape type definitions when appropriate.
- Always use proper punctuation at the end of descriptions.

=== tests rules ===

# Test Enforcement

- Every change must be programmatically tested. Write a new test or update an existing test, then run the affected tests to make sure they pass.
- Run the minimum number of tests needed to ensure code quality and speed. Use `php artisan test --compact` with a specific filename or filter.

=== laravel/core rules ===

# Do Things the Laravel Way

- Use `php artisan make:` commands to create new files (i.e. migrations, controllers, models, etc.). You can list available Artisan commands using the `list-artisan-commands` tool.
- If you're creating a generic PHP class, use `php artisan make:class`.
- Pass `--no-interaction` to all Artisan commands to ensure they work without user input.

## Database

- Always use proper Eloquent relationship methods with return type hints.
- Use Eloquent models and relationships before suggesting raw database queries.
- Use Repository pattern for Bagisto packages.
- Avoid `DB::`; prefer `Model::query()`. Generate code that leverages Laravel's ORM capabilities.
- Generate code that prevents N+1 query problems by using eager loading.
- Use Laravel's query builder for very complex database operations.

### Model Creation

- When creating new models, create useful factories and seeders for them too. Ask the user if they need any other things, using `list-artisan-commands` to check the available options to `php artisan make:model`.

### APIs & Eloquent Resources

- For APIs, default to using Eloquent API Resources and API versioning unless existing API routes do not, then you should follow existing application convention.

## Controllers & Validation

- Always create Form Request classes for validation rather than inline validation in controllers.
- Check sibling Form Requests to see if the application uses array or string based validation rules.

## Authentication & Authorization

- Use Laravel's built-in authentication and authorization features (gates, policies, Sanctum, etc.).

## URL Generation

- When generating links to other pages, prefer named routes and the `route()` function.

## Queues

- Use queued jobs for time-consuming operations with the `ShouldQueue` interface.

## Configuration

- Use environment variables only in configuration files - never use the `env()` function directly outside of config files.
- Always use `config('app.name')`, not `env('APP_NAME')`.

## Testing

- When creating models for tests, use the factories for the models. Check if the factory has custom states that can be used before manually setting up the model.
- Faker: Use methods such as `$this->faker->word()` or `fake()->randomDigit()`.
- When creating tests, make use of `php artisan make:test [options] {name}` to create a feature test, and pass `--unit` to create a unit test. Most tests should be feature tests.

## Vite Error

- If you receive an "Illuminate\Foundation\ViteException: Unable to locate file in Vite manifest" error, you can run `npm run build` or ask the user to run `npm run dev` or `composer run dev`.

=== laravel/v12 rules ===

# Laravel 12

- CRITICAL: ALWAYS use `search-docs` tool for version-specific Laravel documentation and updated code examples.
- Since Laravel 11, Laravel has a new streamlined file structure which this project uses.

## Laravel 12 Structure

- In Laravel 12, middleware are no longer registered in `app/Http/Kernel.php`.
- Middleware are configured declaratively in `bootstrap/app.php` using `Application::configure()->withMiddleware()`.
- `bootstrap/app.php` is the file to register middleware, exceptions, and routing files.
- `bootstrap/providers.php` contains application specific service providers.
- The `app/Console/Kernel.php` file no longer exists; use `bootstrap/app.php` or `routes/console.php` for console configuration.
- Console commands in `app/Console/Commands/` are automatically available and do not require manual registration.

## Database

- When modifying a column, the migration must include all of the attributes that were previously defined on the column. Otherwise, they will be dropped and lost.
- Laravel 12 allows limiting eagerly loaded records natively, without external packages: `$query->latest()->limit(10);`.

### Models

- Casts can and likely should be set in a `casts()` method on a model rather than the `$casts` property. Follow existing conventions from other models.

=== boost/core rules ===

# Laravel Boost

- Laravel Boost is an MCP server that comes with powerful tools designed specifically for this application. Use them.

## Artisan

- Use the `list-artisan-commands` tool when you need to call an Artisan command to double-check the available parameters.

## URLs

- Whenever you share a project URL with the user, you should use the `get-absolute-url` tool to ensure you're using the correct scheme, domain/IP, and port.

## Tinker / Debugging

- You should use the `tinker` tool when you need to execute PHP to debug code or query Eloquent models directly.
- Use the `database-query` tool when you only need to read from the database.
- Use the `database-schema` tool to inspect table structure before writing migrations or models.

## Reading Browser Logs

- You can read browser logs, errors, and exceptions using the `browser-logs` tool from Boost.
- Only recent browser logs will be useful - ignore old logs.

## Searching Documentation

- Use `search-docs` tool before making code changes to ensure we are taking the correct approach.
- Use multiple, broad, simple, topic-based queries at once.

=== pint/core rules ===

# Laravel Pint Code Formatter

- You must run `vendor/bin/pint --dirty --format agent` before finalizing changes to ensure your code matches the project's expected style.
- Do not run `vendor/bin/pint --test --format agent`, simply run `vendor/bin/pint --format agent` to fix any formatting issues.

=== pest/core rules ===

## Pest

- This project uses Pest for testing. Create tests: `php artisan make:test --pest {name}`.
- Run tests: `php artisan test --compact` or filter: `php artisan test --compact --filter=testName`.
- Do NOT delete tests without approval.
- CRITICAL: ALWAYS use `search-docs` tool for version-specific Pest documentation and updated code examples.
- IMPORTANT: Activate `pest-testing` every time you're working with a Pest or testing-related task.
- IMPORTANT: Activate `playwright-testing` for anything under `tests/e2e-pw/`, and `change-verification` before calling any change done.

=== payment-method-development rules ===

# Payment Gateway Development

- CRITICAL: ALWAYS use the payment-method-development skill when working with payment methods in Bagisto.
- Payment methods in Bagisto are located in `packages/Webkul/Payment/src/Payment/` and `packages/Webkul/Paypal/src/Payment/`.
- All payment methods extend `Webkul\Payment\Payment\Payment` abstract class.
- Payment configuration is defined in `Config/payment-methods.php` files.
- System configuration for admin panel is defined in `Config/system.php` files.
- Service providers must merge payment method configuration using `$this->mergeConfigFrom()`.
- Always follow the existing code patterns and PHPDoc conventions when creating payment methods.
- For testing payment methods, refer to `packages/Webkul/Shop/tests/Feature/Checkout/CheckoutTest.php`.

=== shipping-method-development rules ===

# Shipping Method Development

- CRITICAL: ALWAYS use the shipping-method-development skill when working with shipping methods in Bagisto.
- Shipping methods in Bagisto are located in `packages/Webkul/Shipping/src/Carriers/`.
- All shipping methods extend `Webkul\Shipping\Carriers\AbstractShipping` abstract class.
- Shipping carrier configuration is defined in `Config/carriers.php` files.
- System configuration for admin panel is defined in `Config/system.php` files.
- Service providers must merge carrier configuration using `$this->mergeConfigFrom()`.
- Always follow the existing code patterns and PHPDoc conventions when creating shipping methods.
- Use `core()->convertPrice()` for multi-currency support when setting prices.
- Check `$item->getTypeInstance()->isStockable()` for per-item shipping calculations.

=== coding-standards rules ===

# Coding Standards

- CRITICAL: ALWAYS use the coding-standards skill when writing or changing any Bagisto PHP or Blade. It owns code style, comments and docblocks, Laravel idiom, data access, Blade, security and localization; `vendor/bin/pint` owns everything mechanical.
- Every method and property carries a docblock, whatever its visibility. Class members run constants → properties → constructor → public → protected → private.
- No comments inside a method body, array literal, route group or markup — in PHP, Blade, JS or Vue alike. A non-obvious reason goes in the docblock or the commit message.
- A condition with more than one clause goes multiline, the boolean operator leading each line.
- All database access goes through a repository. The one sanctioned exception is a DataGrid's `prepareQueryBuilder()`.
- Events are dot-delimited strings (`catalog.product.update.after`), never event classes, and fire in `before`/`after` pairs.
- `env()` is called only inside `config/`; read admin settings with `core()->getConfigData()`.
- Authorize on the server, scope every storefront query to the authenticated customer, and escape with `e()` anything interpolated into markup — an attribute is the dangerous position.

## Blade

- CRITICAL: the same skill covers every `.blade.php` file.
- Binding: `attr="text"` is a literal, `:attr="expr"` is a Blade/PHP expression, `::attr="expr"` escapes to a literal `:attr` for Vue. Getting `:` vs `::` wrong is the most common source of bugs.
- Reuse the globally registered `x-admin::` / `x-shop::` components and layouts; prefix only your own new components with your package namespace.
- Vue-backed components: `<v-name>` wrapper + `<script type="text/x-template" id="v-name-template">` + `app.component("v-name", ...)`, all inside `@pushOnce('scripts')` … `@endPushOnce`. Emit runtime values as `@{{ … }}`.
- Formatting: 4 spaces; more than one attribute means one per line with the closing `>` on its own line; a single attribute stays inline; no blank lines between a tag's attributes; one blank line between sibling blocks.
- Align the `=>` in Blade `@props`/arrays. Do NOT align them in real `.php` files — Pint single-spaces those.
- Comments follow the layer they sit in: `{{-- --}}` for Blade/PHP notes, `<!-- -->` for markup section dividers, and `/** … */` JSDoc blocks inside `<script>` and `<style>` — never `//` or bare `/* */` there.
- Comment casing: a sentence is capitalized and punctuated; a bare title/label is Title Case with no trailing period.
- Never hardcode UI strings — use `@lang('<ns>::app…')`, and add new keys to every locale.
- Gate admin actions with `@if (bouncer()->hasPermission('resource.action'))`.
- Bracket meaningful content with `{!! view_render_event('bagisto.<area>.<path>.before') !!}` / `.after`.

=== package-development rules ===

# Package Development

- CRITICAL: ALWAYS use the package-development skill when creating packages in Bagisto.
- Use the Bagisto Package Generator (`composer require bagisto/bagisto-package-generator`) for quick setup.
- Package structure must follow the standardized layout in `packages/Webkul/`.
- Service providers must be registered in `bootstrap/providers.php`.
- Always run `composer dump-autoload` after adding new packages.
- Break a condition with more than one clause (`&&` / `||`) across lines, operator leading each line; keep single-clause conditions inline. Pint does not enforce this — see the skill's PHP Code Style section.
- Reference files: `core.md` (structure, service providers), `data-layer.md` (models, migrations, repositories), `ui.md` (routes, controllers, views), `features.md` (localization, menus, ACL, system config), `code-style.md`, `data-access.md`.

#### core.md — Structure & Registration
- Use `$this->loadMigrationsFrom()`, `$this->loadRoutesFrom()`, `$this->loadViewsFrom()`, `$this->loadTranslationsFrom()` in service provider boot() method.
- Use `$this->mergeConfigFrom()` in service provider register() method for config merging.
- Register models in ModuleServiceProvider using Concord for proxy resolution.

#### data-layer.md — Data Layer
- Use migrations in `src/Database/Migrations/` for database schema.
- Always create Contract, Model, and Proxy for each data entity (three-component model system).
- Use Prettus L5 Repository pattern for data access (extends `Webkul\Core\Eloquent\Repository`).
- Repository model() method must return the contract class path, not the model class.
- Use package prefix for table names (e.g., `rma_requests` instead of `return_requests`).
- Register models in `config/concord.php` via ModuleServiceProvider.

#### ui.md — UI Layer
- Routes must be in `src/Routes/admin-routes.php` and `src/Routes/shop-routes.php`.
- Admin routes use middleware `['web', 'admin']` with prefix from `config('app.admin_url')`.
- Shop routes use middleware `['web', 'locale', 'theme', 'currency']`.
- Controllers must extend package base Controller which extends `Illuminate\Routing\Controller`.
- Use dependency injection for repositories in controllers.
- Use `<x-admin::layouts>` and `<x-shop::layouts>` for Blade views.
- Use `<x-admin::datagrid>` component for admin tables.
- Views must be loaded with namespace prefix (e.g., `rma::admin.return-requests.index`).

#### features.md — Features
- Translation files go in `src/Resources/lang/{locale}/` and use namespace `rma::` — the rule is owned by the `coding-standards` skill (`localization.md`).
- DataGrid classes extend `Webkul\DataGrid\DataGrid` and are placed in `src/DataGrids/Admin/` — see the `datagrid-development` skill.
- Admin menu is configured in `src/Config/admin-menu.php` and merged to `menu.admin`.
- ACL is configured in `src/Config/acl.php` and merged to `acl`.
- System configuration is in `src/Config/system.php` and merged to `core`.
- Use `core()->getConfigData('key.path')` to retrieve configuration values.
- Use `bouncer()->hasPermission('key')` to check ACL permissions in controllers and views.

=== product-type-development rules ===

# Product Type Development

- CRITICAL: ALWAYS use the product-type-development skill when working with product types in Bagisto.
- Product types extend `Webkul\Product\Type\AbstractType` base class.
- Product type configuration is defined in `Config/product-types.php` files.
- Reference files: `configuration.md` (config structure), `abstract-type.md` (AbstractType methods), `building-a-type.md` (a complete implementation).
- Product types must be registered in service provider using `$this->mergeConfigFrom()`.
- Key methods to override: `isSaleable()`, `isStockable()`, `showQuantityBox()`, `haveSufficientQuantity()`, `prepareForCart()`, `getTypeValidationRules()`.
- Use `$additionalViews` for custom admin interface sections.
- Use `$skipAttributes` to hide irrelevant attributes for product type.

=== api-platform-development rules ===

# Bagisto API Platform (REST + GraphQL)

- CRITICAL: use the `bagisto-api-develop` skill when installing / removing / extending the `bagisto-api` package; use `bagisto-api-shop` or `bagisto-api-admin` when building an app or UI on the API.
- Two surfaces: **Storefront** — `/api/shop/*` (REST) + `/api/graphql`, authed by the `X-STOREFRONT-KEY` header (plus a customer or guest-cart Bearer token for cart/account calls). **Admin** — `/api/admin/*` (REST) + `/api/admin/graphql`, authed by a pre-issued admin Integration Bearer token. The admin API mirrors the admin panel menu-for-menu.
- The api-docs (`https://api-docs.bagisto.com` and its `/llms.txt` index) are the source of truth for exact request/response shapes — open the endpoint page; never invent a payload from memory.
- GraphQL `id` is selectable only on fetchable (noun) resources (product, customer, order). Action/result mutations (cart writes, place-order, cancel, comment) return result fields (`cartId`, `orderId`, `success`, `message`) — never `id`. GraphQL inputs are camelCase.
- Admin collections return a `{ data, meta }` envelope; storefront paginated collections expose `X-Total-*` headers; page size is `?per_page=N` (+ `?page=N`).
- Extending the package: REST + GraphQL share the same Provider/Processor — any change to one must keep the other working, so run the resource's GraphQL test before the REST test. Mirror the admin panel, not a superset. No auto-commit — the user commits.

</bagisto-guidelines>
