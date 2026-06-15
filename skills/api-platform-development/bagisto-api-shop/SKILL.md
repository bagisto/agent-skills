---
name: bagisto-api-shop
description: "ALWAYS use when building a STOREFRONT app or UI on the Bagisto Shop API — a customer-facing storefront, catalog, cart, checkout, customer account, wishlist, compare, reviews, or ANY page/component of a shop on the API (web, mobile, or custom). Also when the user mentions products, cart, checkout, coupons, customer login/account, wishlist, or 'storefront on the API'. Routes each task to a reference page; asks the client's platform/stack first; treats the api-docs as the source of truth for exact shapes."
license: MIT
metadata:
  author: bagisto
---

# Build a storefront on the Bagisto Shop API

Implement any customer-facing storefront — catalog, cart, checkout, account, wishlist, compare — on the Bagisto **Shop API** (`/api/shop/*` REST + `POST /api/graphql`). This skill is a **router**: it tells you the flow and points you at the reference page for each feature; the reference pages carry the architecture, UI/UX, endpoints, and a checklist.

## ⚠️ Load these FIRST (before any code)

1. **`reference/connecting-to-the-api.md`** — auth (storefront key + cart/customer tokens), the `{data,meta}`/header pagination, error codes, and the **verify-before-coding protocol**.
2. **`reference/graphql.md`** — if the client picked GraphQL: the result-field/`id` rule, camelCase inputs, cursor pagination.

**The api-docs are the source of truth for exact request/response shapes** — `https://api-docs.bagisto.com` and its `/llms.txt` index. The reference pages name the endpoints and flow; **open the linked docs page for the precise body/response before writing the call. Never invent a payload from memory.**

## Step 1 — ask the client (CRITICAL, before building)

1. **Platform** — web, mobile (native/cross-platform), desktop?
2. **Framework/stack** — React/Next, Vue/Nuxt, Flutter, React Native, Swift/Kotlin, plain JS?
3. **Transport** — REST or GraphQL? (REST for simple screens; GraphQL when a screen needs many related fields at once. Both fully supported.)
4. **First feature/flow** — catalog, cart+checkout, account, …?

Confirm, then tailor everything to the answers. Don't assume a stack.

## Step 2 — open the reference for the feature

### Flows (multi-step journeys / pages)
| Page | Build this |
|------|-----------|
| `reference/flows/product-listing.md` | Categories, product list, search, filters |
| `reference/flows/product-details.md` | Product page (per-type option discovery, reviews, related) |
| `reference/flows/add-to-cart.md` | Add-to-cart per product type |
| `reference/flows/cart.md` | Mini-cart + cart page (read/update/remove/merge/totals) |
| `reference/flows/checkout.md` | Address → shipping → payment → place order |
| `reference/flows/order-confirmation.md` | Post-order thank-you page |
| `reference/flows/authentication.md` | Register, login, logout, verify, forgot/change password |
| `reference/flows/account.md` | Profile + address book |
| `reference/flows/customer-orders.md` | Order history, detail, cancel, reorder, invoices, downloadables |

### Features (single capabilities)
| Page | Build this |
|------|-----------|
| `reference/features/coupons.md` | Apply / remove coupon |
| `reference/features/wishlist.md` | Wishlist add/toggle/list/move-to-cart |
| `reference/features/compare.md` | Compare list |
| `reference/features/reviews.md` | Product reviews + the customer's own reviews |
| `reference/features/newsletter.md` | Newsletter subscribe |
| `reference/features/contact-us.md` | Contact form |
| `reference/features/storefront-context.md` | Countries/states, channels, currencies, locales, CMS pages, themes |

Each page = **overview → flow architecture → UI/UX → step-by-step API (with the exact endpoints) → errors → checklist.** Follow it; it defers exact shapes to the api-docs.

## Consolidated critical rules (the gotchas that bite)

- **Verify before coding.** PAUSE → open the endpoint's docs page (or query the MCP) → confirm the method/fields → implement → check types. Don't guess endpoint names or bodies.
- **Auth per surface.** Every shop call sends `X-STOREFRONT-KEY`; cart/account/checkout calls also send `Authorization: Bearer <cartToken | customerToken>`. Guests mint a cart token first (`POST /api/shop/cart-tokens`).
- **Mutating cart/checkout calls return the full updated cart** — reconcile your UI from the response, don't mutate locally.
- **Guest→customer merge on login** (`merge-carts`) or the guest's items are lost.
- **Post-order cleanup** — clear cart state + discard the guest cart token after a placed order, or the cart popup shows stale items.
- **GraphQL:** select the documented **result fields** of action mutations (`success`/`message`/`orderId`/totals), not a generic `id`; inputs are camelCase; one field per line. See `reference/graphql.md`.
- **Don't hardcode dynamic data** (shipping/payment methods, prices, options) — fetch it from the API.
