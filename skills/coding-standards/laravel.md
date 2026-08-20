# Laravel in Bagisto

## Contents

- [Version and bootstrap](#version-and-bootstrap)
- [Events are strings](#events-are-strings)
- [Migrations](#migrations)
- [Configuration and `env()`](#configuration-and-env)
- [The global helpers](#the-global-helpers)
- [Validation](#validation)
- [Container bindings](#container-bindings)
- [Queues](#queues)
- [What not to reach for](#what-not-to-reach-for)

Bagisto is Laravel 12 on PHP 8.3+, but several places where a Laravel developer
would reach for the framework default, Bagisto has its own convention. Following
the framework instead of the codebase is the most common way generated code
looks wrong here.

## Version and bootstrap

Laravel 11+ slim skeleton — there is **no `providers` array in `config/app.php`**
and no `app/Http/Kernel.php`:

| Concern | File |
|---|---|
| Service providers | `bootstrap/providers.php` |
| Middleware, exceptions, routing | `bootstrap/app.php` (`withRouting`, `withMiddleware`, `withExceptions`) |
| Concord model registration | `config/concord.php` |

A package registers **twice** — its main provider in `bootstrap/providers.php`,
its `ModuleServiceProvider` in `config/concord.php`.

## Events are strings

This is the biggest departure. Bagisto does **not** use event classes. Events are
dot-delimited strings naming the domain, the entity and the moment:

```php
Event::dispatch('checkout.order.save.before', [$data]);
Event::dispatch('checkout.order.orderitem.save.after', $orderItem);
```

Listeners are mapped in a package's `EventServiceProvider` with `protected $listen`:

```php
protected $listen = [
    'customer.create.after' => [
        [Customer::class, 'afterCreated'],
    ],
];
```

Conventions that follow:

- **`<domain>.<entity>.<action>.<before|after>`**, lowercase and dotted.
- **Fire both halves.** `before` receives the input (an id or the payload);
  `after` receives the resulting model. A new action that fires only one half
  leaves listeners — including the full page cache — unable to react.
- **Do not create an event class** for a new hook. A string keeps it overridable
  by any package without a shared class to import.

## Migrations

Anonymous class, the Laravel 9+ form:

```php
return new class extends Migration
{
    public function up(): void { /* … */ }

    public function down(): void { /* … */ }
};
```

- Package migrations live in `src/Database/Migrations/` and load from the
  package's provider with `loadMigrationsFrom()`.
- **Write `down()`** — a migration that cannot be rolled back blocks everyone.
- **No comments inside the body**, as everywhere else.
- Adding a column used by a listing usually means a `product_flat` column too —
  see the `attribute-development` skill.

## Configuration and `env()`

**`env()` is only called inside `config/`.** Anywhere else it returns null once
the config is cached, which is the state of any production install.

Read settings through the config, and admin-configurable settings through core:

```php
config('app.admin_url');
core()->getConfigData('catalog.products.attribute.file_attribute_upload_size');
```

The single exception in the codebase is `EnvValidatorServiceProvider`, which
exists to report on the environment itself.

## The global helpers

Bagisto ships helpers that are the expected entry points. Use them rather than
resolving from the container by hand:

| Helper | For |
|---|---|
| `core()` | Channels, locales, currencies, admin configuration, price formatting |
| `bouncer()` | Admin permission checks |
| `acl()` | The permission tree |
| `datagrid()` | Resolving a DataGrid class |
| `image_manager()` | Image encoding and resizing |

`core()->getConfigData()` reads the admin's saved configuration, which is not the
same as `config()` — the first is database-backed and channel/locale aware.

## Validation

Use a FormRequest so the rules are one object a reviewer can read:

```php
public function update(CategoryRequest $request, int $id): JsonResponse
```

Inline `$request->validate()` exists in older controllers. Do not add more —
and a mass action validates too, since its `indices` array arrives from the
browser.

## Container bindings

Package providers bind interfaces to implementations and register singletons in
`register()`, and load routes, views, translations, migrations and config in
`boot()`. Extensions replace core behaviour by binding a subclass rather than
editing the class — that is what keeps a store upgradeable.

## Queues

Anything long-running is a queued job — indexing, imports, image downloads,
mail. Two rules the codebase already follows:

- **Assume the job runs more than once.** A queue retries, so make it idempotent.
- **Batch work, do not loop over everything in one job.** `Bus::batch()` with a
  chunk per job is the pattern; see the `data-transfer` skill.

With `QUEUE_CONNECTION=sync` a job runs inline in the request, which is fine for
a test fixture and useless for a real import.

## What not to reach for

| Laravel default | Bagisto instead |
|---|---|
| Event classes | dot-delimited event strings |
| `config/app.php` providers | `bootstrap/providers.php` + `config/concord.php` |
| `Model::all()` / query in a controller | a repository method |
| Route model binding | an id, resolved through the repository |
| `$request->validate()` | a FormRequest |
| A new facade | one of the existing global helpers |
