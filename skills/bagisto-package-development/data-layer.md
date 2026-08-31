# Data Layer — Migrations, Models, Repositories

> **The `Webkul/RMA` + `ReturnRequest` names below are a worked example, not a
> citation.** A real `RMA` package exists in the checkout, but it is built around
> `RMA`, `RMAItem` and `RMAStatus` and has no `Contracts/ReturnRequest.php`,
> `Config/` or `Routes/` directory. Read these paths as the ones *you* will
> create; for a pattern to copy from, open an actual package such as
> `packages/Webkul/CartRule` or `packages/Webkul/Category`.

## Migrations

### Creating Migrations

The `package:make-*` commands come from `bagisto/bagisto-package-generator`,
which is **not** a dependency of either Bagisto line — install it first
(see [core.md](core.md)) or use the plain Laravel command beneath.

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
