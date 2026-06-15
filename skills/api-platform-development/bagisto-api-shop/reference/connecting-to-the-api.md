# Connecting to the Shop API

Read this before writing any call. It covers detecting the backend, auth, the verify-before-coding protocol, pagination, errors, and data-layer patterns. Exact request/response shapes always come from the api-docs endpoint page.

## 1. The backend + the docs

- REST base: `/api/shop/*`. GraphQL: `POST /api/graphql` (shop; separate from the admin endpoint).
- **Source of truth:** `https://api-docs.bagisto.com` + its `/llms.txt` index. Fetch `llms.txt` to discover the surface, then open the specific endpoint page for the exact body/response.
- Store the base URL + storefront key in env vars (`NEXT_PUBLIC_*`, `PUBLIC_*`, etc.). **Never expose admin/secret keys in client code** — the storefront key is the only key a shop client holds.

## 2. Verify-before-coding protocol (do this for every new call)

1. **PAUSE** — don't write the call from memory.
2. **QUERY** — open the endpoint's api-docs page (or query the MCP doc server).
3. **VERIFY** — confirm the exact path, method, required fields, and response shape.
4. **IMPLEMENT** — write the call with the verified shape.
5. **CHECK** — validate the response/types match.

This prevents silent failures from a wrong path or field name.

## 3. Authentication

| Scope | Headers |
|-------|---------|
| Any shop request | `X-STOREFRONT-KEY: <key>` |
| Guest cart / checkout (cart-keyed calls) | `X-STOREFRONT-KEY` **+** `Authorization: Bearer <cartToken>` |
| Logged-in customer (account, their cart, orders) | `X-STOREFRONT-KEY` **+** `Authorization: Bearer <customerToken>` |

- **Customer register:** `POST /api/shop/customers`. **Login:** `POST /api/shop/customer/login` → top-level `token` (format `<id>|<secret>`). **Logout:** `POST /api/shop/customer/logout`. See `flows/authentication.md`.
- **Guest cart token:** `POST /api/shop/cart-tokens` (GraphQL `createCartToken`) → `cartToken`; send it as the Bearer on every cart/checkout call until the order is placed (then discard it).
- **Guest→customer merge:** on login, merge the guest cart (`POST /api/shop/merge-carts`, guest cart `_id` as `cartId`, customer Bearer) or the items are lost.
- Document auth once; don't re-prompt the user per screen.

## 4. Pagination & response shape

- **Storefront collections** paginate with `?page=N` + `?per_page=N` and expose count headers: `X-Total-Count`, `X-Page`, `X-Per-Page`, `X-Total-Pages` (CORS-exposed — read them client-side).
- **Cart/checkout mutating calls return the full cart** (items + totals + `couponCode` + `success`/`message`) — reconcile your UI from the response.
- Null fields are included in responses (not stripped) — safe to read a field that's currently null.
- GraphQL collections use **cursor pagination** (`edges`/`node`, `pageInfo`) — see `graphql.md`.

## 5. Error handling

| Status | Meaning | UX |
|--------|---------|----|
| 200 / 201 | Success | — |
| 401 | Unauthenticated (missing key/token) | Mint/refresh token; for guest cart, create a new cart token |
| 403 | Forbidden (not your resource) | Block / redirect to login |
| 400 | Bad input | Fix the request; surface a friendly message |
| 404 | Not found (or invalid coupon code) | Inline "not found" / "invalid code" |
| 422 | Validation (e.g. qty exceeds stock, missing field) | Inline field/stock message; keep user input |

Map ecommerce errors (out of stock, payment declined, session expired) to friendly messages — never raw technical text.

## 6. Data-layer patterns

- Use a query library (e.g. TanStack Query) for all calls. Server-fetch initial page loads (catalog/SEO); client-fetch interactions (cart/account).
- Cache reads keyed by their inputs (catalog by filters, shipping rates by cart+address); **invalidate the cart query after any cart mutation**.
- Treat the **server cart as the source of truth**; optimistic UI is fine but reconcile to the returned cart.
- Use the store's official SDK if one exists; otherwise a thin typed fetch wrapper that always attaches the storefront key + current Bearer token.
