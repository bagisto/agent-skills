---
name: package-development
description: "Package development in Bagisto. Activates when creating packages, migrations, models, repositories, routes, controllers, views, localization, DataGrid, menus, ACL, or system configuration. Use references to skills for specific areas: @core, @data, @ui, @features."
license: MIT
metadata:
  author: bagisto
  references:
    - core: Package structure, service providers, package generator
    - data: Migrations, models (contracts, proxies), repositories
    - ui: Routes, controllers, Blade views
    - features: Localization, DataGrid, menus, ACL, system config
---

# Package Development in Bagisto

## Overview

A package is a self-contained module that encapsulates specific features or functionality in Bagisto. This comprehensive skill covers all aspects of package development from structure to advanced features.

## When to Apply

Activate this skill when:
- Creating new packages for Bagisto
- Setting up package directory structure
- Creating database migrations
- Building Eloquent models with contracts and proxies
- Implementing repositories for data access
- Creating routes for admin/shop sections
- Building controllers with dependency injection
- Creating Blade views with Bagisto layouts
- Adding multi-language support
- Creating admin DataGrid tables
- Setting up admin navigation menus
- Implementing permission-based access control
- Creating configurable settings for admin

---

# PHP Code Style

`vendor/bin/pint` fixes most formatting, so run it and trust it. The rules below are the ones Pint
does **not** enforce — they have to be written by hand, and they apply to every PHP file in a
package (controllers, repositories, models, DataGrids, enums, listeners, jobs).

These rules cover `.php` files, and they apply just as much to PHP written inside an `@php … @endphp`
block in a Blade file — Pint cannot reach a `.blade.php`, so there you apply them by hand. Blade's own
layer (`@props`, directive arguments, markup) has its own conventions: see the **blade-conventions**
skill.

## Multi-clause conditions go multiline

A condition with **more than one clause** (two or more operands joined by `&&` / `||`) is broken
across lines: the `(` opens alone, each clause sits on its own line at one indent, the boolean
operator **leads** the line it joins, and `) {` closes back at the statement's indent.

```php
// Good — each clause is one scannable line, and the operator is the first thing you read.
if (
    $product->is_owner
    && $product->is_approved
    && ! $product->is_draft
) {
    app(SellerProductIndexer::class)->reindex($product->product);
}

// Bad — clauses run together, and the operators hide at the end of the line.
if ($product->is_owner && $product->is_approved && ! $product->is_draft) {
    app(SellerProductIndexer::class)->reindex($product->product);
}
```

A **single-clause** condition stays inline — wrapping it adds noise and hides nothing:

```php
if (! $product) {
    return;
}

if ($request->ajax()) {
    return datagrid(ProductDataGrid::class)->process();
}
```

The rule keys off the number of clauses, not line length: two short clauses still go multiline.

```php
if (
    $product->is_approved
    && $product->seller->is_approved
) {
    // ...
}
```

Applies equally to `elseif`, `while`, and a `return` of a compound boolean:

```php
return is_null($value)
    || $value === '';
```

Guard clauses that merely negate one call (`if (! $this->cart) {`) are single-clause and stay
inline, as do single-clause returns, ternaries, and arrow functions.

## Every method gets a docblock

No exceptions, and regardless of visibility — `public`, `protected`, and `private` alike. A method
without one is incomplete, even when its name seems to say everything.

The description is a **sentence**: capitalised, ending in a full stop. One line is the norm; write a
second only when the first cannot carry it.

```php
/**
 * Reindex all products.
 */
public function reIndexAll()

/**
 * Source documents from the core product index for the given ids, keyed by product id.
 */
protected function fetchSourceDocuments($channel, $locale, array $productIds): array
```

```php
/**
 * reindex all products      ← no capital, no full stop
 */

/**
 * Reindexes all of the products
 */                          ← no full stop
```

Type information belongs in the signature. Add `@param` / `@return` only for what a native type
cannot express — the shape of an array, or a mixed return:

```php
/**
 * Products grouped by seller id.
 *
 * @return array<int, list<Product>>
 */
protected function groupBySeller(array $products): array
```

## Every property gets a docblock too

The same rule extends to **class constants and properties** — `const`, `static`, typed, untyped,
whatever the visibility. Bagisto's own models document `$table`, `$fillable` and `$casts`, and a new
property that skips one stands out. **Each property carries its own docblock**, even when several sit
together — one docblock describing two adjacent properties leaves the second undocumented:

```php
// Wrong — the second property has no docblock of its own.
/**
 * The table and columns the index covers.
 */
protected string $table = 'product_inventories';

protected array $columns = ['vendor_id', 'product_id', 'qty'];
```

```php
/**
 * The table associated with the model.
 *
 * @var string
 */
protected $table = 'marketplace_pickups';

/**
 * The attributes that should be cast.
 *
 * @var array
 */
protected $casts = [
    'scheduled_from' => 'datetime',
];

/**
 * The courier is booked and has not yet called.
 */
public const STATUS_SCHEDULED = 'scheduled';
```

