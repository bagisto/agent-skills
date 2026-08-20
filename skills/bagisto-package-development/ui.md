# UI Layer — Routes, Controllers, Views

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

> **Writing the Blade itself?** The **bagisto-coding-standards** skill carries the markup rules —
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
