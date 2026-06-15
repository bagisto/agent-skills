# Cart

The cart is the staging area between catalog and checkout — and the single most-revisited surface in the storefront. It appears in two forms: the **mini-cart** (popup/drawer from the header) and the **full cart page**. Both render the same server cart; keep them in sync from one source.

> **Source of truth:** open the linked api-docs page for each call's exact body/response. This page gives the flow, endpoints, state model, and UX.

- **Auth:** `X-STOREFRONT-KEY` + `Authorization: Bearer <cartToken | customerToken>`. Guests must mint a cart token first (`POST /api/shop/cart-tokens`).
- Every mutating call **returns the full updated cart** — reconcile your UI from the response rather than mutating locally.

---

## 1. Flow architecture & state

The cart is server-owned state keyed by the token. Your client mirrors it:

```
  guest:  POST /api/shop/cart-tokens ──▶ cartToken (persist it)
  read:   POST /api/shop/cart ──────────▶ full cart (items, totals, couponCode)
            │
            ├─ add item        POST /api/shop/add-product-in-cart      → full cart   (see add-to-cart.md)
            ├─ change qty      POST /api/shop/update-cart-item         → full cart
            ├─ remove one      POST /api/shop/remove-cart-item         → full cart
            ├─ remove many     POST /api/shop/remove-cart-items        → full cart
            ├─ apply coupon    POST /api/shop/apply-coupon             → full cart   (see features/coupons.md)
            └─ remove coupon   POST /api/shop/remove-coupon            → full cart
            │
  on login: POST /api/shop/merge-carts (cartId = guest cart _id, customer Bearer) → merged cart
            │
            ▼
        proceed to checkout.md
```

- **Mint the guest token first:** `POST /api/shop/cart-tokens` (GraphQL `createCartToken`) → `cartToken`.
- **Token persistence:** store the guest `cartToken` (e.g. localStorage) so the cart survives reloads; send it as the Bearer on every cart call. Discard it after a successful order (see checkout post-order cleanup).
- **Read cart over GraphQL is a mutation, not a query:** use `createReadCart(input: {})` (returns `readCart`), not a `cart` query.
- **Source of truth:** the server cart. After any mutation, refresh the store + mini-cart + badge from the returned cart. Optional optimistic UI is fine, but reconcile to the response.
- **Client architecture:** a single cart store (Context/Zustand/Redux) holding the cart + token + loading/error flags; a data layer wrapping each call (e.g. TanStack Query with a `['cart']` key you invalidate after mutations); the mini-cart and cart page both read from that store.

---

## 2. Operations

| Operation | REST | GraphQL field | Body essentials |
|-----------|------|---------------|-----------------|
| Mint guest cart token | `POST /api/shop/cart-tokens` | `createCartToken` | — (returns `cartToken`; send it as the Bearer) |
| Read cart | `POST /api/shop/cart` | `createReadCart` (mutation → returns `readCart`) | — (token in Bearer) |
| Add item | `POST /api/shop/add-product-in-cart` | `createAddProductInCart` | per product type (see [add-to-cart](./add-to-cart.md)) |
| Update qty/options | `POST /api/shop/update-cart-item` | `createUpdateCartItem` | cart item id + new quantity |
| Remove one item | `POST /api/shop/remove-cart-item` | `createRemoveCartItem` | cart item id |
| Remove several | `POST /api/shop/remove-cart-items` | `createRemoveCartItems` | cart item ids |
| Apply coupon | `POST /api/shop/apply-coupon` | `createApplyCoupon` | coupon code (see [coupons](../features/coupons.md)) |
| Remove coupon | `POST /api/shop/remove-coupon` | `createRemoveCoupon` | — |
| Merge guest→customer | `POST /api/shop/merge-carts` | `createMergeCart` | guest cart `_id` as `cartId` (customer Bearer) |

Docs: [get cart](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-cart), [update item](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/update-cart-item), [remove item](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/remove-cart-item), [merge cart](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/merge-cart).

### Cart payload (what you render)
Each call returns: `id`, `itemsCount`, `items[]` (per item: `id`, `productId`, `name`, `sku`, `quantity`, `type`, `options`, `price`/`formattedPrice`, `total`/`formattedTotal`, `canChangeQty`), totals (`subtotal`, `discountAmount`, `taxAmount`, `shippingAmount`, `grandTotal` + `formatted*`), `couponCode`, `success`, `message`.