Keep `@var` on untyped properties, where it is the only type information there is. Drop it when the
property is already typed in the declaration — repeating it adds nothing:

```php
/**
 * Unique carrier code, matching the key under `marketplace_carriers.carriers`.
 */
protected string $code;
```

**Constructor-promoted properties are the exception.** They are parameters, and the constructor's own
docblock covers them — do not document each one:

```php
/**
 * Create a new repository instance.
 */
public function __construct(
    protected PickupRepository $pickupRepository,
    protected ShippingLabelRepository $labelRepository
) {}
```

## A class docblock defines; it does not narrate

Describe what the class **is**, in a sentence or two. Do not write the history of how it came to
exist, what it replaced, or why a past approach was wrong — that belongs in the commit message.

```php
/**
 * Drives a carrier for a saved shipment: buys the label, books the collection, and returns the
 * values to write back onto the shipment.
 */
class FulfilmentBooker
```

```php
/**
 * Turns a saved shipment into a real, carried parcel.
 *
 * This is the step the package was missing. A marketplace seller does not invent a tracking
 * number — they pick a carrier and a collection slot, and the carrier hands back the tracking
 * number, the label and the booking. So the carrier is driven here, straight after the shipment
 * row exists, and whatever it returns is written back onto that row.
 */                              ← history and justification, not a definition
class FulfilmentBooker
```

A genuine constraint still deserves a comment — put it **where it applies**, inside the method,
under "Comment only what the code cannot say" above. A reader looking for the rule about
re-delivered jobs wants it next to the guard, not in a preamble they scrolled past.

A plain `Class ProductRepository` restates the declaration and is worse than nothing.

## Order members by visibility

Lay a class out in the order Bagisto's own classes use, so a new member lands where a reader expects
it rather than wherever the diff was easiest:

1. Constants
2. Properties
3. The constructor
4. Abstract method declarations (the contract a trait or base class requires)
5. Public methods
6. Protected methods
7. Private methods

The visibility order is the one that matters most, and it cuts **both ways** — a `protected` or
`private` helper never sits above or between the public methods, and a `public` method never sits
buried among the protected ones. Each visibility forms one contiguous block.

When you add a helper that an existing public method calls, resist dropping it right after that caller
— that leaves a protected method in the middle of the public ones. Put it in the protected block at
the bottom.

```php
class Reporting
{
    public function countLowStock($seller): int
    {
        return $this->lowStockQuery($seller)->count();   // caller stays up top…
    }

    public function getTopProducts($seller) { /* … */ }

    // …every other public method…

    protected function lowStockQuery($seller)            // …the helper lives down here
    {
        // …
    }
}
```

**Check the whole file, not just your own lines.** Whenever you edit a class, scan its full member
order and fix any member that is already out of place — a public helper wedged among protected
methods, a property with no docblock, a private method sitting up in the public block. Leaving a
pre-existing violation in a file you just touched is the same defect as introducing one.

Within a visibility group, keep related methods together (a getter beside the query it wraps), but do
not reorder existing members to achieve it — the grouping is a tie-breaker, not a mandate to churn a
file.

## Comment only what the code cannot say

The rule above is about **docblocks**. This one is about **explanation inside a method body**, which
is where over-commenting accumulates.

Bagisto's own packages are sparsely commented, and generated code that is not will stand out
immediately. Inside a method the default is **no comment**. Earn one.

A comment is warranted when a reader who understands the code would still act wrongly without it —
almost always because the code encodes a **constraint that is invisible locally**:

- A line that looks removable or simplifiable but is load-bearing (a join deliberately kept out of
  a base query, a filter written as a negation for a reason).
- A non-obvious ordering, compatibility, or migration concern.
- A workaround for behaviour in core, Laravel, or a third-party service.

```php
/**
 * Joined only for these filters. Kept out of the base query because the `or` in its condition is
 * not indexable — MySQL scans the whole products table per candidate row.
 */
$qb->leftJoin('products as variants', function ($join) {
    $join->on('variants.parent_id', '=', 'products.id')
        ->orOn('variants.id', '=', 'products.id');
});
```

Do **not** explain code that already reads clearly. These are all noise:

```php
/**
 * Loop through the products.        ← narrates the obvious
 */
foreach ($products as $product) { ... }

/**
 * Set the total.                    ← labels an assignment
 */
$total = $invoice->sub_total - $invoice->discount_amount;

/**
 * Dispatch the event.               ← restates the call
 */
Event::dispatch('marketplace.product.update.after', $sellerProduct);
```

Keep the ones you do write **short** — two or three lines. A paragraph explaining a symptom in
detail belongs in the commit message or the PR, not above the statement. State the constraint, not
the war story.

---

# Data Access

## Go through the repository, never the query builder

