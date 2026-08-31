# Package Development

- CRITICAL: ALWAYS use the bagisto-package-development skill when creating packages in Bagisto.
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
- Translation files go in `src/Resources/lang/{locale}/` and use namespace `rma::` — the rule is owned by the `bagisto-coding-standards` skill (`localization.md`).
- DataGrid classes extend `Webkul\DataGrid\DataGrid` and are placed in `src/DataGrids/Admin/` — see the `bagisto-datagrid-development` skill.
- Admin menu is configured in `src/Config/admin-menu.php` and merged to `menu.admin`.
- ACL is configured in `src/Config/acl.php` and merged to `acl`.
- System configuration is in `src/Config/system.php` and merged to `core`.
- Use `core()->getConfigData('key.path')` to retrieve configuration values.
- Use `bouncer()->hasPermission('key')` to check ACL permissions in controllers and views.
