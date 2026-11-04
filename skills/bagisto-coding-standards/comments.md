# Comments and docblocks

The single authority for every comment in this codebase — PHP, Blade, JS and
CSS. `vendor/bin/pint` enforces none of it.

## Contents

- [The bar](#the-bar)
- [Every method gets a docblock](#every-method-gets-a-docblock)
- [Every property gets a docblock too](#every-property-gets-a-docblock-too)
- [No docblock above the class](#no-docblock-above-the-class)
- [Comment only what the code cannot say](#comment-only-what-the-code-cannot-say)
- [Syntax per layer](#syntax-per-layer)

## The bar

**No comments inside a method body, an array literal or a route group — not even a one-line "why".** In code, the only comment this codebase wants is the docblock above a method, a property or a constant. **Not above the class.**

A genuinely non-obvious reason belongs in that docblock or in the commit message. If a line needs prose to be followed, that is the signal to extract a well-named method, not to annotate it.

This holds in PHP, JavaScript and Vue alike, including the `<script>` of a Blade file. **Markup is different:** it takes HTML arrow comments, `<!-- -->`, as [Syntax per layer](#syntax-per-layer) describes.

## Every method gets a docblock

No exceptions, and regardless of visibility — `public`, `protected`, and `private` alike. A method
without one is incomplete, even when its name seems to say everything.

The description is a **sentence**: capitalised, ending in a full stop. **One line is the norm, two is
the hard ceiling** — a docblock is a label, not an explanation. If what you want to say does not fit
in two lines, it is not docblock material: cut it, or put it in the commit message.

The same ceiling applies to a property, a constant, a Blade `@php` closure and a Vue
`method`/`computed` — every layer, no exceptions.

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

## No docblock above the class

A class, interface, trait or enum carries **no docblock at all**. The declaration and the members
below it say what it is; a preamble above it is noise the codebase does not use.

This is not a preference — it is what the code does. Across `Product`, `Admin/Http/Controllers`,
`Checkout`, `Core` and `Sales`, **462 of 468 classes have no class docblock (98.7%)**. The handful
that do are the outliers, not the pattern.

```php
namespace Webkul\Marketplace\Services;

use Webkul\Marketplace\Contracts\Carrier;

class FulfilmentBooker
{
    /**
     * Buy the label and book the collection for a saved shipment.
     */
    public function book(Shipment $shipment): array
```

```php
/**
 * Drives a carrier for a saved shipment: buys the label, books the collection, and returns
 * the values to write back onto the shipment.
 */                              ← delete it; the class needs no preamble
class FulfilmentBooker
```

Where does the "why" go, then? A genuine constraint goes in the **docblock of the method it applies to**, as "Comment only what the code cannot say" below describes. Anything larger (history, what this replaced, why an earlier approach was wrong) belongs in the commit message or the PR.

## Comment only what the code cannot say

The rule above says where a docblock goes. This one says when a **reason** earns a place in it, because explanation is where over-commenting accumulates.

Inside a method body there is **no comment**. Older code still has some, which is debt rather than a pattern to copy. A reason belongs in the method's docblock when a reader who understands the code would still act wrongly without it, almost always because the code encodes a **constraint that is invisible locally**:

- A line that looks removable or simplifiable but is load-bearing (a join deliberately kept out of
  a base query, a filter written as a negation for a reason).
- A non-obvious ordering, compatibility, or migration concern.
- A workaround for behaviour in core, Laravel, or a third-party service.

```php
/**
 * Join the variants for these filters only, because the `or` in the condition is not indexable
 * and MySQL would scan the whole products table per candidate row.
 */
protected function joinVariants($qb)
{
    $qb->leftJoin('products as variants', function ($join) {
        $join->on('variants.parent_id', '=', 'products.id')
            ->orOn('variants.id', '=', 'products.id');
    });
}
```

Do **not** explain code that already reads clearly, wherever the comment sits. These are all noise:

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

Keep what you do write within the two-line ceiling. A paragraph explaining a symptom in detail belongs in the commit message or the PR. State the constraint, not the war story.

---

## Syntax per layer

When a comment *is* warranted, its form depends on which layer it sits in.

Two rules from the **bagisto-package-development** skill govern Blade too, and they pull in opposite directions — apply both:

- **"Every method gets a docblock"** — a Vue `method` or `computed` in a `<script>` block is a method. It gets a `/** … */` describing what it does, as a capitalised sentence ending in a full stop. Same for any function inside an `@php` block.
- **"Comment only what the code cannot say"** — *inside* a method body there is no comment, and a reason goes in the docblock. In the markup a comment labels a section or states a reason the markup cannot say; skip anything that merely restates it.

What follows is the syntax to use for each layer.

Each comment syntax belongs to its own layer — pick by *where* the comment sits, then follow the casing/punctuation rule for that layer.

- **HTML `<!-- -->`** — the comment form for markup, anywhere in a Blade file. Across the Admin and Shop views it outnumbers `{{-- --}}` about 100 to 1 (3,943 lines to 36), so it is the default, and an existing one is never converted.
  - A **section label** is short and in **Title Case**, with no trailing period (3,606 labels to 322). Mirror the heading the block renders; a `?` on a question is fine:
    ```blade
    <!-- What kind of product? -->
    <!-- Attribute Family (Searchable) -->
    <!-- SKU -->
    ```
  - A **reason** is a sentence with a capital and terminal punctuation, on one line or as a multi-line block, and it stays an arrow comment. Leave the wording of an existing one alone, because shortening it to a label loses the reason:
    ```blade
    <!-- Use Teleport to move the modal to the body. -->

    <!--
        Kept outside of the drawer, which is only rendered while open, so that the
        metadata is submitted with the form whether the drawer was opened or not.
    -->
    ```

- **Blade `{{-- --}}`** — rare, for a note that must not reach the browser, such as one about the `@php` block below it. Follow the same casing and punctuation as an arrow comment.
  - **Not inside `@php … @endphp`.** Blade does not strip its own comment there — it copies it verbatim into the compiled PHP, producing a parse error. Inside an `@php` block you are writing plain PHP, so use PHP comment syntax and the PHP conventions that go with it; put a `{{-- --}}` header *above* the block if the whole block needs explaining:
    ```blade
    {{-- Everything the wizard needs to describe its steps. --}}
    @php
        // The upload-size config is stored in MB; VeeValidate's size rule expects KB.
        $maxUploadKb = $maxUploadMb * 1024;
    @endphp
    ```

- **JS `/** … */` (JSDoc block)** — inside `<script>`. This is the **only** comment form used in the Vue layer — **no `//` line comments**. Every `computed`/`method` gets one, as a capitalized sentence ending in a full stop, **at most two lines** — the same ceiling as PHP. Older views mostly lack them (794 of 1,075), which is debt rather than convention, so add them in a file you touch. Lifecycle hooks and watchers do not take one (163 of 163 hooks and 28 of 29 watchers have none). Statements *inside* a method get none either, so a reason goes here:
  ```js
  /**
   * The axis checkboxes only appear for a variable kind, once the seller has said "yes"
   * and picked a family.
   */
  showAxes() {
      return this.isVariable && this.hasVariations === true && !! this.familyId;
  }
  ```
  A trivial one-liner still gets its docblock — but keep it to the one sentence, and don't pile extra commentary onto statements that already read clearly. A three-line JSDoc describing how a method fits into the wider flow is over the ceiling: state what it returns and stop.

- **CSS `/** … */` (JSDoc block)** — inside `<style>`, same form as JS: describe *why* a rule exists (especially non-obvious ones like `:checked`-driven state or scrollbar hiding), as a punctuated sentence:
  ```css
  /**
   * Hide the navigation radios; they only drive the :checked state.
   */
  #rma-steps .rma-step-radio { … }
  ```

Rule of thumb: **sentence → capitalized + punctuated; bare title/label → Title Case, no period.** In markup use `<!-- -->`. In `<script>`/`<style>` always use the `/** … */` block form, never `//` or bare `/* */`.