Every read and write goes through a repository. Reaching for `DB::table(...)` or the model's query
builder from a controller, listener, job, or service bypasses the layer the whole codebase is built
on — and makes the operation impossible to reuse or override.

```php
// Good — the operation lives on the repository, named for what it does.
$this->pickupRepository->attachShipment($pickup, $shipment->id);
```

```php
// Bad — a service reaching past the repository into the table.
DB::table('marketplace_pickups')
    ->where('id', $pickup->id)
    ->update(['package_count' => $pickup->shipments()->count()]);
```

If the repository has no method for what you need, **add one**. That is the extension point:

```php
/**
 * Attach a shipment to a collection and refresh its package count.
 */
public function attachShipment(Pickup $pickup, int $shipmentId): void
{
    $pickup->shipments()->syncWithoutDetaching([$shipmentId]);

    $this->update(['package_count' => $pickup->shipments()->count()], $pickup->id);
}
```

**The one place `DB` is expected is a DataGrid's `prepareQueryBuilder()`**, which is built on the
query builder by design and returns a `Builder` for the grid to paginate. `DB::transaction()` and
`DB::raw()` inside a repository are also fine — the objection is to querying *tables* from outside
the data layer, not to the facade itself.

### Scope every seller-facing query in the repository

On a marketplace, a repository method that touches seller-owned data takes the seller id as its
first argument and filters on it. Then there is no call shape that can reach another seller's rows:

```php
/**
 * One of a seller's collections, or null when it is not theirs.
 */
public function findForSeller(int $sellerId, int $pickupId): ?Pickup
{
    return $this->model
        ->where('marketplace_seller_id', $sellerId)
        ->where('id', $pickupId)
        ->first();
}
```

---

# @core: Package Development - Core

## Package Structure

### Standard Directory Structure

```
packages/Webkul/{PackageName}/
├── src/
│   ├── Config/
│   │   ├── admin-menu.php
│   │   ├── acl.php
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
│   │   └── lang/
│   ├── Providers/
│   │   ├── {Package}ServiceProvider.php
│   │   └── ModuleServiceProvider.php
│   ├── DataGrids/
│   │   └── Admin/
│   └── manifest.php
└── composer.json
```

## Using Package Generator

The generator is a **convenience, not a requirement** — it only scaffolds the files described in
"Manual Setup" below. Skip this section entirely if you would rather create the files yourself, or
if adding a dev dependency to the project needs sign-off first.

### Installation

```bash
composer require --dev bagisto/bagisto-package-generator
```

### Creating a Package

```bash
# If package directory doesn't exist
php artisan package:make Webkul/RMA

# If package directory already exists
php artisan package:make Webkul/RMA --force
```

### Making Models

```bash
php artisan package:make-model ReturnRequest Webkul/RMA
```

### Making Repositories

```bash
php artisan package:make-repository ReturnRequestRepository Webkul/RMA
```

### Making Migrations

```bash
php artisan package:make-migration CreateRmaRequestsTable Webkul/RMA
```

## Manual Setup

### Create Package Directory

```bash
mkdir -p packages/Webkul/RMA/src/Providers
```

### Create Service Provider

**File:** `packages/Webkul/RMA/src/Providers/RMAServiceProvider.php`

```php
<?php

namespace Webkul\RMA\Providers;

use Illuminate\Support\ServiceProvider;

class RMAServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        //
    }
}
```

## Registering Your Package

### Update Composer Autoloader

In root `composer.json`:

```json
{
    "autoload": {
        "psr-4": {
            "Webkul\\RMA\\": "packages/Webkul/RMA/src"
        }
    }
}
```

Then run:

```bash
composer dump-autoload
```

### Register Service Provider

In `bootstrap/providers.php`:

```php
<?php

return [
    App\Providers\AppServiceProvider::class,
    
    // ... other providers ...
    
    Webkul\RMA\Providers\RMAServiceProvider::class,
];
```

### Clear Cache

```bash
php artisan optimize:clear
```

## Service Provider Methods

### Loading Migrations

```php
public function boot(): void
{
    $this->loadMigrationsFrom(__DIR__ . '/../Database/Migrations');
}
```

### Loading Routes

```php
public function boot(): void
{
    $this->loadRoutesFrom(__DIR__ . '/../Routes/admin-routes.php');
    $this->loadRoutesFrom(__DIR__ . '/../Routes/shop-routes.php');
}
```

### Loading Views

```php
public function boot(): void
{
    $this->loadViewsFrom(__DIR__ . '/../Resources/views', 'rma');
}
```

### Loading Translations

```php
public function boot(): void
{
    $this->loadTranslationsFrom(__DIR__ . '/../Resources/lang', 'rma');
}
```

### Merging Config

```php
public function register(): void
{
    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/admin-menu.php',
        'menu.admin'
    );

    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/acl.php',
        'acl'
    );

    $this->mergeConfigFrom(
        dirname(__DIR__) . '/Config/system.php',
        'core'
    );
}
```

