# Wishlist (save for later)

Lets a **logged-in customer** save products to a personal list, toggle the heart on a product card, move a saved item into the cart, and clear the list. **Guests have no wishlist** — every wishlist call needs a customer token; show the heart but route guests to login first.

> **Source of truth:** [get-wishlists](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-wishlists) · [toggle-wishlist](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/toggle-wishlist) · [create-wishlist](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-wishlist) · [delete-wishlist](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-wishlist) · [move-wishlist-to-cart](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/move-wishlist-to-cart) · [delete-all-wishlists](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-all-wishlists). Open the page for the exact body/response before writing a call — never invent a payload. (The wishlist endpoints have GraphQL docs only; for REST, mirror the same fields against the live endpoint.)

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List wishlist | `GET /api/shop/wishlists` | `wishlists` |
| Get one item | `GET /api/shop/wishlists/{id}` | `wishlist` |
| Add a product | `POST /api/shop/wishlists` (`productId`) | `createWishlist` |
| Toggle (add/remove) | `POST /api/shop/wishlists/toggle` (`productId`) | `toggleWishlist` |
| Remove one item | `DELETE /api/shop/wishlists/{id}` | `deleteWishlist` |
| Move item to cart | `POST /api/shop/move-wishlist-to-carts` | `moveWishlistToCart` |
| Clear the list | `POST /api/shop/delete-all-wishlists` | `createDeleteAllWishlists` |

- **Auth:** `X-STOREFRONT-KEY` + `Authorization: Bearer <customerToken>` on **every** call. No guest support.
- Wishlist membership is **per channel** — the same customer can wishlist a product on one channel and not see it on another.

---

## 1. Flow

```
  product card / PDP heart
     │  logged in? ── no ──▶ redirect to login (remember the product), retry after
     │           └─ yes
     ▼
  POST /api/shop/wishlists/toggle { productId }
     │   added   → fill the heart, badge++
     │   removed → outline the heart, badge--
     ▼
  Wishlist page:  GET /api/shop/wishlists  → list
     ├─ move to cart   POST /api/shop/move-wishlist-to-carts  → item leaves wishlist, lands in cart
     ├─ remove one     DELETE /api/shop/wishlists/{id}
     └─ clear all      POST /api/shop/delete-all-wishlists
```

**Toggle vs add:** prefer `toggle` for the heart icon — one endpoint covers both directions, so you don't track "is it already saved?" before deciding. Use `create` only where the intent is strictly "add" (e.g. a "Save" button that should be idempotent-add). The toggle response tells you which way it went; reflect that in the icon.

---

## 2. Status / behaviour handling

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Added | 200/201 + `success: true` | Fill the heart, increment the wishlist badge, optional toast "Saved". |
| Removed (toggle) | 200 + `success: true` | Outline the heart, decrement the badge. |
| Not logged in | 401 | Don't call — gate at the click: redirect to login, remember the product, retry the toggle after auth. |
| Item already there (create) | 200 (no-op) / `message` | Treat as success; show the saved state. |
| Moved to cart | 200 + `success: true` | Remove the row from the wishlist list, bump the cart badge, confirm "Moved to cart". |
| Item / product gone | 404 | Drop the stale row and tell the user it's no longer available. |

Always read `success` + `message` from the response — they're the confirmation the action took.

**`/api/shop/move-to-wishlists` is a different thing:** that operation moves items **out of the cart** into the wishlist (GraphQL-only — `MoveToWishlist`). It belongs to the cart surface (see [cart](../flows/cart.md)), not the product/wishlist heart. Don't wire the PDP heart to it.

---

## 3. Showing the saved state without a round-trip

Every product payload already carries an **`isInWishlist`** flag (`1`/`0`) for the authenticated customer on the current channel — so a listing or PDP can render the correct heart state immediately, without cross-referencing the separately-paginated wishlist list. Use that flag to seed the icon; call `toggle` on click and reconcile from the response. For guests the flag is always `0`.

---

## 4. UI/UX

- **Heart on cards + PDP:** filled = saved, outline = not. Optimistically flip on click, then reconcile from the response; revert on error.
- **Header badge:** count of saved items, kept in sync with toggles and move-to-cart. `aria-live="polite"` so screen readers hear the change.
- **Wishlist page:** grid/list of saved products with image, name, price, stock/availability, **Move to cart** and **Remove**, plus a **Clear all** action (with a confirm step — it's destructive).
- **Move to cart:** for products that need options (configurable/bundle), moving may need the option choices — if the API requires them, route to the PDP or an option mini-form instead of a silent move. For simple products it's one click.
- **Guest gating:** keep the heart visible (don't hide the feature) but intercept the click → login → return and complete the save. Losing the user's intent ("I clicked save and nothing happened") is the worst outcome.
- **Empty state:** friendly "Your wishlist is empty" + continue-shopping link; never a blank grid.
- **Mobile:** the heart must be a comfortable tap target; the wishlist page is a single-column list with swipe-or-button remove.
- **a11y:** the heart is a toggle button with `aria-pressed`; announce add/remove and move-to-cart via `aria-live`; Clear-all needs an explicit confirm.

---

## 5. GraphQL notes

- Queries: `wishlists` (cursor-paginated collection) and `wishlist` (single by id) — select the documented fields, one per line.
- Mutations: `createWishlist(input: { productId })`, `toggleWishlist(input: { productId })`, `deleteWishlist(input: { id })`, `moveWishlistToCart(input: { … })`, `createDeleteAllWishlists(input: {})`. Inputs are camelCase.
- These are **action mutations** — select the documented result fields (`success`/`message`, the wishlist item, `deletedCount` for delete-all), not a blind `id`.
- Every wishlist operation requires the **customer Bearer token**; an unauthenticated call fails.

---

## 6. Checklist

- [ ] Customer token sent on every wishlist call; guests gated at click (login → retry), feature still visible.
- [ ] Heart wired to `toggle` (`POST /wishlists/toggle` / `toggleWishlist`); add-only paths use `create` where appropriate.
- [ ] Icon state seeded from the product's `isInWishlist` flag; reconciled from each toggle response.
- [ ] Wishlist page lists items via `GET /wishlists`; remove (`DELETE /wishlists/{id}`), move-to-cart (`/move-wishlist-to-carts`), clear-all (`/delete-all-wishlists`) wired.
- [ ] Move-to-cart removes the row, bumps the cart badge; option-requiring products routed to the PDP, not silently moved.
- [ ] `move-to-wishlists` (cart→wishlist) kept on the cart surface, not the PDP heart.
- [ ] 401 handled by gating, not by erroring; 404 drops stale rows.
- [ ] Header badge + `aria-live`; heart is a toggle button with `aria-pressed`; Clear-all confirms.
- [ ] Empty state handled; mobile tap targets sized; storefront key always sent.
