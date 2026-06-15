# Order confirmation flow

The thank-you page — the moment right after the order is placed. It's a **conversion-closing, trust-building, mostly-UX** screen: it confirms success, restates what was ordered, sets expectations for what happens next, and (critically) **cleans up the spent cart**. It introduces almost no new endpoints — the order data arrives from the place-order call, and logged-in customers can re-read it.

> **Source of truth for exact shapes:** the order fields you can render come from the place-order response and the customer-order read. Open the linked api-docs page for the precise shape. **Never invent an order payload from memory.**

- **Auth:** rendering the just-placed order summary needs no extra call (use what place-order returned). Re-reading a stored order needs a **customer Bearer** (`GET /api/shop/customer-orders/{id}`); guests cannot re-read it — render from the in-memory summary.
- **This page runs the post-order cleanup** (clear cart + discard the guest cart token). Skipping it leaves the cart popup showing the items the shopper just bought.

---

## 1. Flow architecture & structure

The order is already placed before this page renders. Confirmation is the landing after that success:

```
  checkout.md ── POST /api/shop/checkout-orders ──▶ { orderId }   (the order is created)
        │
        │  redirect to /order-confirmation/<orderId>
        ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  ORDER CONFIRMATION (thank-you)                                │
  │                                                                │
  │  RUN CLEANUP FIRST (CRITICAL):                                 │
  │    • clear cart state from the store                           │
  │    • discard the guest cartToken (+ stored cart id)            │
  │    • invalidate cart queries                                   │
  │                                                                │
  │  RENDER the summary:                                           │
  │    • logged-in → GET /api/shop/customer-orders/{orderId}       │
  │    • guest     → render from the place-order result / passed   │
  │                  order summary (no re-read available)          │
  └──────────────────────────────────────────────────────────────┘
        │
        ├─ "View order" / "Track order"  ──▶ customer-orders.md (logged-in)
        ├─ "Create an account"           ──▶ authentication.md (guest upsell)
        └─ "Continue shopping"           ──▶ product-listing.md
```

**Recommended client architecture**

- **Routing** — a dynamic route keyed by the returned `orderId`, e.g. Next.js `app/order-confirmation/[orderId]/page.tsx`, SvelteKit `routes/order-confirmation/[orderId]/+page.svelte`. Don't reuse the checkout route — a refresh of `/checkout` must not re-trigger anything.
- **Guard the route.** It's only valid immediately after a successful place-order (or for a logged-in customer who owns the order). If someone hits it cold with no order context and no auth, redirect to the order history or the shop root — never show a fake "thank you".
- **State** — read `orderId` from the route; carry the place-order result through navigation (router state / a short-lived store) so the guest summary renders without a re-fetch. For logged-in customers, fetch the order fresh by id.
- **Idempotency** — this page must never place an order. The order was already created in checkout; confirmation only *reads* and *cleans up*.

---

## 2. Post-order cleanup (CRITICAL — do this first)

The moment confirmation mounts, the old cart is spent. Clean it up before rendering anything cart-related:

1. **Clear cart state** from your global store (items, totals, badge → 0).
2. **Discard the guest `cartToken`** and any stored cart id — it's consumed; a new cart needs a fresh token (`POST /api/shop/cart-tokens`).
3. **Invalidate cart queries** (e.g. `queryClient.invalidateQueries({ queryKey: ['cart'] })`) so the mini-cart/badge don't show stale items.

This is the same cleanup the checkout flow mandates — see **[checkout.md → post-order cleanup](./checkout.md)**. Skip it and the header cart badge keeps counting the just-ordered items.

---

## 3. Decision points / variants

| Decision | Guidance |
|---|---|
| **Logged-in vs guest data source** | Logged-in → re-read the order by id for the authoritative, persisted summary. Guest → render from the place-order result you carried over; there's no guest re-read endpoint. |
| **What `orderId` gets you** | The place-order response returns `orderId` (and `id`). Use it for the route and, for logged-in customers, the detail fetch. |
| **Offsite-payment returns** | If checkout used an offsite gateway, the user lands here after the gateway redirect resolves to your success URL. Treat the order as placed only once the order actually exists (the checkout flow owns finalisation); confirmation just displays it. |
| **Account upsell timing** | Offer "create an account to track this order" **after** the order is placed (never block guest checkout with it). Pre-fill the email from the order. |

---

## 4. UI/UX

### Component breakdown

- **`SuccessHeader`** — a clear success state: checkmark, "Thank you, your order is confirmed", and the **order number** prominently (shoppers screenshot this). A brief "a confirmation email is on its way" line.
- **`OrderSummary`** — line items (image, name, variant options, qty, line total), the totals breakdown (subtotal, discount with coupon, tax, shipping, grand total — all from the order's `formatted*` fields), and the billing/shipping addresses + chosen shipping & payment method.
- **`NextSteps`** — what happens now: order processing → shipment → delivery; estimated timeline; how to track. For bank-transfer / cash-on-delivery, show the payment instructions.
- **`GuestAccountUpsell`** — "Create an account to track this and future orders" with the email pre-filled (guest only).
- **`SecondaryActions`** — "Continue shopping" (→ listing), "View order" / "Track order" (logged-in → order detail), download invoice (when available), contact support.

### Mobile
- Single column; order number and success state above the fold.
- Sticky or top-pinned primary action ("Continue shopping" / "Track order"); collapse the full item list into an expandable summary if it's long.

### Accessibility
- Move focus to the `SuccessHeader` heading on mount and announce success via `aria-live="polite"` (or `role="status"`) so screen-reader users hear the confirmation.
- The order number is selectable text (not an image) so it can be copied.
- All secondary actions are real, keyboard-focusable links/buttons with clear names.

### Trust & conversion
- **Reassurance:** confirmation email notice, support contact, return/refund policy link, secure-checkout badge.
- **Set expectations:** concrete next-steps timeline reduces "where's my order?" support contacts.
- **Re-engage:** a tasteful "you might also like" rail or a first-order discount for the next purchase — *below* the confirmation, never competing with it.
- **Don't re-show the cart** anywhere on this page (it's empty now) — that's a jarring trust killer.