## Concord Model Registration

### Create ModuleServiceProvider

**File:** `packages/Webkul/RMA/src/Providers/ModuleServiceProvider.php`

```php
<?php

namespace Webkul\RMA\Providers;

use Konekt\Concord\BaseModuleServiceProvider;

class ModuleServiceProvider extends BaseModuleServiceProvider
{
    protected $models = [
        \Webkul\RMA\Models\ReturnRequest::class,
    ];
}
```

### Register in concord.php

In `config/concord.php`:

```php
<?php

return [
    'modules' => [
        // Other service providers...
        \Webkul\RMA\Providers\ModuleServiceProvider::class,
    ],
];
```

---

# @data: Package Development - Data Layer

## Migrations

### Creating Migrations

```bash
# Using Bagisto generator
php artisan package:make-migration CreateRmaRequestsTable Webkul/RMA

# Using Laravel artisan
php artisan make:migration CreateRmaRequestsTable --path=packages/Webkul/RMA/src/Database/Migrations
```

### Basic Migration Structure

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('rma_requests', function (Blueprint $table) {
            $table->id();
            $table->unsignedInteger('customer_id');
            $table->unsignedInteger('order_id');
            $table->string('product_sku');
            $table->string('product_name');
            $table->integer('product_quantity');
            $table->string('status')->default('pending');
            $table->string('reason')->nullable();
            $table->text('admin_notes')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('rma_requests');
    }
};
```

### Running Migrations

Migrations alter the database, so run them against your local or staging database — never straight
against production — and make sure the package's migrations are the only ones pending if you are
unsure what else is queued (`php artisan migrate:status` lists them first).

```bash
# Run all migrations
php artisan migrate

# Run specific package migrations
php artisan migrate --path=packages/Webkul/RMA/src/Database/Migrations

# Check migration status
php artisan migrate:status
```

## Models

### Bagisto Model Architecture

Bagisto uses a three-component model system:
1. **Contract** - Interface defining the public API
2. **Model** - Eloquent model implementation
3. **Proxy** - Runtime model resolution via Concord

### Creating Model Components

```bash
# Using Bagisto generator (creates all three)
php artisan package:make-model ReturnRequest Webkul/RMA
```

### Contract

**File:** `packages/Webkul/RMA/src/Contracts/ReturnRequest.php`

```php
<?php

namespace Webkul\RMA\Contracts;

interface ReturnRequest
{
}
```

### Model Proxy

**File:** `packages/Webkul/RMA/src/Models/ReturnRequestProxy.php`

```php
<?php

namespace Webkul\RMA\Models;

use Konekt\Concord\Proxies\ModelProxy;

class ReturnRequestProxy extends ModelProxy
{
}
```

### Base Model

**File:** `packages/Webkul/RMA/src/Models/ReturnRequest.php`

```php
<?php

namespace Webkul\RMA\Models;

use Illuminate\Database\Eloquent\Model;
use Webkul\RMA\Contracts\ReturnRequest as ReturnRequestContract;

class ReturnRequest extends Model implements ReturnRequestContract
{
    protected $table = 'rma_requests';

    protected $fillable = [
        'customer_id',
        'order_id',
        'product_sku',
        'product_name',
        'product_quantity',
        'status',
        'reason',
        'admin_notes',
    ];
}
```

### Model Properties

| Property | Purpose |
|----------|---------|
| `$table` | Database table name (use package prefix) |
| `$fillable` | Mass-assignable fields |
| `$guarded` | Fields that cannot be mass-assigned |
| `$dates` | Date columns |
| `$casts` | Type casting |
| `$with` | Eager loading relationships |

## Repositories

### Repository Pattern

Bagisto uses the Prettus L5 Repository package for data access abstraction.

### Creating Repositories

```bash
php artisan package:make-repository ReturnRequestRepository Webkul/RMA
```

### Basic Repository Structure

**File:** `packages/Webkul/RMA/src/Repositories/ReturnRequestRepository.php`

```php
<?php

namespace Webkul\RMA\Repositories;

use Webkul\Core\Eloquent\Repository;

class ReturnRequestRepository extends Repository
{
    public function model(): string
    {
        return 'Webkul\RMA\Contracts\ReturnRequest';
    }
}
```

### Available Repository Methods

#### Basic CRUD

```php
// Create
$returnRequest = $repository->create([
    'customer_id' => 1,
    'order_id' => 123,
    'product_sku' => 'SAMPLE-001',
    'status' => 'pending',
]);

// Read
$all = $repository->all();
$find = $repository->find($id);
$findOrFail = $repository->findOrFail($id);
$first = $repository->findWhere(['status' => 'pending'])->first();

// Update
$repository->update(['status' => 'approved'], $id);

// Delete
$repository->delete($id);
```

#### Advanced Queries

```php
// Where conditions
$results = $repository->findWhere([
    'status' => 'pending',
    'customer_id' => 456,
]);

