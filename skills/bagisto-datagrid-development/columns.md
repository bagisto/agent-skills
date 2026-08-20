# Columns, filters and the query

## Contents

- [The column array](#the-column-array)
- [Types](#types)
- [Search, filter, sort](#search-filter-sort)
- [Dropdown filters](#dropdown-filters)
- [Date and datetime ranges](#date-and-datetime-ranges)
- [Closures](#closures)
- [Escaping](#escaping-what-the-engine-protects-and-what-it-does-not)
- [Joins and `addFilter`](#joins-and-addfilter)
- [Excluding a column from export](#excluding-a-column-from-export)

## The column array

```php
$this->addColumn([
    'index'      => 'name',        // the select alias this column reads
    'label'      => trans('…'),    // always translated
    'type'       => 'string',
    'searchable' => true,
    'filterable' => true,
    'sortable'   => true,
]);
```

`index` must match the alias in the select list, not the underlying table
column. When the two differ, filtering and sorting need `addFilter()` — see
below.

## Types

`Webkul\DataGrid\Enums\ColumnTypeEnum` defines exactly seven, each with a
handler in `ColumnTypes/`:

| Type | Use for |
|---|---|
| `string` | text |
| `integer` | whole numbers |
| `decimal` | money and rates — formats to the channel's currency |
| `boolean` | flags; renders as a yes/no filter |
| `date` | dates, with a date-range filter |
| `datetime` | timestamps, with a datetime-range filter |
| `aggregate` | a `SUM`/`COUNT` produced by the query |

An unrecognised type throws `InvalidColumnTypeException`. Pick the type by what
the value *is*, not by how you want it displayed — display is the closure's job.

## Search, filter, sort

The three flags are independent and each has a cost:

- **`searchable`** — the column joins the grid's free-text search. Set it only
  on columns a human would type into (name, SKU, email). Every searchable column
  widens the `LIKE` fan-out on every keystroke.
- **`filterable`** — the column gets its own filter control.
- **`sortable`** — the column header becomes clickable.

Never set `searchable` on a `decimal`, `date` or `boolean` column; free-text
search over them matches nothing useful and costs a scan.

## Dropdown filters

For a closed set of values, declare the options rather than leaving a free-text
box:

```php
$this->addColumn([
    'index'              => 'status',
    'label'              => trans('…'),
    'type'               => 'string',
    'filterable'         => true,
    'filterable_type'    => 'dropdown',
    'filterable_options' => [
        ['label' => trans('…processing'), 'value' => Order::STATUS_PROCESSING],
        ['label' => trans('…completed'),  'value' => Order::STATUS_COMPLETED],
    ],
]);
```

Options may be built at runtime from a repository or a core helper:

```php
'filterable_options' => core()->getAllChannels()
    ->map(fn ($channel) => ['label' => $channel->name, 'value' => $channel->id])
    ->values()
    ->toArray(),
```

`FilterTypeEnum` allows `dropdown`, `date_range` and `datetime_range`.

## Date and datetime ranges

A `date` or `datetime` column is given a range filter automatically — do not
hand-roll two columns for "from" and "to". `DateRangeOptionEnum` supplies the
presets (today, this week, this month, and so on).

## Closures

A closure rewrites the value for display. It receives the **whole row**, not the
single value, so it can combine columns:

```php
'closure' => function ($row) {
    return empty($row->state) ? '*' : $row->state;
},
```

The engine assigns the result back onto the record:
`$record->{$column->getIndex()} = $closure($record)`.

Two consequences worth knowing:

- **A closure runs after the query**, so it cannot help filtering or sorting.
  Sorting still uses the raw SQL value. If users must sort by the displayed
  form, compute it in the query instead.
- **A closure runs per row**, so a repository call inside one is an N+1 across
  the page. Join or eager-load in `prepareQueryBuilder()` instead.

## Escaping: what the engine protects, and what it does not

`components/datagrid/table.blade.php` renders each cell with:

```blade
v-html="record[column.index]"
```

So a column's value reaches the DOM as HTML. Two things already stand between
that and an injection, and knowing them tells you where the real risk is:

- **`DataGrid::sanitizeRow()` runs `strip_tags()` over every string value
  before the closures run.** An injected `<img onerror=…>` in a raw column value
  never survives.
- **Filter options render through `v-text`**, so `filterable_options` are
  escaped by Vue even though they carry raw values.

What `strip_tags()` does **not** remove is quotes. So the remaining hole is a
closure that interpolates a value **into an attribute**, where a surviving quote
closes it and opens an event handler:

```php
// Vulnerable — a colour of  red" onmouseover="alert(1)  breaks out
'closure' => fn ($row) => '<p style="background: '.$row->color.';">'.$row->color.'</p>',

// Safe
'closure' => fn ($row) => '<p style="background: '.e($row->color).';">'.e($row->color).'</p>',
```

`strip_tags('red" onmouseover="alert(1)')` returns the string unchanged — there
are no tags in it — and the result renders as
`<p style="background: red" onmouseover="alert(1);">`.

The rule: **escape with `e()` any value a closure interpolates**, and treat an
attribute as the dangerous position. A closure returning only `trans()` output
or an integer id needs nothing.

## Joins and `addFilter`

When the query joins, the select list is aliased and the grid's `index` no
longer matches a real SQL column. Register the mapping in the same method:

```php
public function prepareQueryBuilder()
{
    $queryBuilder = DB::table('currency_exchange_rates')
        ->leftJoin('currencies', 'currency_exchange_rates.target_currency', '=', 'currencies.id')
        ->select(
            'currency_exchange_rates.id as currency_exchange_id',
            'currencies.name as currency_name',
        );

    $this->addFilter('currency_exchange_id', 'currency_exchange_rates.id');
    $this->addFilter('currency_name', 'currencies.name');

    return $queryBuilder;
}
```

Set `$primaryColumn` too when the identifier is aliased — the default is `'id'`,
which no longer exists in the result set:

```php
protected $primaryColumn = 'currency_exchange_id';
```

Skipping either step produces an ambiguous-column or unknown-column SQL error
the moment someone filters or sorts, not when the page first loads — which is
why it survives a casual manual check.

## Excluding a column from export

```php
'exportable' => false,
```

Set it on columns whose value is markup or an action link; a closure that
returns an `<a>` tag exports as raw HTML into the spreadsheet otherwise.