---

## 5. Step-by-step API flow

This flow is intentionally light on endpoints — most of the work is UX + cleanup.

### Step 0 — Carry over the order (from checkout)
- The place-order call (`POST /api/shop/checkout-orders` / `createCheckoutOrder`) returned `{ id, orderId }`. The confirmation route is keyed on `orderId`; the order summary for guests comes from this same result.
- Docs: [place order](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/place-order) · REST [place order](https://api-docs.bagisto.com/api/rest-api/shop/checkout/place-order).

### Step 1 — Run cleanup (no API call required for state, mint later)
- Clear cart store, discard guest `cartToken` + cart id, invalidate cart queries (see §2). The next time the shopper adds an item, mint a fresh cart token.

### Step 2 — Render the order summary
- **Logged-in (authoritative re-read):**
  - **REST:** `GET /api/shop/customer-orders/{id}`
  - **GraphQL:** `customerOrder(id:)`
  - **Does:** returns the persisted order — items, addresses, payment, shipments, totals — embedded inline (no follow-up calls).
  - **Returns:** the full order detail document for the owning customer (other customers' orders return not-found).
  - Docs: [get customer order (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-order) · REST [get customer order](https://api-docs.bagisto.com/api/rest-api/shop/customer-orders/get-customer-order).
- **Guest:** render from the place-order result you carried over — there is no guest re-read endpoint. Persist nothing sensitive client-side beyond the current session.

### Step 3 — Offer next steps
- Link "View order" / order history for logged-in customers (see [customer-orders.md](./customer-orders.md) for detail, cancel, reorder, invoices, and downloadables). Offer the account-creation upsell for guests (see [authentication.md](./authentication.md)).

---

## 6. Errors & edge cases

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Page hit cold (no order context, guest) | — | Guard the route; redirect to shop root / order history rather than show an empty "thank you". |
| Missing storefront key | **401** | Attach `X-STOREFRONT-KEY`. |
| Re-reading an order without auth (guest) | **401** | Don't attempt the re-read for guests; render from the carried-over summary. |
| Requesting another customer's order | **403 / 404** | Treated as not-found (prevents order enumeration); show "order not found". |
| Order id not found | **404** | Show "order not found" + link to order history / support. |
| Validation | **422** | Surface a friendly message; the order already exists — never retry place-order from here. |

Standard statuses: **200/201** · **401** · **403** · **400** · **404** · **422**.

---

## 7. GraphQL notes

- Shop endpoint `POST /api/graphql`; the order re-read needs the **customer Bearer** + storefront key.
- `customerOrder(id:)` is a **fetchable** resource — its `id` argument is the IRI (`/api/shop/customer-orders/3`); select the documented order fields (items, addresses, payment, shipments, totals) one per line.
- The place-order mutation returns a **result object** (`id`, `orderId`) — select those documented fields, not a generic entity.

---

## 8. Checklist

**Cleanup (CRITICAL — run on mount, before rendering cart-related UI)**
- [ ] Cart state cleared from the store; badge → 0.
- [ ] Guest `cartToken` + stored cart id discarded (a new cart needs a fresh token).
- [ ] Cart queries invalidated (mini-cart/badge can't show stale items).
- [ ] Same cleanup as checkout's post-order step — no divergence.

**Routing & guarding**
- [ ] Dynamic route keyed on the returned `orderId`; refresh never re-places an order (idempotent — no place-order call here).
- [ ] Route guarded: cold/unauth hits redirect to shop root / order history, not a fake thank-you.

**Data source**
- [ ] Logged-in → authoritative re-read via `GET /api/shop/customer-orders/{id}` / `customerOrder(id:)`.
- [ ] Guest → render from the carried-over place-order summary (no guest re-read endpoint).

**UI/UX**
- [ ] Success state + prominent order number (selectable text) + "email on its way".
- [ ] Order summary: items, totals (from `formatted*`), addresses, shipping + payment method.
- [ ] Next-steps timeline / payment instructions; secondary actions (continue shopping, track order, invoice, support).
- [ ] Guest account-creation upsell **after** placement, email pre-filled.

**Accessibility & trust**
- [ ] Focus moved to the heading + `aria-live`/`role="status"` success announcement; actions keyboard-focusable.
- [ ] Reassurance (email/support/returns/secure badge); the cart is never shown on this page.

**Both transports & cross-links**
- [ ] Detail/cancel/reorder/invoices/downloadables → [customer-orders](./customer-orders.md); guest upsell → [authentication](./authentication.md); cleanup detail → [checkout](./checkout.md).
- [ ] Storefront key on every call; logged-in re-read sends the customer Bearer; GraphQL selections use documented fields.