// Where in
$results = $repository->findWhereIn('id', [1, 2, 3]);

// Where between
$results = $repository->findWhereBetween('created_at', ['2024-01-01', '2024-12-31']);

// Pagination
$paginator = $repository->paginate(15);

// Eager loading
$withRelations = $repository->with(['customer', 'order'])->find($id);
```

### Custom Repository Methods

```php
<?php

namespace Webkul\RMA\Repositories;

use Webkul\Core\Eloquent\Repository;

class ReturnRequestRepository extends Repository
{
    public function model(): string
    {
        return 'Webkul\RMA\Contracts\ReturnRequest';
    }

    public function getPendingForCustomer(int $customerId)
    {
        return $this->findWhere([
            'customer_id' => $customerId,
            'status' => 'pending'
        ]);
    }

    public function getStats(): array
    {
        return [
            'total' => $this->count(),
            'pending' => $this->findWhere(['status' => 'pending'])->count(),
            'approved' => $this->findWhere(['status' => 'approved'])->count(),
        ];
    }

    public function getRecent(int $limit = 10)
    {
        return $this->orderBy('created_at', 'desc')
            ->limit($limit)
            ->get();
    }
}
```

---

# @ui: Package Development - UI Layer

## Routes

### Admin Routes

**File:** `packages/Webkul/RMA/src/Routes/admin-routes.php`

```php
<?php

use Illuminate\Support\Facades\Route;
use Webkul\RMA\Http\Controllers\Admin\ReturnRequestController;

Route::group([
    'middleware' => ['web', 'admin'],
    'prefix' => config('app.admin_url')
], function () {
    Route::prefix('rma/return-requests')->group(function () {
        Route::get('', [ReturnRequestController::class, 'index'])
            ->name('admin.rma.return-requests.index');

        Route::get('{id}', [ReturnRequestController::class, 'show'])
            ->name('admin.rma.return-requests.show');

        Route::post('', [ReturnRequestController::class, 'store'])
            ->name('admin.rma.return-requests.store');

        Route::put('{id}', [ReturnRequestController::class, 'update'])
            ->name('admin.rma.return-requests.update');

        Route::delete('{id}', [ReturnRequestController::class, 'destroy'])
            ->name('admin.rma.return-requests.destroy');

        Route::post('mass-delete', [ReturnRequestController::class, 'massDestroy'])
            ->name('admin.rma.return-requests.mass-delete');
    });
});
```

### Shop Routes

**File:** `packages/Webkul/RMA/src/Routes/shop-routes.php`

```php
<?php

use Illuminate\Support\Facades\Route;
use Webkul\RMA\Http\Controllers\Shop\ReturnRequestController;

Route::group([
    'middleware' => ['web', 'locale', 'theme', 'currency']
], function () {
    Route::prefix('rma/return-requests')->group(function () {
        Route::get('', [ReturnRequestController::class, 'index'])
            ->name('shop.rma.return-requests.index');

        Route::post('', [ReturnRequestController::class, 'store'])
            ->name('shop.rma.return-requests.store');
    });
});
```

### Route Middleware

| Middleware | Purpose |
|------------|---------|
| `web` | Session handling, CSRF protection |
| `admin` | Admin authentication |
| `locale` | Language handling |
| `theme` | Theme resolution |
| `currency` | Currency handling |

## Controllers

### Base Controller

**File:** `packages/Webkul/RMA/src/Http/Controllers/Controller.php`

```php
<?php

namespace Webkul\RMA\Http\Controllers;

use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Foundation\Bus\DispatchesJobs;
use Illuminate\Foundation\Validation\ValidatesRequests;
use Illuminate\Routing\Controller as BaseController;

class Controller extends BaseController
{
    use AuthorizesRequests, DispatchesJobs, ValidatesRequests;
}
```

### Admin Controller

**File:** `packages/Webkul/RMA/src/Http/Controllers/Admin/ReturnRequestController.php`

```php
<?php

namespace Webkul\RMA\Http\Controllers\Admin;

use Webkul\RMA\Http\Controllers\Controller;
use Webkul\RMA\Repositories\ReturnRequestRepository;
use Webkul\RMA\DataGrids\Admin\ReturnRequestDataGrid;

class ReturnRequestController extends Controller
{
    public function __construct(
        protected ReturnRequestRepository $returnRequestRepository
    ) {}

    public function index()
    {
        if (request()->ajax()) {
            return datagrid(ReturnRequestDataGrid::class)->process();
        }

        return view('rma::admin.return-requests.index');
    }

