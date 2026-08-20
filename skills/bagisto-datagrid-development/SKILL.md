---
name: bagisto-datagrid-development
description: Use when building or changing a Bagisto admin listing page — a DataGrid class with columns, search, filters, sorting, row actions, mass actions or export, and the controller and Blade view that render it. Trigger phrases include "datagrid", "admin listing", "add a column", "mass action", "prepareQueryBuilder", "listing page", "grid filter", "export grid".
requires: bagisto-coding-standards
---

# DataGrid Development

An admin listing page is a `DataGrid` subclass plus three lines of wiring. The
engine (`packages/Webkul/DataGrid`) owns paging, search, filtering, sorting,
saved filters and export; the subclass supplies a query and describes its
columns. There are 51 of them in the codebase — copy the closest one rather than
inventing a shape.

## The four methods

`Webkul\DataGrid\DataGrid` declares two abstract methods and two optional hooks:

| Method | Required | Purpose |
|---|---|---|
| `prepareQueryBuilder()` | yes | Return a **query builder**, not a collection |
| `prepareColumns()` | yes | `addColumn([...])` per column |
| `prepareActions()` | no | Per-row actions, each ACL-gated |
| `prepareMassActions()` | no | Checkbox actions, each ACL-gated |

Tunable properties, overridden only when the default is wrong: `$primaryColumn`
(default `'id'`), `$sortColumn`, `$sortOrder` (`'desc'`), `$itemsPerPage` (10),
`$perPageOptions`.

## The shape

```php
class CurrencyDataGrid extends DataGrid
{
    /**
     * Prepare query builder.
     *
     * @return Builder
     */
    public function prepareQueryBuilder()
    {
        return DB::table('currencies')
            ->select('id', 'name', 'code');
    }

    /**
     * Add Columns.
     *
     * @return void
     */
    public function prepareColumns()
    {
        $this->addColumn([
            'index'      => 'name',
            'label'      => trans('admin::app.settings.currencies.index.datagrid.name'),
            'type'       => 'string',
            'searchable' => true,
            'filterable' => true,
            'sortable'   => true,
        ]);
    }

    /**
     * Prepare actions.
     *
     * @return void
     */
    public function prepareActions()
    {
        if (bouncer()->hasPermission('settings.currencies.edit')) {
            $this->addAction([
                'index'  => 'edit',
                'icon'   => 'icon-edit',
                'title'  => trans('admin::app.settings.currencies.index.datagrid.edit'),
                'method' => 'GET',
                'url'    => fn ($row) => route('admin.settings.currencies.edit', $row->id),
            ]);
        }
    }
}
```

Align the `=>` inside an `addColumn`/`addAction` array only if the file you are
editing already does; Pint does not enforce alignment either way, and the
codebase has both.

## Wiring

The controller serves JSON on an AJAX hit and the view otherwise — one route,
two responses:

```php
public function index()
{
    if (request()->ajax()) {
        return datagrid(CurrencyDataGrid::class)->process();
    }

    return view('admin::settings.currencies.index');
}
```

The Blade side is one tag pointing at that same route:

```blade
<x-admin::datagrid :src="route('admin.settings.currencies.index')" />
```

`datagrid()` throws `InvalidDataGridException` unless the class extends
`DataGrid`, so the class name is the only contract.

## Reference files

| File | Load when |
|---|---|
| [columns.md](columns.md) | Column types, search/filter/sort flags, dropdown options, closures, joins and `addFilter` |
| [actions.md](actions.md) | Row actions, mass actions, ACL gating, export |

## Non-negotiables

- **`prepareQueryBuilder()` returns a builder.** Calling `->get()`, `->paginate()`
  or mapping to a collection breaks paging, filtering and export, because the
  engine appends to the query you return.
- **The query builder is the one place `DB::` is expected.** Everywhere else in
  Bagisto goes through a repository; a DataGrid is built on the query builder by
  design.
- **Every action and mass action is wrapped in `bouncer()->hasPermission(...)`.**
  An ungated action renders for admins who cannot perform it, and the grid is
  the most common place this is forgotten.
- **Every `label` goes through `trans()`**, with the key added to all 22 locales.
- **A joined query needs `addFilter()` for every aliased column** — see
  [columns.md](columns.md). Without it, filtering and sorting on that column
  produce an ambiguous-column SQL error.
- **Escape whatever a closure interpolates.** Cells render through `v-html`.
  The engine strips tags from raw values first, but not quotes — so a value
  placed inside an attribute can break out. See [columns.md](columns.md).

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
