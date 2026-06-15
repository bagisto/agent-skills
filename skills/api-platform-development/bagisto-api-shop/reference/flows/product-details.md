# Product details flow

The product detail page (PDP) — the single highest-intent screen in the storefront. It does two jobs: **present** the product (gallery, copy, price, reviews) and **configure** it (let the shopper pick variant / bundle / grouped / downloadable / booking options) so it can be added to the cart. **The option IDs that add-to-cart needs are discovered here** — the PDP is where selection happens, add-to-cart just submits the result.

> **Source of truth for exact shapes:** this page gives you the flow, endpoints, and UX. For the precise embedded structure of a product (variants, super-attributes, bundle options, slot config…), open the linked api-docs page. **Never invent the option shape from memory — open the detail page and read what the product actually embeds.**

- **Auth:** the product read is **public** (`X-STOREFRONT-KEY` only). Wishlist/compare buttons need a customer Bearer; add-to-cart needs a cart or customer Bearer (see add-to-cart).
- **One fetch, no follow-ups for the core PDP:** the single-product call embeds categories, channels, variants, super-attributes, bundle options, grouped products, downloadable links, and booking slot config inline. You generally don't need extra round-trips to render the page or build the add-to-cart body.

---

## 1. Flow architecture & structure

```
  arrive from listing (product id)         (see product-listing.md)
        │
        ▼
  ┌──────────────────────────────────────────────────────────┐
  │  GET /api/shop/products/{id}   ── the whole PDP document   │
  │  embeds: categories · channels · variants · superAttributes│
  │          bundleOptions · groupedProducts                   │
  │          downloadableLinks/Samples · bookingProducts(slots) │
  └──────────────────────────────────────────────────────────┘
        │ branch on product.type
        ▼
  ┌─────────────┬──────────────┬───────────┬───────────────┬──────────────┐
  │ simple/     │ configurable │ bundle    │ grouped       │ downloadable  │
  │ virtual     │ pick variant │ pick      │ pick member   │ pick link(s)  │
  │ (no options)│ via super-   │ option    │ qtys          │               │
  │             │ attributes   │ products  │               │               │
  └─────────────┴──────────────┴───────────┴───────────────┴──────────────┘
        │           booking → GET /api/shop/booking-slots (runtime availability for a date)
        ▼
  selection complete ──▶ add-to-cart.md   (the picked IDs become the add body)
        │
        ├─ reviews summary ──▶ features/reviews.md
        ├─ wishlist / compare buttons ──▶ features/wishlist.md · features/compare.md
        └─ related / cross-sell rail ──▶ product cards (product-listing.md)
```

**Recommended client architecture**