    public function show(int $id)
    {
        $returnRequest = $this->returnRequestRepository->findOrFail($id);

        return view('rma::admin.return-requests.show', compact('returnRequest'));
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'customer_id' => 'required|integer',
            'order_id' => 'required|integer',
            'product_sku' => 'required|string',
            'product_name' => 'required|string',
            'product_quantity' => 'required|integer|min:1',
            'reason' => 'nullable|string',
        ]);

        $this->returnRequestRepository->create($data);

        return redirect()->route('admin.rma.return-requests.index')
            ->with('success', 'Return request created successfully.');
    }

    public function update(Request $request, int $id)
    {
        $data = $request->validate([
            'status' => 'required|string|in:pending,approved,rejected',
            'admin_notes' => 'nullable|string',
        ]);

        $this->returnRequestRepository->update($data, $id);

        return redirect()->back()->with('success', 'Return request updated.');
    }

    public function destroy(int $id)
    {
        $this->returnRequestRepository->delete($id);

        return redirect()->back()->with('success', 'Return request deleted.');
    }

    public function massDestroy()
    {
        $indices = request()->input('indices');

        foreach ($indices as $index) {
            $this->returnRequestRepository->delete($index);
        }

        return response()->json(['message' => 'Selected records deleted.']);
    }
}
```

### Shop Controller

**File:** `packages/Webkul/RMA/src/Http/Controllers/Shop/ReturnRequestController.php`

```php
<?php

namespace Webkul\RMA\Http\Controllers\Shop;

use Webkul\RMA\Http\Controllers\Controller;
use Webkul\RMA\Repositories\ReturnRequestRepository;

class ReturnRequestController extends Controller
{
    public function __construct(
        protected ReturnRequestRepository $returnRequestRepository
    ) {}

    public function index()
    {
        $returnRequests = $this->returnRequestRepository->findWhere([
            'customer_id' => auth()->id()
        ]);

        return view('rma::shop.return-requests.index', compact('returnRequests'));
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'order_id' => 'required|integer',
            'product_sku' => 'required|string',
            'product_name' => 'required|string',
            'product_quantity' => 'required|integer|min:1',
            'reason' => 'required|string',
        ]);

        $data['customer_id'] = auth()->id();
        $data['status'] = 'pending';

        $this->returnRequestRepository->create($data);

        return redirect()->back()->with('success', 'Return request submitted.');
    }
}
```

## Views

> **Writing the Blade itself?** The **blade-conventions** skill carries the markup rules —
> `:` vs `::` attribute binding, anonymous vs Vue-backed components, indentation, comment
> style, and where translations and `view_render_event` hooks go.

### Admin Layout

```blade
<x-admin::layouts>
    <x-slot:title>
        @lang('rma::app.admin.return-requests.title')
    </x-slot:title>

    <!-- Content here -->
</x-admin::layouts>
```

### Shop Layout

```blade
<x-shop::layouts>
    <x-slot:title>
        @lang('rma::app.shop.return-requests.title')
    </x-slot:title>

    <!-- Content here -->
</x-shop::layouts>
```

### Admin Index View

**File:** `packages/Webkul/RMA/src/Resources/views/admin/return-requests/index.blade.php`

```blade
<x-admin::layouts>
    <x-slot:title>
        @lang('rma::app.admin.return-requests.title')
    </x-slot:title>

    <div class="flex gap-4 justify-between items-center max-sm:flex-wrap">
        <p class="text-xl text-gray-800 dark:text-white font-bold">
            @lang('rma::app.admin.return-requests.title')
        </p>
    </div>

    <x-admin::datagrid :src="route('admin.rma.return-requests.index')" />
</x-admin::layouts>
```

### Admin Detail View

**File:** `packages/Webkul/RMA/src/Resources/views/admin/return-requests/show.blade.php`

```blade
<x-admin::layouts>
    <x-slot:title>
        @lang('rma::app.admin.return-requests.show.title')
    </x-slot:title>

    <div class="flex gap-4 justify-between items-center max-sm:flex-wrap">
        <p class="text-xl text-gray-800 dark:text-white font-bold">
            @lang('rma::app.admin.return-requests.show.title') #{{ $returnRequest->id }}
        </p>
    </div>

    <div class="flex gap-2.5 mt-3.5 max-xl:flex-wrap">
        <div class="flex flex-col gap-2 flex-1 max-xl:flex-auto">
            <div class="p-4 bg-white dark:bg-gray-900 rounded box-shadow">
                <p class="text-base text-gray-800 dark:text-white font-semibold mb-4">
                    @lang('rma::app.admin.return-requests.show.general-info')
                </p>

                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-gray-600 dark:text-gray-300 font-semibold">
                            @lang('rma::app.admin.return-requests.show.product-name'):
                        </p>
                        <p class="text-gray-800 dark:text-white">
                            {{ $returnRequest->product_name }}
                        </p>
                    </div>

                    <div>
                        <p class="text-gray-600 dark:text-gray-300 font-semibold">
                            @lang('rma::app.admin.return-requests.show.status'):
                        </p>
                        <span class="badge label-info">
                            {{ ucfirst($returnRequest->status) }}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</x-admin::layouts>
