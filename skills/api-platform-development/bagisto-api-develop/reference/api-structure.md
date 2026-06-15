# API structure — surfaces, transports, declaring a resource

## Two surfaces × two transports

| Surface | REST prefix | GraphQL endpoint | Auth |
|---------|-------------|------------------|------|
| **Storefront (shop)** | `/api/shop/*` | `POST /api/graphql` | `X-STOREFRONT-KEY` header (+ a customer or guest-cart Bearer token for cart/account calls) |
| **Admin** | `/api/admin/*` | `POST /api/admin/graphql` | `Authorization: Bearer <id>|<token>` (pre-issued admin Integration token) |

The shop and admin GraphQL endpoints are **physically separate** (separate middleware + auth + scoped schema). A change to one surface must not leak types into the other.

Built on **API Platform for Laravel** + `webonyx/graphql-php`. Auth is Laravel **Sanctum** for customers and the custom **`admin-api` guard** (`AdminApiGuard`) for admin Integration tokens.

## Declaring a resource (the `#[ApiResource]` model)

A single Model class declares **both** transports. Shape:

```php
#[ApiResource(
    routePrefix: '/api/shop',                              // or build admin routes under src/Admin
    normalizationContext: ['skip_null_values' => false],   // REQUIRED on Eloquent-backed resources
    operations: [
        new Get,
        new GetCollection(provider: YourProvider::class),
        new Post(processor: YourProcessor::class, openapi: /* requestBody + responses examples */),
        new Delete(processor: YourProcessor::class),
    ],
    graphQlOperations: [
        new Query(resolver: BaseQueryItemResolver::class),
        new QueryCollection(provider: YourProvider::class, paginationType: 'cursor', extraArgs: [/* every custom filter */]),
        new Mutation(name: 'create', input: CreateYourInput::class, output: YourModel::class, processor: YourProcessor::class),
        new Mutation(name: 'delete', input: DeleteYourInput::class, output: YourModel::class, processor: YourProcessor::class),
    ],
)]
```

Routing facts that bite if missed:
- **REST `Post` hands the Processor the Model instance**, not a DTO — build the DTO from `request()->input()` inside the processor. **GraphQL `Mutation` hands it the input DTO.** A processor that serves both must branch on `$data` type + `$operation` instance.
- **GraphQL mutation field name = `<name><ResourceShortName>`** — `Mutation(name: 'create')` on `AdminCart` → `createAdminCart`; `Mutation(name: 'addItem')` → `addItemAdminCart`.
- **`QueryCollection` does NOT auto-expose custom filter args** — declare each in `extraArgs`.
- **Never set a custom `name:` on `QueryCollection`** — API Platform auto-pluralises the shortName; a custom name throws "Operation 'collection_query' not found" and (because one combined schema is built) takes the whole GraphQL endpoint down.
- A `Get`/detail op declared with a separate `output:` DTO **500s on the GraphQL `id`** — return the resource itself (the "Invoice template" in the package `CLAUDE.md`).
- Disambiguate literal sub-routes from `{id}` with `requirements: ['id' => '\\d+']` (so `/export`, `/tree`, `/mass-delete` aren't captured by `{id}`).
- **Declare the export `Get` op LAST** (after the detail `Get`) — GraphQL builds the node `id` IRI from the first `Get`, so an `/export` op declared first corrupts every node id.

## Read vs write path

- **Provider** (`ProviderInterface`) = the read path. Auth check → query (filter by `customer_id` + `channel_id` for customer-scoped shop resources) → eager-load → paginate → map. Storefront uses `ApiPlatform\State\Pagination\Pagination`; admin extends `AbstractAdminCollectionProvider` / `AbstractAdminItemProvider`.
- **Processor** (`ProcessorInterface`) = the write path. Auth → permission gate → validation → repository call → fire Bagisto core events → return. Mirror the Bagisto core controller/request/repository for the feature; fire the same events so core listeners (notifications, indexers, cache flushers) still run.

## Exception → HTTP status

| Exception | REST status | GraphQL | Use for |
|-----------|-------------|---------|---------|
| `AuthenticationException` | 401 | `errors[]` | Missing/invalid token |
| `AuthorizationException` | 403 | `errors[]` | Authenticated but not permitted / cross-user |
| `InvalidInputException` | 400 (or pass an explicit status, e.g. 409/422) | `errors[]` | Missing/invalid input, business-rule violation, wrong-step sequence |
| `ResourceNotFoundException` | 404 | `errors[]` | Entity not found |
| `ValidationException` | 422 | `errors[]` | Form-level validation failure |
| `OperationFailedException` | 500 | `errors[]` + `null` data | GraphQL remove that must return `null` with a message |

## REST response conventions

- GET collection → 200; GET single → 200; POST create → 201; DELETE → 204 (or 200 + body when returning data).
- **Null fields are always included** — every Eloquent-backed `#[ApiResource]` sets `normalizationContext: ['skip_null_values' => false]`.
- Pagination: `?per_page=N` (+ `?page=N`), default 10, cap 50. Admin collections wrap as `{ data, meta }`; both surfaces expose `X-Total-Count` / `X-Page` / `X-Per-Page` / `X-Total-Pages`.

## Feature surface map (points OUT — don't inline the full list)

The admin API mirrors the Bagisto admin panel menu-for-menu; the shop API covers the storefront journey. **The exhaustive, per-endpoint list is the source of truth — do not re-derive it here:**

- **Package `CLAUDE.md` coverage tables** — every endpoint with its operations, decisions, and quirks (package-facing).
- **`https://api-docs.bagisto.com` + `/llms.txt`** — the consumer-facing index + exact request/response shapes.

High-level menus (open the sources above for the actual endpoints):

- **Shop** — catalog (categories/products/search/reviews/booking slots), cart + coupons, checkout (addresses → shipping → payment → place order), customer account (auth, profile, addresses, orders, wishlist, compare), plus countries/channels/CMS/newsletter/contact.
- **Admin → Sales** — Orders (list/detail/cancel/comment/invoice/shipment/refund + Create-Order draft-cart flow), Invoices, Shipments, Refunds, Transactions, Bookings (+ CSV export per datagrid).
- **Admin → Catalog** — Products (datagrid + CRUD + images/inventory/customer-group-prices), Categories, Attributes, Attribute Families.
- **Admin → Customers** — Customers (CRUD + addresses/notes/impersonate), Groups, Reviews, GDPR.
- **Admin → Marketing** — Cart Rules + Coupons, Catalog Rules, Email Templates, Events, Campaigns, Subscribers, Search Terms/Synonyms, URL Rewrites, Sitemaps.
- **Admin → CMS** — Pages.
- **Admin → Settings** — Currencies, Channels, Locales, Exchange Rates, Inventory Sources, Tax Rates/Categories, Roles, Users, Themes, Data-Transfer Imports.
- **Admin → Configuration / Dashboard / Reporting** — config read+write, dashboard stats, reporting (sales/customers/products + export).
- **Admin → Integration** — the API token management UI + audit history (the package's own admin surface).
