# Create-Order flow (admin places an order for a customer)

The admin "Create Order" screen — building an order on a customer's behalf through a **draft cart**. Like storefront checkout, it's a **strict sequential state machine**, but keyed by a draft cart the admin owns (`is_active = 0`), and it starts by choosing a customer.

> **Source of truth:** open the linked api-docs page for each call's exact body/response. This page gives the flow, endpoints, sequence rules, and UX. **Never invent a payload from memory.**

**Auth:** every call carries the admin Integration Bearer token (see `../connecting-to-the-api.md`). Actions are capped by the admin's role — placing an order needs the order-create permission (else 403).

---

## 1. Flow architecture & structure

```
  pick customer (GET /api/admin/customers?…)
        │
        ▼
  POST /api/admin/customers/{customerId}/draft-carts ───▶ cartId   (empty draft cart, is_active=0)
        │
        ▼
  ┌──────────────┐  POST   /api/admin/carts/{cartId}/items        (per product type; booking blocked)
  │  ADD ITEMS   │  PUT    /api/admin/carts/{cartId}/items        (bulk qty update)
  │              │  DELETE /api/admin/carts/{cartId}/items        (remove an item)
  └──────────────┘  POST/DELETE /api/admin/carts/{cartId}/coupon  (apply / remove)
        │  prerequisite: cart has items
        ▼
  ┌──────────────┐  POST /api/admin/carts/{cartId}/addresses      (billing [+ shipping])
  │  ADDRESSES   │
  └──────────────┘
        │  prerequisite: items present
        ▼
  ┌──────────────┐  GET  /api/admin/carts/{cartId}/shipping-methods   (rates)
  │  SHIPPING    │  POST /api/admin/carts/{cartId}/shipping-methods    { shippingMethod }
  └──────────────┘
        │  prerequisite: addresses saved
        ▼
  ┌──────────────┐  GET  /api/admin/carts/{cartId}/payment-methods    (supported)
  │  PAYMENT     │  POST /api/admin/carts/{cartId}/payment-methods     { method }
  └──────────────┘
        │  prerequisite: shipping selected
        ▼
  POST /api/admin/orders/place/{cartId} ───▶ orderId
        validates the whole chain; accepts only cashondelivery / moneytransfer
```