```

---

# @features: Package Development - Features

## Localization

### Creating Translation Files

**File:** `packages/Webkul/RMA/src/Resources/lang/en/app.php`

```php
<?php

return [
    'admin' => [
        'return-requests' => [
            'title' => 'RMA Listing',
            'datagrid' => [
                'id' => 'ID',
                'product-name' => 'Product Name',
                'status' => 'Status',
                'view' => 'View',
            ],
        ],
    ],
];
```

### Loading Translations

In service provider `boot()` method:

```php
$this->loadTranslationsFrom(__DIR__ . '/../Resources/lang', 'rma');
```

### Using Translations

```blade
<!-- In Blade templates -->
@lang('rma::app.admin.return-requests.title')
```

```php
// In controllers/code
trans('rma::app.admin.return-requests.title')
__('rma::app.admin.return-requests.title')
```

### Publishing Translations (Optional)

```php
public function boot(): void
{
    $this->publishes([
        __DIR__ . '/../Resources/lang' => resource_path('lang/vendor/rma'),
    ], 'rma-translations');
}
```

Users can then run:
```bash
php artisan vendor:publish --tag=rma-translations
```

## DataGrid

### Creating DataGrid

**File:** `packages/Webkul/RMA/src/DataGrids/Admin/ReturnRequestDataGrid.php`

```php
<?php

namespace Webkul\RMA\DataGrids\Admin;

use Illuminate\Support\Facades\DB;
use Webkul\DataGrid\DataGrid;

class ReturnRequestDataGrid extends DataGrid
{
    public function prepareQueryBuilder()
    {
        $queryBuilder = DB::table('rma_requests')
            ->select('id', 'product_name', 'status', 'created_at');

        return $queryBuilder;
    }

    public function prepareColumns()
    {
        $this->addColumn([
            'index' => 'id',
            'label' => trans('rma::app.admin.return-requests.datagrid.id'),
            'type' => 'integer',
            'sortable' => true,
            'filterable' => false,
        ]);

        $this->addColumn([
            'index' => 'product_name',
            'label' => trans('rma::app.admin.return-requests.datagrid.product-name'),
            'type' => 'string',
            'sortable' => true,
            'filterable' => true,
        ]);

        $this->addColumn([
            'index' => 'status',
            'label' => trans('rma::app.admin.return-requests.datagrid.status'),
            'type' => 'string',
            'sortable' => true,
            'filterable' => true,
            'filterable_type' => 'dropdown',
            'filterable_options' => [
                ['label' => 'Pending', 'value' => 'pending'],
                ['label' => 'Approved', 'value' => 'approved'],
                ['label' => 'Rejected', 'value' => 'rejected'],
            ],
            'closure' => function ($row) {
                return "<span class='badge label-info'>" . ucfirst($row->status) . "</span>";
            },
        ]);
    }

    public function prepareActions()
    {
        $this->addAction([
            'icon' => 'icon-view',
            'title' => trans('rma::app.admin.return-requests.datagrid.view'),
            'method' => 'GET',
            'url' => function ($row) {
                return route('admin.rma.return-requests.show', $row->id);
            },
        ]);
    }

    public function prepareMassActions()
    {
        $this->addMassAction([
            'icon' => 'icon-delete',
            'title' => trans('rma::app.admin.return-requests.datagrid.mass-delete'),
            'method' => 'POST',
            'url' => route('admin.rma.return-requests.mass-delete'),
        ]);
    }
}
```

### Column Options

| Option | Purpose |
|--------|---------|
| `index` | Database column name |
| `label` | Column header text |
| `type` | Data type (string, integer, date, etc.) |
| `sortable` | Enable sorting |
| `filterable` | Enable filtering |
| `filterable_type` | Filter type (dropdown, date_range) |
| `closure` | Custom formatting function |

### Using DataGrid in Controller

```php
public function index()
{
    if (request()->ajax()) {
        return datagrid(ReturnRequestDataGrid::class)->process();
    }

    return view('rma::admin.return-requests.index');
}
```

### Displaying DataGrid in View

```blade
<x-admin::datagrid :src="route('admin.rma.return-requests.index')" />
```

## Admin Menu

### Creating Menu Configuration

**File:** `packages/Webkul/RMA/src/Config/admin-menu.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.menu.rma',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 100,
        'icon' => 'icon-rma',
    ],
    [
        'key' => 'rma.return-requests',
        'name' => 'rma::app.admin.menu.return-requests',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
];
```

### Registering Menu

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/admin-menu.php',
    'menu.admin'
);
```

## Access Control List (ACL)

### Creating ACL Configuration

**File:** `packages/Webkul/RMA/src/Config/acl.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.acl.rma',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
    [
        'key' => 'rma.return-requests',
        'name' => 'rma::app.admin.acl.return-requests',
        'route' => 'admin.rma.return-requests.index',
        'sort' => 1,
    ],
    [
        'key' => 'rma.return-requests.view',
        'name' => 'rma::app.admin.acl.view',
        'route' => 'admin.rma.return-requests.show',
        'sort' => 1,
    ],
];
```

