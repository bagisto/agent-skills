# Add to cart

The single most-clicked action in the storefront. One endpoint handles every product type — the body changes by type, and the **option IDs always come from the product-detail response**, never from memory.

> **Source of truth:** open the [add-to-cart docs page](https://api-docs.bagisto.com/api/rest-api/shop/cart/add-to-cart) for the full per-type request/response. This page gives you the flow, the per-type fields, and the UX.

- **REST:** `POST /api/shop/add-product-in-cart`
- **GraphQL:** mutation `createAddProductInCart(input: { productId, quantity, … })`
- **Auth:** `X-STOREFRONT-KEY` + `Authorization: Bearer <cartToken | customerToken>`. A guest needs a cart token first (`POST /api/shop/cart-tokens` → `cartToken`); send it as the Bearer on every cart call.
- **Returns:** the **full updated cart** (`items[]`, `itemsCount`, totals, `couponCode`, `success`, `message`) — use it to refresh the mini-cart in one round-trip; no follow-up read needed.

---

## 1. Flow architecture

```
  product detail (has the option IDs)
        │  user picks variant / bundle options / qty / links
        ▼
  build body by product TYPE  ──▶  POST /api/shop/add-product-in-cart
        │                              │ validates: qty ≥ 1, required options present, item saleable + in stock
        ▼                              ▼
  optimistic mini-cart open      returns FULL cart  ──▶  reconcile mini-cart + badge from response
                                       │ on error (422): keep the user on the product, show why
```

- The product-detail fetch is the **prerequisite** — it supplies the variant IDs, bundle-option IDs, associated-product IDs, and download-link IDs you must send.
- Treat the **returned cart as truth**: update your cart store and item count from the response, don't increment locally and hope.

---

## 2. Body per product type

All types send `productId` + `quantity` (min 1). Add the type-specific fields:

| Type | Extra fields | Where the IDs come from |
|------|--------------|--------------------------|
| simple / virtual | *(none)* | — |
| **configurable** | `selectedConfigurableOption` = chosen **variant product ID** (required) | the product detail's variants / super-attribute matrix |
| **bundle** | `bundleOptions` = `{ "<optionId>": [<bundleOptionProductId>] }` + `bundleOptionQty` = `{ "<optionId>": <qty> }` | the product detail's bundle options |
| **grouped** | `groupedQty` = `{ "<associatedProductId>": <qty> }` (include **every** associated product) | the product detail's grouped/associated products |
| **downloadable** | `links` = `[<linkId>]` | the product detail's downloadable links |

(Configurable + customizable products may also accept customizable-option fields — see the docs page.) **Items must be active and in stock** or the call is rejected (422).

---

## 3. UI/UX per type

- **Simple / virtual** — a quantity stepper + "Add to cart". The fastest path; don't over-build it.
- **Configurable** — render the variant selectors (size/color swatches) from the product detail; **disable "Add to cart" until a complete variant is selected**, then send that variant's product ID as `selectedConfigurableOption`. Surface out-of-stock variants as disabled, not hidden.
- **Bundle** — render each bundle option (radio/checkbox per the option's selection type) + per-option qty; build the `bundleOptions` / `bundleOptionQty` maps; show the running bundle price.
- **Grouped** — render every associated product with its own qty input (0 = skip); send the non-zero ones in `groupedQty`.
- **Downloadable** — render the selectable links as checkboxes; send the chosen `links`.

**Feedback (all types):** open the mini-cart / show a toast on success using the returned cart; animate the cart badge to the new `itemsCount`. Announce the change with `aria-live="polite"` for screen readers. Keep the button in a loading state during the call and disable it to prevent double-adds.

---

## 4. Errors & edge cases

| Failure | HTTP / GraphQL | Handle by |
|---|---|---|
| Quantity < 1 or missing required options | 422 | Validate before submit; show which option is missing. |
| Out of stock / not saleable | 422 | Disable add for OOS variants; on rejection, message and offer alternatives. |
| Configurable with no variant chosen | 422 | Gate the button until a full variant is selected. |
| Missing cart token (guest) | 401 | Mint a cart token first (`POST /api/shop/cart-tokens`), then retry. |
| Quantity exceeds stock | 422 | Surface the available quantity; clamp the stepper. |

Standard statuses: **200/201** success · **401** unauthenticated · **403** forbidden · **422** validation.

---

## 5. GraphQL notes

- Field: `createAddProductInCart(input: { productId, quantity, … })`; select the returned cart fields (items, totals, `success`, `message`) — see the [GraphQL add-to-cart page](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/add-to-cart).
- Inputs camelCase; one field per line in selection sets.
- Same per-type fields as REST (`selectedConfigurableOption`, `bundleOptions`/`bundleOptionQty`, `groupedQty`, `links`).

---

## 6. Checklist

- [ ] Cart token obtained for guests before any add (`POST /api/shop/cart-tokens`).
- [ ] Body built by product **type**; option IDs sourced from the **product-detail** response, not hardcoded.
- [ ] Configurable: "Add" gated until a complete, in-stock variant is selected; variant product ID sent as `selectedConfigurableOption`.
- [ ] Bundle: `bundleOptions` + `bundleOptionQty` maps built from the selected options.
- [ ] Grouped: `groupedQty` includes every chosen associated product.
- [ ] Downloadable: `links` carries the selected link IDs.
- [ ] Mini-cart, badge `itemsCount`, and totals refreshed from the **returned cart** (not incremented locally).
- [ ] Button shows loading + is disabled during the call (no double-add); `aria-live` announces the update.
- [ ] 422 (stock / missing option) handled with a clear, recoverable message.
- [ ] Works for guest (`cartToken`) and logged-in (`customerToken`); storefront key always sent.
