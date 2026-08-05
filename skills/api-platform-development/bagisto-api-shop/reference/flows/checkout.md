# Checkout flow

The final step in the conversion funnel — turning a cart into an order. On the Bagisto Shop API, checkout is a **strict, sequential state machine over the cart**: each step depends on the previous one, and the API rejects out-of-order calls. Build the UI to mirror that sequence and never let the user reach a step whose prerequisite isn't met.

> **Source of truth for exact shapes:** this page gives you the flow, the endpoints, the sequence rules, and the UX. For the full request/response body of any call, open its api-docs page (linked per step). **Never hardcode a payload from memory — open the page.** Verify the method/fields before writing the call.

**The one rule that governs everything:** **always fetch shipping methods and payment methods from the backend** after the address is saved — they vary by cart, address, region, and store config. Never hardcode them.

---

## 1. Flow architecture & structure

Checkout is a progression through cart states. Each transition is an API call; each call has a prerequisite:

```
   cart has items
        │
        ▼
  ┌──────────────┐   POST /checkout-addresses          (billing [+ shipping])
  │  ADDRESSES   │ ──────────────────────────────────▶ cart.billing & cart.shipping set
  └──────────────┘
        │  prerequisite: cart not empty
        ▼
  ┌──────────────┐   GET  /checkout-shipping-methods   (rates for THIS cart+address)
  │  SHIPPING    │   POST /checkout-shipping-methods    { shippingMethod }
  └──────────────┘ ──────────────────────────────────▶ cart.shipping_method set
        │  prerequisite: addresses saved (+ stockable items present)
        ▼
  ┌──────────────┐   GET  /payment-methods             (supported methods)
  │  PAYMENT     │   POST /checkout-payment-methods     { paymentMethod, *Url? }
  └──────────────┘ ──────────────────────────────────▶ cart.payment set  ──┐
        │  prerequisite: shipping method selected                          │ offsite gateway?
        ▼                                                                  ▼ paymentGatewayUrl → redirect
  ┌──────────────┐   POST /checkout-orders                          ┌─────────────┐
  │  REVIEW +    │ ───────────────────────────────────────────────▶│  ORDER      │ → orderId
  │  PLACE ORDER │   validates: items, both addresses, shipping,    │  PLACED     │
  └──────────────┘   payment, stock/inventory                       └─────────────┘
        │ prerequisite: all of the above                                   │
        └── on failure: stay on review, surface field/stock/payment error  ▼
                                                              clear cart token + redirect to confirmation
```

**Recommended client architecture**

- **Routing** — one route per logical step (multi-step) or one route with in-page sections (single-page). Dynamic confirmation route, e.g. Next.js `app/checkout/page.tsx` + `app/order-confirmation/[orderId]/page.tsx`; SvelteKit `routes/checkout/+page.svelte`; etc.
- **State** — a single checkout state container (Context / Zustand / Redux) holding: the cart, the current step, the saved address, the fetched shipping rates + selected method, the fetched payment methods + selected method, and per-step loading/error flags. Treat the **server cart as the source of truth** — re-read it (or use each call's returned cart) after every mutation rather than trusting local copies.
- **Data layer** — wrap each call in a query/mutation (e.g. TanStack Query). Cache the GETs (shipping/payment) keyed by cart + address; invalidate them when the address changes (rates depend on it).
- **Guarding** — gate each step's route on its prerequisite (no items → back to cart; no address → back to step 1). This mirrors the API's own sequence enforcement and avoids 4xx round-trips.

---

## 2. Decision: single-page vs multi-step

| Choose **single-page** (accordion / sections) when… | Choose **multi-step** (one screen per step) when… |
|---|---|
| Simple catalog, low field count | Many fields, B2B, complex shipping |
| Mobile-heavy traffic (>60%) | High-value orders where review matters |
| You want the fewest taps to order | You want progress framing + per-step validation |

**Hybrid (recommended):** scrollable sections on desktop, accordion with progressive disclosure on mobile. Either way the **API call sequence is identical** — only the presentation differs. Always show a **progress indicator** (Address → Shipping → Payment → Review).

---

## 3. Guest vs logged-in

The entire checkout works for **both** — the only difference is the Bearer token:

| Mode | Headers |
|---|---|
| Guest | `X-STOREFRONT-KEY` + `Authorization: Bearer <cartToken>` (from `POST /api/shop/cart-tokens`) |
| Logged-in customer | `X-STOREFRONT-KEY` + `Authorization: Bearer <customerToken>` |

- **Don't force account creation.** Offer guest checkout when the store allows it; optionally offer "create an account" *after* the order is placed.
- **Logged-in:** pre-fill from the customer's saved addresses (`GET /api/shop/checkout-addresses` returns the address applied to the session; the customer's address book comes from the account addresses endpoints). Let them pick a saved address or enter a new one.
- **Guest→customer merge:** if a guest logs in mid-session, merge the guest cart into the customer cart (`merge-cart`) before continuing — otherwise the items are lost. See the cart flow page.

---

