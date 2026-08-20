# Comments and docblocks

The single authority for every comment in this codebase — PHP, Blade, JS and
CSS. `vendor/bin/pint` enforces none of it.

## Contents

- [The bar](#the-bar)
- [Every method gets a docblock](#every-method-gets-a-docblock)
- [Every property gets a docblock too](#every-property-gets-a-docblock-too)
- [A class docblock defines; it does not narrate](#a-class-docblock-defines-it-does-not-narrate)
- [Comment only what the code cannot say](#comment-only-what-the-code-cannot-say)
- [Syntax per layer](#syntax-per-layer)

## The bar

**No comments inside a method body, an array literal, a route group or
markup — not even a one-line "why".** The only comment this codebase wants is
the docblock above a class, method or property.

A genuinely non-obvious reason belongs in that docblock or in the commit
message. If a line needs prose to be followed, that is the signal to extract a
well-named method, not to annotate it.

This holds in PHP, Blade, JavaScript and Vue alike.

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

## Syntax per layer

When a comment *is* warranted, its form depends on which layer it sits in.

Two rules from the **package-development** skill govern Blade too, and they pull in opposite directions — apply both:

- **"Every method gets a docblock"** — a Vue `method` or `computed` in a `<script>` block is a method. It gets a `/** … */` describing what it does, as a capitalised sentence ending in a full stop. Same for any function inside an `@php` block.
- **"Comment only what the code cannot say"** — *inside* a method body, and in the markup, the default is no comment. Explain a constraint that is invisible locally, a workaround, or a line that looks removable but is load-bearing; skip anything that merely restates the markup or the call.

What follows is the syntax to use for each layer.

Each comment syntax belongs to its own layer — pick by *where* the comment sits, then follow the casing/punctuation rule for that layer.

- **Blade `{{-- --}}`** — for Blade/PHP-level notes (file headers, `@php` logic, control-flow explanations). Never ships to the browser.
  - If the comment is a **sentence** (or sentences), write it as prose with a **capital first letter and terminal punctuation**. Multi-line headers explain *what the view is and why*:
    ```blade
    {{--
        The friendly "What kind of product?" create funnel (stepped scratch page only). It maps a
        plain kind + a "Does it have variations?" answer to a Bagisto product type behind the scenes.
    --}}
    ```
  - If it is a **short label/title** (not a sentence), use **Title Case** with no trailing period: `{{-- Media --}}`, `{{-- Type-Specific Controls --}}`.
  - **Not inside `@php … @endphp`.** Blade does not strip its own comment there — it copies it verbatim into the compiled PHP, producing a parse error. Inside an `@php` block you are writing plain PHP, so use PHP comment syntax and the PHP conventions that go with it; put a `{{-- --}}` header *above* the block if the whole block needs explaining:
    ```blade
    {{-- Everything the wizard needs to describe its steps. --}}
    @php
        // The upload-size config is stored in MB; VeeValidate's size rule expects KB.
        $maxUploadKb = $maxUploadMb * 1024;
    @endphp
    ```

- **HTML `<!-- -->`** — section dividers *inside* an x-template / markup. Keep them short: a **Title-Cased** label or a natural question — mirror the heading the block renders. No trailing period on labels; a `?` on a question is fine:
  ```blade
  <!-- What kind of product? -->
  <!-- Attribute Family (Searchable) -->
  <!-- SKU -->
  ```

- **JS `/** … */` (JSDoc block)** — inside `<script>`. This is the **only** comment form used in the Vue layer — **no `//` line comments**. Every `computed`/`method` gets one, as a capitalized sentence ending in a full stop. Statements *inside* a method get one only when genuinely non-obvious:
  ```js
  /**
   * The axis checkboxes only appear for a variable kind, once the seller has said "yes"
   * and picked a family.
   */
  showAxes() {
      return this.isVariable && this.hasVariations === true && !! this.familyId;
  }
  ```
  A trivial one-liner still gets its docblock — but keep it to the one sentence, and don't pile extra commentary onto statements that already read clearly.

- **CSS `/** … */` (JSDoc block)** — inside `<style>`, same form as JS: describe *why* a rule exists (especially non-obvious ones like `:checked`-driven state or scrollbar hiding), as a punctuated sentence:
  ```css
  /**
   * Hide the navigation radios; they only drive the :checked state.
   */
  #rma-steps .rma-step-radio { … }
  ```

Rule of thumb: **sentence → capitalized + punctuated; bare title/label → Title Case, no period.** In `<script>`/`<style>` always use the `/** … */` block form, never `//` or bare `/* */`.
