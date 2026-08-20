# How values are stored and resolved

## Contents

- [The value table](#the-value-table)
- [Reading a value](#reading-a-value)
- [Writing a value](#writing-a-value)
- [The flat index](#the-flat-index)
- [Debugging a missing value](#debugging-a-missing-value)

## The value table

`product_attribute_values` holds one row per attribute, per product, per scope:

| Column | Holds |
|---|---|
| `product_id`, `attribute_id` | what the value belongs to |
| `channel`, `locale` | its scope; null when the attribute is not scoped that way |
| `text_value`, `integer_value`, `float_value`, `boolean_value`, `date_value`, `datetime_value` | the value, in exactly one of these |
| `unique_id` | `channel\|locale\|product_id\|attribute_id`, kept unique |

Only one value column is used per row — the one
`Attribute::$attributeTypeFields` maps the attribute's `type` to, exposed as
`$attribute->column_name`:

```php
protected function getColumnNameAttribute()
{
    return $this->attributeTypeFields[$this->type];
}
```

A unique index on `(channel, locale, attribute_id, product_id)` guarantees one
row per scope, so a write with the wrong scope fails loudly rather than
duplicating.

## Reading a value

`Product::getCustomAttributeValue($attribute)` is the entry point, and it does
three things worth knowing:

1. **Resolves the scope** from the request —
   `core()->getRequestedLocaleCodeInRequestedChannel()` and
   `core()->getRequestedChannelCode()` — not from the application locale.
2. **Branches on the two flags**, looking for a row matching channel and locale,
   channel only, locale only, or neither.
3. **Falls back to the default** channel and locale when the requested row's
   value column is empty, so a product with no French name shows the English one
   rather than a blank.

Because the lookup is over `$this->attribute_values`, reading many attributes on
many products without eager loading is an N+1. Load the relation before a loop:

```php
$products->load('attribute_values');
```

## Writing a value

Go through `ProductAttributeValueRepository`. It normalises the payload before
saving, and two of those normalisations are easy to reimplement wrongly:

```php
if (in_array($attribute->type, ['multiselect', 'checkbox'])) {
    $data[$attribute->code] = implode(',', $data[$attribute->code] ?? []);
}
```

- **`multiselect` and `checkbox` are stored comma-separated in `text_value`** —
  a joined string of option ids, not JSON and not a relation.
- **`boolean` is coerced** from presence, so an unchecked box saves `false`
  rather than being skipped.
- **`select` stores a single option id in `integer_value`** — the id, never the
  label. Comparing against a label always fails.

Writing the value table directly bypasses all of this and produces rows the rest
of the system cannot read.

## The flat index

Reading EAV per product is too slow for listings, so attributes are denormalised
into `product_flat` — one row per product per locale per channel, with a column
per attribute.

`Helpers\Indexers\Flat` builds it, and it only fills columns that already exist
on the table:

```php
$this->flatColumns = Schema::getColumnListing('product_flat');
// …
! in_array($attribute->code, $this->flatColumns)
```

So an attribute is denormalised **only if `product_flat` has a column of the
same name**. A new filterable attribute needs a migration adding that column;
without it the indexer skips it silently and the attribute never filters or
sorts in a listing.

After any change affecting listings, reindex:

```bash
php artisan indexer:index --mode=full
```

Until it runs, the admin grid and storefront read stale values — which reads as
"my change did nothing".

## Debugging a missing value

In order; the cause is nearly always one of the first three.

1. **Wrong scope.** Check `value_per_locale` and `value_per_channel` on the
   attribute, then look for the row: is there one for the channel and locale you
   are reading in? A value saved against the default locale is invisible on
   another one unless the fallback applies.
2. **Wrong column.** `select` written into `text_value` reads back null from
   `integer_value`. Confirm with `$attribute->column_name`.
3. **Stale flat index.** The value is in `product_attribute_values` but the
   listing shows the old one — reindex.
4. **Missing flat column.** A filterable attribute that never filters usually
   has no `product_flat` column.
5. **Option id versus label.** A `select` comparison against the label finds
   nothing; compare against the option id.
6. **The family.** An attribute not in the product's family is not on its form
   at all, so nothing was ever saved.