## 4. Component architecture (recommended)

Split the page into one component per step rather than one massive form — better testability, reuse, and isolated loading/error states:

- `AddressStep` — billing form + "use for shipping" toggle (+ shipping form when off); on submit → save address.
- `ShippingStep` — renders the fetched rates as radios (label + `formattedPrice` + delivery estimate); on select → set method; updates the order total.
- `PaymentStep` — renders the fetched payment methods (title + icon); on select → set method; handles the gateway-redirect case.
- `ReviewStep` — read-only summary (items, both addresses, shipping, payment, totals) + terms checkbox + **Place Order** button.
- `OrderSummary` — sticky sidebar (desktop) / collapsible drawer (mobile) with live totals; re-renders from the server cart after each step.

Anti-pattern: one giant component that fetches everything and holds all state inline — it becomes untestable and re-renders the world on every keystroke.

---

## 5. Step-by-step API flow

Each step: the endpoints (REST + the GraphQL field), what it does, and the UX. **Open the linked api-docs page for the exact body/response.**

### Step 1 — Addresses
- **REST:** `GET /api/shop/checkout-addresses` (address applied to the session) · `POST /api/shop/checkout-addresses` (save)
- **GraphQL:** query `collectionGetCheckoutAddresses` · mutation `createCheckoutAddress`
- **Send:** the input is **flat scalar fields**, not nested `{ billing{}, shipping{} }` (nested is rejected). Billing (all required): `billingFirstName`, `billingLastName`, `billingEmail`, `billingAddress`, `billingCity`, `billingCountry`, `billingState`, `billingPostcode`, `billingPhoneNumber`, plus `useForShipping` (Boolean). When `useForShipping=false`, also send the `shipping*` equivalents (`shippingFirstName` … `shippingPhoneNumber`).
- **Returns:** the saved checkout address (+ `success`/`message`; GraphQL also echoes `cartToken`).
- **UX:** email first (guest), then country **early** — country/region constrains shipping and the available states. Validate on blur. Docs: [set address](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/set-billing-address), [get addresses](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-addresses).

### Step 2 — Shipping method
- **REST:** `GET /api/shop/checkout-shipping-methods` (rates) · `POST /api/shop/checkout-shipping-methods` (set)
- **GraphQL:** query `collectionShippingRates` · mutation `createCheckoutShippingMethod`
- **Send (set):** `{ shippingMethod }` — the method code, e.g. `flatrate_flatrate`.
- **Returns:** rates carry `code` / `label` / `method` / `description` / `price` / `formattedPrice`; set returns `{ success, id, message }`.
- **UX:** **fetch rates only after the address is saved** (they depend on it). Radios with label + `formattedPrice` + estimate; re-fetch rates if the address changes; recompute the total on select. Docs: [get shipping methods](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-shipping-methods), [set shipping method](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/set-shipping-method).

### Step 3 — Payment method
- **REST:** `GET /api/shop/payment-methods` (supported) · `POST /api/shop/checkout-payment-methods` (set)
- **GraphQL:** query `collectionPaymentMethods` · mutation `createCheckoutPaymentMethod`
- **Send (set):** `{ paymentMethod }` (e.g. `moneytransfer`) plus optional `paymentSuccessUrl` / `paymentFailureUrl` / `paymentCancelUrl` for offsite gateways.
- **Returns:** methods carry `method` / `title` / `description` / `icon` / `isAllowed`; set returns `{ success, message, paymentGatewayUrl, paymentData }`.
- **CRITICAL — always fetch, never hardcode.** Admins enable/disable methods; availability varies by region/config. Map the returned `method` codes to friendly names via `title`/`icon` from the API, not a local map.
- **Offsite gateways:** if set returns a non-null `paymentGatewayUrl`, **redirect the browser there** (pass your success/failure/cancel URLs) and complete the order on return. For on-site methods (`moneytransfer`, `cashondelivery`) it's null — proceed to review. Docs: [get payment methods](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-payment-methods), [set payment method](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/set-payment-method).

### Step 4 — Review & place order
- **REST:** `POST /api/shop/checkout-orders`
- **GraphQL:** mutation `createCheckoutOrder(input: {})` → `{ id, orderId }`
- **Returns:** the created order's `orderId` (use it for the confirmation route).
- **Validates server-side:** cart has items · billing + shipping addresses set · shipping method selected · payment method selected · stock/inventory available. Any unmet prerequisite or stock issue → error (don't lose the user's progress). Docs: [place order](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/place-order).

---

## 6. Payment redirect handling

For offsite gateways the flow forks after **Set payment method**:

1. `createCheckoutPaymentMethod` returns `paymentGatewayUrl` (+ `paymentData`).
2. Redirect the browser to `paymentGatewayUrl`; the gateway processes payment.
3. Gateway returns to your `paymentSuccessUrl` / `paymentFailureUrl` / `paymentCancelUrl`.
4. On success, place the order (`createCheckoutOrder`) — or the gateway/webhook finalises it, per the method.

Never handle raw card data in your UI (PCI). Let the gateway own the card form.

