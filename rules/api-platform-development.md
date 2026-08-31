# Bagisto API Platform (REST + GraphQL)

- CRITICAL: use the `bagisto-api-develop` skill when installing / removing / extending the `bagisto-api` package; use `bagisto-api-shop` or `bagisto-api-admin` when building an app or UI on the API.
- Two surfaces: **Storefront** — `/api/shop/*` (REST) + `/api/graphql`, authed by the `X-STOREFRONT-KEY` header (plus a customer or guest-cart Bearer token for cart/account calls). **Admin** — `/api/admin/*` (REST) + `/api/admin/graphql`, authed by a pre-issued admin Integration Bearer token. The admin API mirrors the admin panel menu-for-menu.
- The api-docs (`https://api-docs.bagisto.com` and its `/llms.txt` index) are the source of truth for exact request/response shapes — open the endpoint page; never invent a payload from memory.
- GraphQL `id` is selectable only on fetchable (noun) resources (product, customer, order). Action/result mutations (cart writes, place-order, cancel, comment) return result fields (`cartId`, `orderId`, `success`, `message`) — never `id`. GraphQL inputs are camelCase.
- Admin collections return a `{ data, meta }` envelope; storefront paginated collections expose `X-Total-*` headers; page size is `?per_page=N` (+ `?page=N`).
- Extending the package: REST + GraphQL share the same Provider/Processor — any change to one must keep the other working, so run the resource's GraphQL test before the REST test. Mirror the admin panel, not a superset. No auto-commit — the user commits.
