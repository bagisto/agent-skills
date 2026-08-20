# Actions, mass actions and export

## Contents

- [Row actions](#row-actions)
- [Mass actions](#mass-actions)
- [The controller side](#the-controller-side)
- [ACL is the whole story](#acl-is-the-whole-story)
- [Export](#export)

## Row actions

One entry per action, added in `prepareActions()`. `url` is a closure receiving
the row, so it can build a route from any column in the select list:

```php
$this->addAction([
    'index'  => 'edit',
    'icon'   => 'icon-edit',
    'title'  => trans('admin::app.settings.currencies.index.datagrid.edit'),
    'method' => 'GET',
    'url'    => fn ($row) => route('admin.settings.currencies.edit', $row->id),
]);
```

| Key | Notes |
|---|---|
| `index` | Short identifier, `edit` / `delete` / `view` |
| `icon` | An icon-font class — `icon-edit`, `icon-delete`, `icon-view` |
| `title` | Tooltip; always `trans()` |
| `method` | `GET` for navigation, `DELETE` for destructive, `POST` otherwise |
| `url` | Closure taking the row |

The closure reads the row **as the query aliased it**. On a joined grid with
`$primaryColumn = 'currency_exchange_id'`, `$row->id` is undefined — use the
alias.

## Mass actions

Added in `prepareMassActions()`. They act on the checkbox selection, so they get
a plain `url`, not a closure:

```php
$this->addMassAction([
    'title'  => trans('admin::app.customers.customers.index.datagrid.delete'),
    'method' => 'POST',
    'url'    => route('admin.customers.customers.mass_delete'),
]);
```

A mass action that sets a value carries `options`, which render as a second
dropdown once rows are selected:

```php
$this->addMassAction([
    'title'   => trans('…update-status'),
    'method'  => 'POST',
    'url'     => route('admin.customers.customers.mass_update'),
    'options' => [
        ['label' => trans('…active'),   'value' => 1],
        ['label' => trans('…inactive'), 'value' => 0],
    ],
]);
```

## The controller side

The grid posts the selection as `indices`, plus `value` when the action has
options. Name the routes `mass_delete` / `mass_update` and the methods
`massDestroy` / `massUpdate`, matching the rest of the codebase:

```php
Route::post('mass-delete', 'massDestroy')->name('admin.customers.customers.mass_delete');
Route::post('mass-update', 'massUpdate')->name('admin.customers.customers.mass_update');
```

```php
public function massDestroy(MassDestroyRequest $massDestroyRequest): JsonResponse
{
    $indices = $massDestroyRequest->input('indices');

    try {
        foreach ($indices as $index) {
            Event::dispatch('customer.review.delete.before', $index);

            $this->productReviewRepository->delete($index);

            Event::dispatch('customer.review.delete.after', $index);
        }
        // …
    }
}
```

Three things this shows that are easy to miss:

- **Validate through a FormRequest** (`MassDestroyRequest`), never by reading
  `request()->input('indices')` unchecked — the ids arrive from the browser.
- **Fire the same before/after events the single-record path fires.** A mass
  delete that skips them silently bypasses every listener, including cache
  invalidation.
- **Go through the repository**, not the model or the query builder. The grid's
  own query builder is the only sanctioned `DB::` usage.

## ACL is the whole story

Every action and mass action is wrapped:

```php
if (bouncer()->hasPermission('settings.currencies.delete')) {
    $this->addAction([...]);
}
```

The wrapper hides the control. It does **not** protect the endpoint — that is
the route's ACL entry and the controller's own check. A grid action gated in the
DataGrid but not on the route is reachable by anyone who can guess the URL.

When adding an action, confirm all three:

1. The `bouncer()` wrapper in the DataGrid, so the control renders for the right
   roles.
2. An entry in the package's `Config/acl.php` for the route.
3. The permission key exists and is spelled identically in both places.

## Export

Export is opt-in per grid:

```php
protected bool $exportable = true;
```

`setExportFileName()` sets the base name and `setExportFileExtension()` the
extension (default `csv`). Any column whose value is markup should carry
`'exportable' => false` — `DataGridExport` filters on that flag for both the
headings and the mapped values, so a closure returning an `<a>` tag otherwise
lands in the spreadsheet as raw HTML.

Export is a `Maatwebsite\Excel` `FromQuery` job whose `query()` returns the
grid's own builder — the filters the user applied, with paging removed. A grid
over a large table therefore exports the whole filtered table. Before enabling
it on a high-volume grid, check that the query is indexed for the default sort
and that no closure performs a per-row lookup, since both run once per exported
row rather than once per page.
