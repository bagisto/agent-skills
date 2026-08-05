# Product listing flow

The top of the catalog funnel — how a shopper discovers products. This flow covers **categories** (the navigation backbone), the **product list / grid**, **search**, **filtering**, **sorting**, and **pagination**. It feeds directly into the product detail page and add-to-cart, so get the IDs and tokens flowing through cleanly.

> **Source of truth for exact shapes:** this page gives you the flow, endpoints, query params, and UX. For the precise request/response body of any call, open its api-docs page (linked per step). **Never hardcode a payload or field list from memory — open the page.**

- **Auth:** listing/search/category calls are **public reads** — only `X-STOREFRONT-KEY` is required. No customer or cart token needed to browse. (Wishlist/compare flags on product cards only populate when a customer Bearer is also sent.)
- Everything here is a **read** — cache aggressively, server-render the first page for SEO.

---

## 1. Flow architecture & structure

The catalog is two cooperating surfaces — a **category navigation tree** and a **product collection** that you filter, sort, and page through:

```
  ┌─────────────────────┐
  │  CATEGORY NAV        │  GET /api/shop/category-trees   (nested tree → menu/sidebar)
  │  (menu + sidebar)    │  GET /api/shop/categories       (flat list, paginated)
  └─────────────────────┘
        │ user picks a category (categoryId)  ── or types a search term ── or lands on /shop
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  PRODUCT COLLECTION                                               │
  │  GET /api/shop/products                                           │
  │    ?query=        full-text (SKU or name)                         │
  │    ?category_id=  scope to a category                             │
  │    ?sort= ?page= ?per_page=   sort + paginate                     │
  │    ?price=from,to ?new=1 ?featured=1                              │
  │    ?color= ?size= ?brand= …  attribute facets                    │
  └─────────────────────────────────────────────────────────────────┘
        │ renders product cards (id, name, price, image, flags)
        ▼
  click a card ──▶ product-details.md   ·   quick-add ──▶ add-to-cart.md
```

**Recommended client architecture**

- **Routing** — a category route (`/category/[slug]` or `?category_id=`), a search route (`/search?query=`), and a generic shop route. Keep the active filters/sort/page in the **URL query string** so a listing is shareable, back-button-correct, and server-renderable.
- **State** — the URL *is* your filter state. Hydrate the data layer from `searchParams`; don't keep a parallel client copy that can drift.
- **Data layer** — wrap the products call in a query (e.g. TanStack Query) keyed by the full filter set (`{ query, category_id, sort, page, per_page, …facets }`). Server-fetch page 1 for SEO; client-fetch subsequent pages/filter changes. Cache categories/tree for the session — they rarely change.
- **Don't hardcode facets.** Available attribute filters (color/size/brand/material/…) come from the catalog config; any query param outside the reserved set (`query, sort, order, page, per_page, locale, channel, filter`) is treated as a filterable attribute automatically. Discover the attribute set from `GET /api/shop/attributes` (see product-details for attribute discovery).

---

## 2. Categories: tree vs flat list

Two endpoints, two jobs:

| Need | REST | GraphQL field | Returns |
|------|------|---------------|---------|
| Nested menu / mega-nav / sidebar tree | `GET /api/shop/category-trees` | `treeCategories(parentId:)` | An **array of nested category nodes** with `children[]` — not paginated. Pass `parentId` to scope to one branch; omit for roots. |
| Flat, paginated category index | `GET /api/shop/categories` | `categories` (cursor) | A paged flat list. **Children-by-parent:** REST accepts `?parent_id=N`; the GraphQL `categories` field has **no** `parentId` argument — use `treeCategories(parentId:)` (row above) for children. |
| Single category (banner, SEO copy) | `GET /api/shop/categories/{id}` | `category(id:)` | One category with its translations. |

