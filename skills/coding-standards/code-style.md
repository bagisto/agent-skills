# PHP Code Style

`vendor/bin/pint` fixes most formatting, so run it and trust it. The rules below are the ones Pint
does **not** enforce — they have to be written by hand, and they apply to every PHP file in a
package (controllers, repositories, models, DataGrids, enums, listeners, jobs).

These rules cover `.php` files, and they apply just as much to PHP written inside an `@php … @endphp`
block in a Blade file — Pint cannot reach a `.blade.php`, so there you apply them by hand. Blade's own
layer (`@props`, directive arguments, markup) has its own conventions: see the **coding-standards**
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

## Comments and docblocks

Owned by [comments.md](comments.md) — the bar, the docblock contract for
methods, properties and classes, and the syntax for each layer.
