# Compare list

Lets a **logged-in customer** collect products into a side-by-side comparison (specs, price, availability). Like the wishlist, it's a small saved set the customer builds from cards/PDP and reviews on a dedicated compare page.

> **Source of truth:** [get-compare-items](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-compare-items) · [get-compare-item](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-compare-item) · [create-compare-item](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-compare-item) · [delete-compare-item](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-compare-item) · [delete-all-compare-items](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-all-compare-items). Open the page for the exact body/response before writing a call. (Compare endpoints have GraphQL docs only; for REST, mirror the same fields against the live endpoint.)

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List compare items | `GET /api/shop/compare-items` | `compareItems` |
| Get one item | `GET /api/shop/compare-items/{id}` | `compareItem` |
| Add a product | `POST /api/shop/compare-items` (`productId`) | `createCompareItem` |
| Remove one item | `DELETE /api/shop/compare-items/{id}` | `deleteCompareItem` |
| Clear the list | `POST /api/shop/delete-all-compare-items` | `createDeleteAllCompareItems` |

- **Auth:** `X-STOREFRONT-KEY` + `Authorization: Bearer <customerToken>` on every call. **No guest support.**
- Unlike the wishlist, the compare list is **not channel-scoped** — it's per customer across channels.

---

## 1. Flow

```
  product card / PDP "Compare" toggle
     │  logged in? ── no ──▶ login (remember the product), retry after
     │           └─ yes
     ▼
  POST /api/shop/compare-items { productId }   → item added
     │
  Compare page:  GET /api/shop/compare-items   → the set
     ├─ remove one   DELETE /api/shop/compare-items/{id}
     └─ clear all    POST /api/shop/delete-all-compare-items
```

There's **no toggle endpoint** here (unlike wishlist) — add with `create`, remove with `delete`. To make the compare icon behave like a toggle, track which products are in the list (seed from `compareItems` or the product's `isInCompare` flag) and call `create` or `delete` accordingly.

---

## 2. Status / behaviour handling

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Added | 200/201 + `success: true` | Activate the compare toggle, increment the compare badge. |
| Already in the list (create) | 200 (no-op) / `message` | Treat as success; show the active state. |
| Removed | 200/204 + `success`/`message` | Deactivate the toggle, decrement the badge, drop the column on the compare page. |
| Not logged in | 401 | Gate at the click: login, remember the product, retry after auth. |
| Item / product gone | 404 | Drop the stale row/column. |
| Cleared | 200 + `deletedCount` | Empty the compare page; show empty state. |

Read `success` + `message` (and `deletedCount` on clear-all) to confirm the action.

---

## 3. Showing the active state without a round-trip

Every product payload carries an **`isInCompare`** flag (`1`/`0`) for the authenticated customer — use it to render the compare toggle's active state immediately on listings and the PDP, without fetching the whole compare set first. Guests always get `0`. (See the wishlist's `isInWishlist` for the same pattern.)

---

## 4. UI/UX

- **Compare toggle on cards + PDP:** a clear "Add to compare / In compare" state, seeded from `isInCompare`. Optimistically flip, reconcile from the response.
- **Compare badge / tray:** a header count or a sticky "Compare (N)" tray; cap the practical number of columns (3–4 on desktop, fewer on mobile) and tell the user when the set is large.
- **Compare page:** a table with one column per product and rows for the comparable attributes (image, name, price, key specs, availability, add-to-cart). Pull the per-product spec values from the product detail payload. Each column has a **remove** affordance; a **Clear all** clears the set (confirm — destructive).
- **Add-to-cart from compare:** option-requiring products (configurable/bundle) route to the PDP for option selection; simple products can add inline.
- **Guest gating:** keep the toggle visible; intercept the click → login → return and complete. Don't silently no-op.
- **Empty state:** "Nothing to compare yet" + a link back to the catalog.
- **Mobile:** the table doesn't fit side-by-side — use a horizontally-scrollable column layout or a stacked per-attribute view; keep the remove control reachable.
- **a11y:** compare toggle is a button with `aria-pressed`; the comparison table uses proper header cells (`<th scope>`); announce add/remove via `aria-live`; Clear-all confirms.

---

## 5. GraphQL notes

- Queries: `compareItems` (cursor-paginated) and `compareItem` (single by id) — select the documented fields, one per line.
- Mutations: `createCompareItem(input: { productId })`, `deleteCompareItem(input: { id })`, `createDeleteAllCompareItems(input: {})`. Inputs camelCase.
- Action mutations — select documented result fields (`success`/`message`, the item, `deletedCount`), not a blind `id`.
- Customer Bearer token required on every operation.

---

## 6. Checklist

- [ ] Customer token sent on every compare call; guests gated at click (login → retry), toggle still visible.
- [ ] Add (`POST /compare-items` / `createCompareItem`) and remove (`DELETE /compare-items/{id}` / `deleteCompareItem`) wired; toggle behaviour driven by current membership.
- [ ] Toggle state seeded from the product's `isInCompare` flag; reconciled from each response.
- [ ] Compare page renders one column per product with comparable attribute rows; per-column remove + Clear-all (`/delete-all-compare-items`) wired.
- [ ] Add-to-cart from compare routes option-requiring products to the PDP.
- [ ] 401 handled by gating; 404 drops stale columns.
- [ ] Compare badge/tray with a sensible column cap; `aria-live` on changes; toggle uses `aria-pressed`; Clear-all confirms.
- [ ] Empty state handled; mobile layout (scroll/stack) handled; storefront key always sent.