---

## 7. Mobile checkout

- Single-column layout; correct input types (email/number/tel keyboards); large touch targets (≥44–48px).
- Make digital/offsite wallet methods prominent (fastest path).
- Collapsible order summary that keeps the form in focus; **sticky Place Order button** with `env(safe-area-inset-bottom)` so iOS doesn't clip it.
- Accordion the steps to reduce scrolling. (See the cross-cutting mobile reference for safe-area + sticky patterns.)

---

## 8. Trust & conversion

- Near the CTA: secure-checkout badge, payment-method icons (use the API `icon`), return/refund link, support contact.
- Reduce friction: progress indicator, guest checkout, minimal fields, free-shipping threshold messaging, "less than 2 minutes" framing.
- Auto-save each completed step to the cart (the API already persists it) so a refresh doesn't lose progress.

---

## 9. Error handling

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Out-of-order step (e.g. shipping before address) | wrong-step / sequence error | Gate the route on the prerequisite; if it slips through, send the user back to the missing step with a message. |
| Missing/invalid field | 422 validation | Inline field errors; scroll to the first error on submit. |
| Payment declined / gateway error | payment error | Keep entered data; show the gateway message; suggest another method. |
| Out of stock / quantity reduced at place-order | stock/inventory error | Update the line item, recalculate totals, tell the user what changed before they retry. |
| Network timeout | — | Retry without re-entry; never double-submit the order (disable the button while in flight). |

Standard statuses: **200/201** success · **401** unauthenticated (missing key/token) · **403** forbidden · **400** bad input · **404** not found · **422** validation.

---

## 10. Post-order cleanup (CRITICAL)

After `createCheckoutOrder` succeeds, the old cart is consumed — your UI must not keep showing it:

1. Clear cart state from your global store.
2. Discard the **guest `cartToken`** (and any stored cart id) — it's spent; a new cart needs a new token.
3. Invalidate cart queries (e.g. `queryClient.invalidateQueries({ queryKey: ['cart'] })`).
4. Redirect to the confirmation page using the returned `orderId`.

Skip this and the cart popup/badge keeps showing the just-ordered items.

---

## 11. GraphQL notes

- Shop endpoint: `POST /api/graphql` (storefront key required; customer/cart token per call).
- **Select the result fields the endpoint documents** — checkout mutations return small result objects (`success` / `message` / `id` / `orderId` / `paymentGatewayUrl`), not a full fetchable entity. Use the fields shown on each mutation's docs page; don't assume a generic `id` selection works the same across mutations.
- Inputs are **camelCase** (`billingFirstName`, `shippingMethod`, `paymentMethod`); one field per line in selection sets.

---

## 12. Checklist

**Flow & sequence**
- [ ] UI mirrors the cart state machine: Address → Shipping → Payment → Review → Place Order.
- [ ] Each step's route/section is gated on its prerequisite (no items → cart; no address → step 1).
- [ ] Server cart treated as source of truth; UI re-reads it after each mutation.

**Addresses**
- [ ] Billing captured; `useForShipping` toggle; separate shipping form when off.
- [ ] Country/region captured early (constrains shipping + states).
- [ ] Validate on blur; scroll to first error on submit.

**Shipping (CRITICAL: fetch from backend)**
- [ ] Rates fetched **after** address saved, via `GET /checkout-shipping-methods`.
- [ ] Rates re-fetched when the address changes.
- [ ] Selected method saved (`POST /checkout-shipping-methods { shippingMethod }`); total updated.

**Payment (CRITICAL: fetch from backend)**
- [ ] Methods fetched via `GET /payment-methods`; never hardcoded.
- [ ] Friendly name/icon taken from the API (`title`/`icon`), not a local map.
- [ ] Offsite gateway: redirect on non-null `paymentGatewayUrl` with success/failure/cancel URLs.
- [ ] No raw card data handled in the UI (PCI).

**Review & place**
- [ ] Review shows items, both addresses, shipping, payment, full total breakdown, terms checkbox.
- [ ] Place Order calls `POST /checkout-orders`; button disabled while in flight (no double-submit).
- [ ] All prerequisites met before enabling Place Order.

**Errors & edge cases**
- [ ] Out-of-stock / quantity-reduced handled at place-order with a clear message.
- [ ] Payment decline keeps data + suggests alternatives.
- [ ] 401/403/422 mapped to user-friendly messages.

**Post-order (CRITICAL)**
- [ ] Cart state cleared; guest `cartToken`/cart id discarded; cart queries invalidated.
- [ ] Redirect to `/order-confirmation/<orderId>`.

**Mobile & a11y**
- [ ] Single-column, correct keyboards, ≥44px targets, sticky CTA with safe-area inset.
- [ ] ARIA on fields (`aria-required`, `aria-invalid`); `aria-live` on total/error updates; keyboard navigable.

**Both transports**
- [ ] Works for guest (`cartToken`) and logged-in (`customerToken`); storefront key always sent.
- [ ] GraphQL selections use the documented result fields; inputs camelCase.