### Shipping estimate (optional, pre-checkout)
For a "calculate shipping" widget on the cart page — estimating rates **before** the checkout address step — use `POST /api/shop/estimate-shippings` (GraphQL `createEstimateShipping`), passing the destination (country / state / postcode). No published api-docs page yet — confirm the exact request body against the live endpoint.

---

## 3. UI/UX

### Mini-cart (popup / drawer)
- Opens from the header cart icon (badge = `itemsCount`). Auto-open or toast on add (your choice — be consistent).
- Lists items (thumbnail, name, variant `options`, qty, `formattedTotal`), a subtotal, and **View cart** + **Checkout** CTAs.
- Inline qty change + remove, each calling the API and reconciling from the response.
- `aria-live="polite"` on the badge + item list so screen readers hear changes.

### Cart page
- Full line-item table: image, name + variant options, unit price, qty stepper (respect `canChangeQty`), line total, remove.
- Order summary: subtotal, discount (with applied `couponCode`), tax, shipping, grand total — all from the API `formatted*` fields.
- Coupon field (see [coupons](../features/coupons.md)). Clear **Proceed to checkout** CTA.
- **Empty state:** friendly message + "continue shopping" link; never a blank table.

### Quantity & removal UX
- Debounce qty steppers so a quick +/+/+ doesn't fire three calls; disable the row while a call is in flight.
- Removing the last item → show the empty state.
- Honor `canChangeQty` (some types/promos lock quantity).

---

## 4. Guest→customer merge (CRITICAL)

When a guest with items logs in, **merge their cart before continuing** or the items vanish:

1. Guest has a cart (token + `_id`).
2. Customer logs in → receives a customer Bearer token.
3. Call `createMergeCart` / `POST /api/shop/merge-carts` with the guest cart's `_id` as `cartId`, using the **customer** Bearer token.
4. Continue with the merged customer cart; drop the old guest token.

Requires customer authentication (the Bearer identifies the target customer cart).

---

## 5. Errors & edge cases

| Failure | HTTP / GraphQL | Handle by |
|---|---|---|
| Stock changed / item no longer saleable | 422 | Update/remove the line, recalc, tell the user what changed. |
| Qty exceeds available stock | 422 | Clamp the stepper to available; surface the max. |
| Missing/expired cart token (guest) | 401 | Mint a new token; the old cart may be gone — start fresh. |
| Coupon invalid / not applicable | 404 / 422 | See [coupons](../features/coupons.md). |

Standard statuses: **200/201** · **401** · **403** · **404** · **422**.

---

## 6. GraphQL notes

- Shop endpoint `POST /api/graphql`; inputs camelCase; one field per line.
- Cart mutations return the cart / a result object — select the documented fields (items, totals, `success`, `message`), per each mutation's docs page.
- `createMergeCart` takes the guest cart `_id` as `cartId` and **requires** a customer Bearer token.

---

## 7. Checklist

**State & persistence**
- [ ] Guest cart token minted (`POST /api/shop/cart-tokens`) and persisted; sent as Bearer on every cart call.
- [ ] Single cart store; mini-cart + cart page + badge all read from it.
- [ ] UI reconciled from the **returned cart** after every mutation (not local-only).

**Operations**
- [ ] Read (`POST /cart`), update qty (`update-cart-item`), remove one (`remove-cart-item`), remove many (`remove-cart-items`) wired.
- [ ] Qty steppers debounced; rows disabled during in-flight calls; `canChangeQty` honored.
- [ ] Coupon apply/remove wired (see coupons feature).

**Merge**
- [ ] On login, guest cart merged via `merge-carts` (guest `_id` as `cartId`, customer Bearer) before proceeding.

**UI/UX**
- [ ] Mini-cart with badge, items, subtotal, View-cart + Checkout CTAs.
- [ ] Cart page with line items, summary (from API `formatted*`), coupon field, checkout CTA.
- [ ] Empty-cart state handled.
- [ ] `aria-live` on badge/list; keyboard-operable steppers/remove.

**Errors**
- [ ] Stock/qty 422s handled with clear, recoverable messages.
- [ ] Expired guest token (401) recovers by minting a new cart.

**Both transports**
- [ ] Works for guest + logged-in; storefront key always sent; GraphQL selections use documented result fields.