- **Routing** — `/product/[slug]` or `/products/[id]`. Server-render the PDP (SEO, social cards, perceived speed) using the single-product fetch; hydrate the interactive selectors client-side.
- **State** — a small per-PDP selection store: the chosen variant (or selected super-attribute options), bundle option selections, grouped-member quantities, picked downloadable links, or the chosen booking slot — plus a derived "can add to cart?" flag and the resolved price/stock for the current selection.
- **Data layer** — one query for the product (keyed by id); a **separate, on-demand query for booking slots** keyed by `bookingProductId` + date (availability is date-specific and must be live). Variants/options come embedded — don't refetch them.
- **Derived price/stock** — recompute the displayed price and saleability from the current selection (e.g. the chosen variant's price), not from the parent alone.

---

## 2. Per-type option discovery (the core of the PDP)

Branch on `product.type`. Each type stores the IDs add-to-cart will need in a different embedded block:

| Type | What the shopper picks | Where the IDs come from (embedded in the product) | Goes into the add body as |
|------|------------------------|---------------------------------------------------|---------------------------|
| **simple / virtual** | nothing (just quantity) | — | `productId` + `quantity` |
| **configurable** | one value per super-attribute (e.g. color + size) | `superAttributes[]` (the axes + their options) and `variants[]` (each child + its attribute values) | the selected option ids → resolve to a variant |
| **bundle** | one+ member per bundle option | `bundleOptions[]` → each option's member products | option id → product id(s) + qtys |
| **grouped** | quantities for member products | `groupedProducts[]` | member product id → qty map |
| **downloadable** | one+ download links | `downloadableLinks[]` | selected link id(s) |
| **booking** | a date + time slot / ticket | `bookingProducts[]` (slot-config block) **+** live `GET /api/shop/booking-slots` | bookingProductId + chosen slot |

**Configurable resolution:** present each `superAttributes` axis as a selector; as the shopper picks, match the combination against `variants[]` to resolve the concrete child product, its price, and its stock. Disable option combinations that have no saleable variant.

**Booking is the only type needing a runtime fetch:** the embedded `bookingProducts[]` gives the *configuration* (type: default/appointment/event/rental/table, duration, etc.), but **available slots for a chosen date** must be fetched live from `GET /api/shop/booking-slots?id=<bookingProductId>&date=<YYYY-MM-DD>` — they change with bookings.

> See **[add-to-cart.md](./add-to-cart.md)** for the exact add body per type — it consumes exactly the IDs you discover here. Read the PDP and add-to-cart pages together.

---

## 3. Supporting endpoints

| Need | REST | GraphQL field | Notes |
|------|------|---------------|-------|
| Full product (PDP doc) | `GET /api/shop/products/{id}` | `product(id:)` (also `product(sku:)`) | Embeds everything below; usually all you need. |
| Configurable variants (standalone) | `GET /api/shop/products/{productId}/variants` | — | The child variants of a configurable parent; same card fields as the listing. Already embedded in the detail — use this only if you want them paginated/standalone. |
| Booking slots for a date | `GET /api/shop/booking-slots?id=&date=` | `bookingSlots(id:, date:)` | Runtime availability; `id` is the `bookingProductId` from the product's `bookingProducts[]`. |
| Attribute metadata | `GET /api/shop/attributes` · `GET /api/shop/attributes/{id}` | `attributes` · `attribute(id:)` | Labels/types/swatches for rendering attribute selectors; discover the facet set. |
| Attribute options | `GET /api/shop/attribute-options` · `/attribute-options/{id}` | `attributeOptions` · `attributeOption(id:)` | Option labels/swatch values (e.g. the color swatch image). |

Docs: [get product](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-product) · [booking slots](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-booking-slots) · [get attributes](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-attributes) · [get attribute](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-attribute) · [attribute options](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-attribute-options) · REST: [get product](https://api-docs.bagisto.com/api/rest-api/shop/products/get-product), [product type sub-resources](https://api-docs.bagisto.com/api/rest-api/shop/products/product-type-subresources), [booking slots](https://api-docs.bagisto.com/api/rest-api/shop/products/get-booking-slots).

---

## 4. UI/UX

### Component breakdown

- **`Gallery`** — main image + thumbnails (zoom on desktop, swipe on mobile). Swap the main image to the chosen variant's image when a configurable selection resolves.
- **`ProductSummary`** — name, SKU, short description, rating summary, price.
- **`PriceBlock`** — `formattedPrice`; struck-through original + `formattedSpecialPrice` when on sale; for configurable/bundle show `minimumPrice`–`maximumPrice` until a selection narrows it, then the resolved variant price.
- **`OptionSelector`** (type-specific — this is the heart of the PDP):
  - *configurable* → one selector per super-attribute (color swatches, size pills), driven by `attributeOptions` for labels/swatches; disable unavailable combinations.
  - *bundle* → grouped option sections with required/optional indicators and per-option member choices.
  - *grouped* → a list of member products each with its own qty stepper.
  - *downloadable* → checkboxes/list of selectable links.
  - *booking* → a date picker → on date change, fetch `booking-slots` → render available time slots / tickets.
- **`QuantityStepper`** — clamp to available stock; disable when the current selection is out of stock.
- **`AddToCartButton`** — disabled until the selection is complete and saleable; shows loading while the add call is in flight.
- **`WishlistButton` / `CompareButton`** — toggle membership (logged-in); reflect `isInWishlist` / `isInCompare` from the payload (see [wishlist](../features/wishlist.md), [compare](../features/compare.md)).
- **`ReviewsSummary`** — average rating + count, link to the full reviews list (see [reviews](../features/reviews.md)).
- **`RelatedRail`** — related / cross-sell product cards (reuse the card from product-listing).

### Decision points / variants
- **Show the option UI only for the matching type.** A simple product shows just a quantity stepper; a configurable shows the super-attribute axes; etc. Branch once on `product.type`.
- **Resolve before enabling add-to-cart.** For configurable, the Add button stays disabled until a full attribute combination maps to a saleable variant. For booking, until a slot is chosen.
- **Price/stock follow the selection**, not the parent. Update the price block and stock badge as the shopper picks.

### Mobile
- Sticky bottom bar with price + Add-to-Cart (respect `env(safe-area-inset-bottom)`); the gallery swipes; option selectors are large pills/swatches.
- Collapse long description / specs into accordions; keep the selector and CTA above the fold.

### Accessibility
- Swatches/pills are real `radio`/`button` controls with accessible names ("Color: Red"); the selected state is announced.
- `aria-live` on the price block and stock badge so selection changes are spoken.
- Gallery thumbnails keyboard-navigable; images have meaningful `alt`.

### Trust & conversion
- Surface stock state ("In stock" / "Only 3 left"), the rating summary, and shipping/returns reassurance near the CTA.
- Show the savings on sale items (original vs special). Keep the Add-to-Cart prominent and never ambiguous about what will be added.

---

## 5. Step-by-step API flow

### Step 1 — Fetch the product
- **REST:** `GET /api/shop/products/{id}`
- **GraphQL:** `product(id:)` (or `product(sku:)`)
- **Does:** returns the full PDP document with all type-specific blocks embedded.
- **Returns:** base fields + `categories`, `channels`, `variants`, `superAttributes`, `bundleOptions`, `groupedProducts`, `downloadableLinks`/`downloadableSamples`, `bookingProducts`. (Paginated reviews + customer-group prices are *not* inlined — fetch separately.)
- Docs: [get product (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-product) · REST [get product](https://api-docs.bagisto.com/api/rest-api/shop/products/get-product).

### Step 2 — Render the type-specific selector
- Branch on `product.type`; build the selector from the embedded block (see §2). No extra fetch for simple/configurable/bundle/grouped/downloadable.

### Step 3 — (Booking only) fetch live slots
- **REST:** `GET /api/shop/booking-slots?id=<bookingProductId>&date=<YYYY-MM-DD>`
- **GraphQL:** `bookingSlots(id:, date:)`
- **Does:** returns available slots/tickets for the chosen date (non-rental → flat list of `from`/`to`/`timestamp`/`qty`).
- Docs: [booking slots (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-booking-slots) · REST [booking slots](https://api-docs.bagisto.com/api/rest-api/shop/products/get-booking-slots).

### Step 4 — (Optional) attribute labels/swatches
- **REST:** `GET /api/shop/attributes` / `/attribute-options`
- **GraphQL:** `attributes` / `attributeOptions`
- **Does:** resolves human labels and swatch values for the super-attribute selectors when you want richer rendering than the embedded values give.
- Docs: [get attributes](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-attributes) · [attribute options](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-attribute-options).

### Step 5 — Hand off to add-to-cart
- The completed selection (variant id / bundle option choices / grouped qtys / link ids / booking slot) becomes the **add body**. See [add-to-cart.md](./add-to-cart.md) for the exact shape per type.

---

## 6. Errors & edge cases

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Missing storefront key | **401** | Attach `X-STOREFRONT-KEY`. |
| Forbidden | **403** | Misconfigured key on a public read. |
| Bad slot params (missing/invalid date or id) | **400** | Validate the date + `bookingProductId` before fetching slots. |
| Product / booking product not found | **404** | Show a "product not available" page; link back to the category. |
| Invalid selection / unavailable variant | **422** (surfaces at add-to-cart) | Disable the unavailable combination in the UI before it reaches add-to-cart. |
| No slots for the chosen date | **200** (empty list) | "No availability — pick another date"; not an error. |

Standard statuses: **200/201** · **401** · **403** · **400** · **404** · **422**.

---

## 7. GraphQL notes

- Shop endpoint `POST /api/graphql`; storefront key only for the product read.
- `product(id:)` / `product(sku:)` is a **fetchable** resource — select its fields and embedded blocks; the node `id` is an IRI, `_id` the raw integer.
- `bookingSlots` / `attributes` / `attributeOptions` are queries; select the documented fields. **Confirm field/arg names on the docs page before querying.**
- Inputs are camelCase; one field per line in selection sets.

---

## 8. Checklist

**Fetch & render**
- [ ] PDP rendered from a single `GET /api/shop/products/{id}` (server-rendered for SEO); interactive bits hydrated client-side.
- [ ] Price block uses `formatted*` strings; sale shows original + special; configurable/bundle show min–max until resolved.

**Per-type option discovery (CRITICAL)**
- [ ] Branch on `product.type`; build the selector from the **embedded** block (`superAttributes`+`variants` / `bundleOptions` / `groupedProducts` / `downloadableLinks` / `bookingProducts`).
- [ ] Configurable: option combination resolves to a saleable variant before Add is enabled; price/stock follow the selection.
- [ ] Booking: slots fetched **live** per chosen date via `GET /api/shop/booking-slots` (id = `bookingProductId`); never cached as if static.
- [ ] The discovered IDs feed the add body exactly as **add-to-cart.md** specifies.

**Supporting data**
- [ ] Attribute labels/swatches resolved from `attributes`/`attribute-options` where richer rendering is wanted (no need to refetch embedded variants).

**UI/UX**
- [ ] Gallery (zoom/swipe); option selectors as real radios/buttons; quantity clamped to stock.
- [ ] Add-to-Cart disabled until selection complete + saleable; loading state while in flight.
- [ ] Wishlist/compare buttons reflect `isInWishlist`/`isInCompare`; reviews summary + related rail present.
- [ ] Mobile sticky price + CTA (safe-area inset); accordions for long content.

**Accessibility**
- [ ] Swatches/pills are labelled, keyboard-operable controls; `aria-live` on price/stock; gallery images have alt text.

**Both transports & cross-links**
- [ ] Reviews → [reviews](../features/reviews.md); wishlist → [wishlist](../features/wishlist.md); compare → [compare](../features/compare.md); add → [add-to-cart](./add-to-cart.md).
- [ ] Storefront key on every read; GraphQL selections use documented fields; inputs camelCase.