- Read the draft cart any time with `GET /api/admin/carts/{cartId}` (items, totals, addresses, selected methods).
- **Sequence is enforced** — calling a step before its prerequisite returns **409** with a message naming what's missing. Gate the UI on each prerequisite to avoid round-trips.
- **Draft-only:** these endpoints operate only on `is_active = 0` carts; a storefront (active) cart returns 403.
- **Client architecture:** a customer picker → a cart workspace holding `cartId` + the draft cart + current step; a data layer wrapping each call; re-read the cart (or use each call's returned cart) after every mutation.

---

## 2. Step-by-step

### Step 0 — choose the customer
`GET /api/admin/customers?...` (search by name/email). The Create-Order screen needs a customer before a cart exists. Docs: Customers menu (`../menus/customers.md`).

### Step 1 — bootstrap a draft cart
- `POST /api/admin/customers/{customerId}/draft-carts` → `{ cartId, customerId, success, message }`.
- Unknown/zero customer → 404; underlying failure → 422. Docs: [create draft cart](https://api-docs.bagisto.com/api/graphql-api/admin/customers/create-draft-cart) and the Carts pages below.

### Step 2 — add items (per product type)
- `POST /api/admin/carts/{cartId}/items` — body forwards to add-product, so every type works (simple/configurable/bundle/grouped/downloadable/virtual). The option IDs come from the product (search via `GET /api/admin/products`).
- **Booking products are blocked** (400) — core ships no booking partial in Create-Order. **Non-saleable / out-of-stock products are rejected up front** (400) and the draft cart is preserved so you can add a different product.
- Update qty: `PUT /api/admin/carts/{cartId}/items` (`{ qty: { itemId: newQty } }`). Remove: `DELETE /api/admin/carts/{cartId}/items` (`{ cartItemId }`).
- Docs: [add item](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/add-item), [update items](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/update-items), [remove item](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/remove-item).

### Step 3 — coupon (optional)
- Apply: `POST /api/admin/carts/{cartId}/coupon`. Remove: `DELETE /api/admin/carts/{cartId}/coupon`. Docs: [apply coupon](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/apply-coupon), [remove coupon](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/remove-coupon).

### Step 4 — addresses
- `POST /api/admin/carts/{cartId}/addresses` — `{ billing: {…, useForShipping}, shipping? }` (camelCase keys). Prefill from the customer's address book: `GET /api/admin/customers/{customerId}/addresses`. Docs: [save address](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/save-address).

### Step 5 — shipping method
- `GET /api/admin/carts/{cartId}/shipping-methods` (rates; addresses must be saved → 409 otherwise) · `POST /api/admin/carts/{cartId}/shipping-methods` `{ shippingMethod }`. Docs: [list](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/list-shipping-methods), [set](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/set-shipping-method).

### Step 6 — payment method
- `GET /api/admin/carts/{cartId}/payment-methods` (shipping must be selected → 409 otherwise) · `POST /api/admin/carts/{cartId}/payment-methods` `{ method }`. Docs: [list](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/list-payment-methods), [set](https://api-docs.bagisto.com/api/graphql-api/admin/sales/carts/set-payment-method).

### Step 7 — place order
- `POST /api/admin/orders/place/{cartId}` → `orderId`. Validates the full chain (items + both addresses + shipping + payment). **Only `cashondelivery` / `moneytransfer` are accepted at place** (the same restriction the admin Create-Order screen hardcodes); other methods → 422. Docs: [place order](https://api-docs.bagisto.com/api/graphql-api/admin/sales/orders/place-order).

---

## 3. Create-Order sidebar (read-only helpers)

The admin screen offers quick-add panels for the chosen customer — surface these and let the admin pull items in:

| Panel | Endpoint |
|-------|----------|
| Customer's active cart items | `GET /api/admin/customers/{customerId}/cart-items` |
| Wishlist items | `GET /api/admin/customers/{customerId}/wishlist-items` |
| Compare items | `GET /api/admin/customers/{customerId}/compare-items` |
| Recent order items | `GET /api/admin/customers/{customerId}/recent-order-items` |
| Address book | `GET /api/admin/customers/{customerId}/addresses` |

Each returns the `{ data, meta }` envelope.

---

## 4. UI/UX

- **Layout:** a two-pane screen — left: customer + product search + the building cart; right: address / shipping / payment / summary, advancing as prerequisites are met.
- **Customer picker** with search; once chosen, spawn the draft cart and show the sidebar panels.
- **Product search modal** (`GET /api/admin/products`) returns a slim picker row (sku/name/price/image/saleable); render type-specific option selectors before adding (configurable variant, bundle options, grouped qty, downloadable links).
- **Gate each step** on its prerequisite (no items → can't reach addresses, etc.) — mirrors the 409 enforcement.
- **Order summary** re-rendered from the returned/`GET` cart after every mutation (items, totals, applied coupon, selected methods).
- Mobile: single-column, collapsible summary, sticky "Place Order".

---

## 5. Errors & edge cases

| Failure | HTTP | Handle by |
|---|---|---|
| Out-of-order step | 409 | Gate the UI; send the admin to the missing prerequisite. |
| Booking product added | 400 | Hide/disable booking products in the picker; explain it's unsupported. |
| Non-saleable / OOS product | 400 | Reject with a message; the draft cart is preserved — add a different product. |
| Unsupported payment at place | 422 | Restrict the place step to cashondelivery / moneytransfer. |
| No order-create permission | 403 | "You don't have permission to create orders." |
| Active (storefront) cart id used | 403 | Only draft carts (`is_active=0`) are valid here. |

---

## 6. GraphQL notes

- Endpoint `POST /api/admin/graphql`; the cart mutations and place-order are **action mutations** — select their result fields (`cartId`, `orderId`, `success`, `message`, the refreshed cart), not a generic `id`. See `../graphql.md`.
- Inputs camelCase; one field per line.

---

## 7. Checklist

**Flow & sequence**
- [ ] Customer chosen before anything (`GET /api/admin/customers`).
- [ ] Draft cart spawned (`POST /customers/{customerId}/draft-carts`) → `cartId` held.
- [ ] Each step gated on its prerequisite (items → addresses → shipping → payment → place); 409 handled.
- [ ] Cart re-read after every mutation (`GET /carts/{cartId}`); summary reflects it.

**Items**
- [ ] Add per product type with option IDs from the product; update (`PUT …/items`) + remove (`DELETE …/items`) wired.
- [ ] Booking products hidden/blocked (400); non-saleable rejection handled, cart preserved.
- [ ] Coupon apply/remove (`…/coupon`) wired.

**Addresses / shipping / payment**
- [ ] Address saved (`POST …/addresses`), prefilled from the customer address book.
- [ ] Shipping rates fetched after address, method set; payment methods fetched after shipping, method set.

**Place**
- [ ] `POST /orders/place/{cartId}` → `orderId`; restricted to cashondelivery / moneytransfer; button disabled while in flight.
- [ ] 403 (no permission) and 422 (unsupported payment / incomplete) handled.

**Sidebar**
- [ ] Customer cart-items / wishlist / compare / recent-order-items / addresses panels surfaced for quick-add.

**Both transports**
- [ ] Admin Bearer token on every call; GraphQL selections use documented result fields; inputs camelCase.