- The **tree** is what you render in the header mega-menu and the listing-page sidebar. The **flat list** is for an "all categories" index or a typed filter.
- Categories list/tree are **status-filtered server-side** — admin-disabled categories never appear, so you don't filter them yourself.
- Docs: [tree categories](https://api-docs.bagisto.com/api/graphql-api/shop/queries/tree-categories), [categories list](https://api-docs.bagisto.com/api/graphql-api/shop/queries/categories), [single category](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-category) · REST: [get categories](https://api-docs.bagisto.com/api/rest-api/shop/categories/get-categories), [category tree](https://api-docs.bagisto.com/api/rest-api/shop/categories/get-category-tree).

---

## 3. Decision points & variants

| Decision | Guidance |
|---|---|
| **Search vs browse** | Both hit the **same** products endpoint. Browse = `?category_id=`; search = `?query=`. They compose — a category page with a search box just adds `query` to the existing filters. |
| **Server-side vs client-side filtering** | Always **server-side** — the API owns price ranges, stock, and attribute facets. Never fetch the whole catalog and filter in JS; it breaks pagination, totals, and stock accuracy. |
| **REST vs GraphQL pagination** | REST returns count **headers** (`X-Total-*`) + a flat array → classic numbered pages. GraphQL returns **cursor** connections (`edges`/`pageInfo`) → infinite scroll / "load more". Pick per the client's transport (see §6). |
| **Default sort** | The API has a sensible default; expose a sort dropdown with the documented tokens (`name-asc`, `name-desc`, `price-asc`, `price-desc`, `created_at-desc`, …). Reflect the chosen token in the URL. |
| **New / featured rails** | `?new=1` and `?featured=1` power "New arrivals" / "Featured" home-page rails — same endpoint, just a boolean filter. |

---

## 4. UI/UX

### Component breakdown

- **`CategoryNav`** — header mega-menu + listing sidebar, rendered from `treeCategories`. Highlight the active branch; collapse deep levels on mobile.
- **`Toolbar`** — result count (from `X-Total-Count` / `pageInfo`), sort dropdown, view toggle (grid/list), active-filter chips with one-tap clear.
- **`FilterSidebar`** — price range, attribute facets (color swatches, size pills, brand checkboxes), new/featured toggles. Each change updates the URL → refetch. Show a count next to applied filters.
- **`ProductGrid`** — responsive grid of `ProductCard`s. Reserve image aspect ratio to avoid layout shift.
- **`ProductCard`** — image (`baseImageUrl`), name, price (`formattedPrice`; show struck-through original + `formattedSpecialPrice` when on sale), badges (New/Sale/Featured), wishlist + compare buttons, quick-add. Link the card to the product detail page by `id`.
- **`Pagination`** — numbered pages (REST) or a "Load more" / infinite-scroll sentinel (GraphQL cursor).

### What the card renders
The list payload is a slim card shape: `id`, `sku`, `type`, `name`, `urlKey`, `price`/`formattedPrice`, `specialPrice`/`formattedSpecialPrice`, `minimumPrice`/`maximumPrice` (configurable/bundle ranges), `new`, `featured`, `baseImageUrl`, `isSaleable`, plus `isInWishlist`/`isInCompare` (only meaningful for logged-in customers). Render the `formatted*` currency strings — don't format prices yourself.

### Empty & loading states
- **No results** — friendly "no products match" + the applied filters as removable chips + a "clear all" reset. Never a blank grid.
- **Loading** — skeleton cards matching the final grid, not a spinner, to avoid layout jump.
- **First paint** — server-render page 1 (SEO + perceived speed); hydrate filters client-side.

### Mobile
- Filters live in a **bottom-sheet / drawer** triggered by a sticky "Filter" + "Sort" bar, not an always-open sidebar. Apply on close; show the active-filter count on the trigger.
- 2-column grid; large tap targets on cards and facet pills (≥44px).
- Infinite scroll generally beats numbered pages on mobile (works naturally with GraphQL cursors).

### Accessibility
- Facet groups as `role="group"` with a labelled legend; checkboxes/radios keyboard-operable.
- `aria-live="polite"` on the result count so screen readers hear "120 products" update after a filter change.
- Each card is a single focusable link with an accessible name (product name + price); badges have text alternatives.

### Trust & conversion
- Show the **result count** and active filters so shoppers trust the scope.
- Surface sale/new badges and stock state (`isSaleable`) on the card to drive clicks.
- Keep the URL shareable (filters in query string) so a curated link works.

---

## 5. Step-by-step API flow

Each step: REST path + GraphQL field, what it does, what it returns, and the docs link. **Open the linked page for the exact body/response.**

### Step 1 — Category navigation
- **REST:** `GET /api/shop/category-trees` (nested) · `GET /api/shop/categories` (flat) · `GET /api/shop/categories/{id}` (single)
- **GraphQL:** `treeCategories(parentId:)` · `categories` · `category(id:)`
- **Does:** returns the category structure for menus, the sidebar, and category landing copy.
- **Returns:** tree nodes carry `id`, name, `urlKey`, `children[]`; flat/single carry the category fields + translations.
- Docs: [tree categories](https://api-docs.bagisto.com/api/graphql-api/shop/queries/tree-categories) · [categories](https://api-docs.bagisto.com/api/graphql-api/shop/queries/categories) · REST [category tree](https://api-docs.bagisto.com/api/rest-api/shop/categories/get-category-tree), [get categories](https://api-docs.bagisto.com/api/rest-api/shop/categories/get-categories).

### Step 2 — Product list / browse
- **REST:** `GET /api/shop/products?category_id=&sort=&page=&per_page=`
- **GraphQL:** `products(first:, after:, sortKey:, reverse:, filter:)`
- **Does:** returns the paginated product collection for a category or the whole shop.
- **Returns:** an array (REST) / `edges[].node` (GraphQL) of slim card payloads + pagination metadata.
- Docs: [get products (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-products) · REST [get products](https://api-docs.bagisto.com/api/rest-api/shop/products/get-products).

### Step 3 — Search
- **REST:** `GET /api/shop/products?query=<term>`
- **GraphQL:** `products(query: <term>, sortKey:, reverse:, first:)` (documented on the search-products page)
- **Does:** full-text match on SKU **or** product name; composes with category + facet filters.
- **Returns:** same card shape as browse.
- Docs: [search products (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/search-products) · REST [search products](https://api-docs.bagisto.com/api/rest-api/shop/products/search-product).

### Step 4 — Filter
- **REST:** add params to `GET /api/shop/products` — `?price=from,to` (e.g. `?price=10,200`), `?new=1`, `?featured=1`, and attribute facets like `?color=3&size=6&brand=38`. (`?price_from=` / `?price_to=` also accepted.)
- **GraphQL:** pass a JSON string to `filter:` e.g. `filter: "{\"category_id\":\"22\",\"price\":\"10,200\",\"color\":\"3\"}"`.
- **Does:** narrows the collection; multiple filters combine.
- **Returns:** the filtered card list + recomputed totals.
- Docs: [search products](https://api-docs.bagisto.com/api/rest-api/shop/products/search-product) (full param table) · [get products (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-products).

### Step 5 — Sort
- **REST:** `?sort=price-asc` (compound) **or** `?sort=price&order=asc` (split). Tokens: `name-asc/-desc`, `price-asc/-desc`, `created_at-asc/-desc`, `updated_at-*`, `id-*`.
- **GraphQL:** `sortKey:` (e.g. `PRICE`, `NAME`, `CREATED_AT`) + `reverse:` (`true` = descending).
- **Returns:** the same list, reordered. Reflect the active token in the URL/dropdown.

### Step 6 — Paginate
- **REST:** `?page=N&per_page=N` (default 30, capped at 50). Read totals from response **headers**: `X-Total-Count`, `X-Page`, `X-Per-Page`, `X-Total-Pages`.
- **GraphQL:** `first: N, after: "<endCursor>"`; read `pageInfo.hasNextPage` + `pageInfo.endCursor` and append `edges`.

---

## 6. Pagination: REST headers vs GraphQL cursor

| | REST | GraphQL |
|---|---|---|
| Request | `?page=2&per_page=20` | `products(first: 20, after: "<cursor>")` |
| Total count | `X-Total-Count` header | derive from loading until `hasNextPage` is false |
| Next page | `page + 1` | `after: pageInfo.endCursor` |
| Best UI fit | numbered pages | infinite scroll / "Load more" |

The count headers are CORS-exposed — read them client-side to render "Showing 1–20 of 137".

---

## 7. Errors & edge cases

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Missing storefront key | **401** | Ensure `X-STOREFRONT-KEY` is attached to every call. |
| Forbidden | **403** | Shouldn't occur on public reads; treat as a misconfigured key. |
| Bad filter value (e.g. malformed price range) | **400** | Validate/clean filter inputs before sending; reset the offending facet. |
| Category / product id not found | **404** | Show a "category not found" page; fall back to the shop root. |
| Validation (bad param shape) | **422** | Surface a friendly message; drop the bad param and retry. |
| Empty search/filter result | **200** (empty list) | Render the empty state with removable filter chips — not an error. |

Standard statuses: **200/201** success · **401** unauthenticated · **403** forbidden · **400** bad input · **404** not found · **422** validation.

---

## 8. GraphQL notes

- Shop endpoint `POST /api/graphql`; only the storefront key is needed for catalog reads.
- Catalog queries are **cursor-paginated** (`edges { node { … } }`, `pageInfo { hasNextPage endCursor }`); one field per line in selection sets.
- `products` powers both browse and search (`query:` arg); `treeCategories` returns a plain array (not a connection); `categories` / `category` are paginated/fetchable.
- The GraphQL node `id` is an IRI (e.g. `/api/shop/products/12`); `_id` is the raw integer. **Confirm the exact field/arg names on the docs page before writing the query.**

---

## 9. Checklist

**Categories**
- [ ] Mega-menu / sidebar rendered from `category-trees` (nested); flat list used only where a paged index is needed.
- [ ] Active category highlighted; admin-disabled categories never shown (server already filters).

**Listing & search**
- [ ] Products fetched via `GET /api/shop/products` (browse) / `?query=` (search) — same endpoint.
- [ ] All filtering/sorting done **server-side** via query params; never fetch-all-and-filter in JS.
- [ ] Filter + sort + page state lives in the **URL** (shareable, back-button-correct, SEO-friendly).

**Filters & facets (CRITICAL: don't hardcode)**
- [ ] Facets driven by catalog config; arbitrary attribute params (`color/size/brand/…`) forwarded automatically.
- [ ] Price range (`?price=from,to`), `new`, `featured` wired; active filters shown as removable chips.

**Pagination**
- [ ] REST: numbered pages from `X-Total-*` headers · GraphQL: cursor (`first`/`after` + `pageInfo`) for load-more.
- [ ] Page 1 server-rendered for SEO/perf; subsequent pages client-fetched.

**UI/UX**
- [ ] Product card renders `formatted*` prices (struck-through original on sale), New/Sale badges, stock (`isSaleable`), wishlist/compare, quick-add.
- [ ] Empty-result state with removable filter chips + reset; skeleton loading (no layout shift).
- [ ] Mobile filters in a drawer/bottom-sheet with active-filter count; ≥44px targets.

**Accessibility**
- [ ] Facet groups labelled; `aria-live` result count; each card a single focusable, accessibly-named link.

**Both transports & next steps**
- [ ] Card links to **product-details.md** by `id`; quick-add follows **add-to-cart.md** (option IDs come from the detail page).
- [ ] Storefront key sent on every call; GraphQL selections use documented fields; inputs camelCase.