### Registering ACL

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/acl.php',
    'acl'
);
```

### Checking Permissions

```php
// In controller
if (! bouncer()->hasPermission('rma')) {
    abort(401, 'Unauthorized access.');
}
```

```blade
<!-- In Blade -->
@if (bouncer()->hasPermission('rma'))
    <!-- Show content -->
@endif
```

## System Configuration

### Creating Configuration

**File:** `packages/Webkul/RMA/src/Config/system.php`

```php
<?php

return [
    [
        'key' => 'rma',
        'name' => 'rma::app.admin.system.rma',
        'info' => 'rma::app.admin.system.rma-info',
        'sort' => 1,
    ],
    [
        'key' => 'rma.settings',
        'name' => 'rma::app.admin.system.general-settings',
        'info' => 'rma::app.admin.system.general-settings-info',
        'icon' => 'settings/settings.svg',
        'sort' => 1,
    ],
    [
        'key' => 'rma.settings.general',
        'name' => 'rma::app.admin.system.rma-configuration',
        'info' => 'rma::app.admin.system.rma-configuration-info',
        'sort' => 1,
        'fields' => [
            [
                'name' => 'enable',
                'title' => 'rma::app.admin.system.enable-rma',
                'type' => 'boolean',
            ],
            [
                'name' => 'allow_partial_returns',
                'title' => 'rma::app.admin.system.allow-partial-returns',
                'type' => 'boolean',
            ],
            [
                'name' => 'max_return_days',
                'title' => 'rma::app.admin.system.max-return-days',
                'type' => 'number',
                'validation' => 'numeric|min:1',
            ],
            [
                'name' => 'default_status',
                'title' => 'rma::app.admin.system.default-status',
                'type' => 'select',
                'options' => [
                    ['title' => 'Pending', 'value' => 'pending'],
                    ['title' => 'Approved', 'value' => 'approved'],
                ],
            ],
        ],
    ],
];
```

### Registering Configuration

In service provider `register()` method:

```php
$this->mergeConfigFrom(
    dirname(__DIR__) . '/Config/system.php',
    'core'
);
```

### Field Types

| Type | Purpose |
|------|---------|
| `text` | Text input |
| `password` | Password input |
| `number` | Numeric input |
| `boolean` | Enable/disable switch |
| `select` | Dropdown select |
| `multiselect` | Multi-select dropdown |
| `textarea` | Text area |
| `editor` | Rich text editor (TinyMCE) |
| `image` | Image upload |
| `file` | File upload |
| `country` | Country dropdown |
| `state` | State dropdown (depends on country) |
| `color` | Color picker |

### Dependent Fields

```php
[
    'name' => 'enable_policy',
    'title' => 'Enable Return Policy',
    'type' => 'boolean',
], [
    'name' => 'max_return_days',
    'title' => 'Maximum Return Days',
    'type' => 'number',
    'depends' => 'enable_policy:1',  // Show only when enable_policy is 1
],
```

### Using Configuration Values

```php
// In controller
$isEnabled = core()->getConfigData('rma.settings.general.enable');
$maxDays = core()->getConfigData('rma.settings.general.max_return_days');
```

```blade
<!-- In Blade -->
@if (core()->getConfigData('rma.settings.general.enable'))
    <!-- Show RMA content -->
@endif
```

---

# Key Files Reference

| File | Purpose |
|------|---------|
| `src/Providers/ServiceProvider.php` | Main service provider |
| `src/Providers/ModuleServiceProvider.php` | Concord model registration |
| `src/manifest.php` | Package metadata |
| `src/Database/Migrations/` | Migration files |
| `src/Contracts/` | Model contract interfaces |
| `src/Models/` | Eloquent models |
| `src/Models/*Proxy.php` | Concord model proxies |
| `src/Repositories/` | Repository classes |
| `src/Routes/admin-routes.php` | Admin routes |
| `src/Routes/shop-routes.php` | Shop routes |
| `src/Http/Controllers/` | Controllers |
| `src/Resources/views/` | Blade templates |
| `src/Resources/lang/` | Translation files |
| `src/DataGrids/Admin/` | DataGrid classes |
| `src/Config/admin-menu.php` | Menu configuration |
| `src/Config/acl.php` | ACL permissions |
| `src/Config/system.php` | System configuration |

## Common Pitfalls

- Forgetting to run `composer dump-autoload` after adding package
- Not registering service provider in `bootstrap/providers.php`
- Not clearing cache after changes
- Incorrect namespace in PSR-4 autoloading
- Not using package prefix for table names
- Not registering models in ModuleServiceProvider
- Not merging config in service provider
- Using hardcoded text instead of translation keys
- Not checking permissions in controllers/views
