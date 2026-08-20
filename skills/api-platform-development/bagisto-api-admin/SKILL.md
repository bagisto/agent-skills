---
name: bagisto-api-admin
description: Use when building an admin app or UI on the Bagisto Admin API — a back-office dashboard, an order, catalog, customer, marketing, CMS or settings management screen, an admin mobile app, the Create-Order flow, or any admin panel page on the API. Ask the client's platform and stack first, and treat the api-docs as the source of truth for exact shapes. Trigger phrases include "admin orders", "admin products", "customers", "cart rules", "CMS", "settings", "reporting", "admin panel on the API".
license: MIT
metadata:
  author: bagisto
---

# Build an admin app on the Bagisto Admin API

Implement any admin/back-office interface on the Bagisto **Admin API** (`/api/admin/*` REST + `POST /api/admin/graphql`). The API mirrors the Bagisto admin panel **menu-for-menu**, so any admin screen can be rebuilt from it. This skill is a **router**: it gives the flow and points you at the per-menu reference page; the reference pages carry the endpoints, UI/UX, and checklists.

## ⚠️ Load these FIRST (before any code)

1. **`reference/connecting-to-the-api.md`** — admin auth (the Integration Bearer token), the `{data,meta}` listing envelope, the list→detail→action pattern, permissions, errors, and the verify-before-coding protocol.
2. **`reference/graphql.md`** — if the client picked GraphQL: the admin endpoint, the result-field/`id` rule, camelCase inputs + filter args, cursor pagination.

**The api-docs are the source of truth for exact shapes** — `https://api-docs.bagisto.com` (Admin API section) + its `/llms.txt` index. The reference pages name the endpoints and flow; **open the linked docs page for the precise body/response before writing the call. Never invent a payload from memory.**

## Step 1 — ask the client (CRITICAL, before building)

1. **Platform** — web, mobile (native/cross-platform), desktop?
2. **Framework/stack** — React/Next, Vue/Nuxt, Flutter, React Native, plain JS?
3. **Which admin menus** — Sales, Catalog, Customers, Marketing, CMS, Settings, Configuration, Dashboard/Reporting — or one first?
4. **Transport** — REST or GraphQL? (REST for list/detail/action screens; GraphQL when a screen needs many related fields in one round-trip. Both fully supported.)
5. **First screen/flow** — order list + actions, product management, Create-Order, a dashboard, …?

Confirm, then tailor everything to the answers. Don't assume a stack.

## The core admin pattern: list → detail → action

Almost every admin screen is the same shape (detailed in `connecting-to-the-api.md`):
- **List** — `GET /api/admin/<resource>` → `{ data, meta }` envelope; drive tables with `?page=` + `?per_page=` + the screen's filters.
- **Detail** — `GET /api/admin/<resource>/{id}` → full record, relations embedded (no follow-up calls).
- **Action** — `POST/PUT/DELETE` for create/update/delete + per-record actions (cancel order, create invoice, mass-update, …), each with its own eligibility rules.

## Step 2 — open the reference for the menu

### Flagship flow
| Page | Build this |
|------|-----------|
| `reference/flows/create-order.md` | The admin **Create-Order** flow (place an order for a customer via a draft cart) |

### Menus (mirror the admin sidebar)
| Page | Covers |
|------|--------|
| `reference/menus/sales.md` | Orders (list/detail + cancel/comment/invoice/shipment/refund), Invoices, Shipments, Refunds, Transactions, Bookings, CSV exports |
| `reference/menus/catalog.md` | Products (datagrid + CRUD + images/inventory/customer-group-prices + mass actions), Categories (+tree), Attributes (+options), Attribute Families |
| `reference/menus/customers.md` | Customers (CRUD + addresses/notes/impersonate), Groups, Reviews, GDPR |
| `reference/menus/marketing.md` | Cart Rules (+coupons), Catalog Rules, Email Templates, Events, Campaigns, Subscribers, Search Terms/Synonyms, URL Rewrites, Sitemaps |
| `reference/menus/cms.md` | CMS Pages |
| `reference/menus/settings.md` | Currencies, Channels, Locales, Exchange Rates, Inventory Sources, Tax Rates/Categories, Roles, Users, Themes, Data-Transfer Imports |
| `reference/menus/configuration.md` | Store configuration (schema / values / update) |
| `reference/menus/dashboard-reporting.md` | Dashboard stats + Reporting (sales/customers/products + export) |

## Discovery — don't hardcode the nav or permissions

Two read-only endpoints (REST + GraphQL) tell you what the **current token** can do — drive navigation and action-gating from them instead of hardcoding:

- `GET /api/admin/menu` (`getAdminMenu`) — the admin sidebar as a permission-filtered tree; each node maps to its API endpoint (`apiResource: { rest, graphql }`, or `null` for group headers / panel-only screens).
- `GET /api/admin/permissions` (`getAdminPermissions`) — the token's effective `{ permissionType, permissions }` (`["*"]` = full access).

Details in `reference/connecting-to-the-api.md`.

## Consolidated critical rules

- **Verify before coding.** PAUSE → open the endpoint's docs page (or query the MCP) → confirm method/fields → implement → check types.
- **Auth:** every call sends `Authorization: Bearer <id>|<token>` (a pre-issued admin Integration token). There's **no login endpoint** — the token is made in the store's admin panel. The admin GraphQL endpoint is `POST /api/admin/graphql` (admin token only; **not** the shop endpoint, no storefront key).
- **Permissions:** a token is capped by its admin's role — an endpoint the role can't reach returns **403**. Build for that.
- **Listings are `{ data, meta }`** (+ `X-Total-*` headers); page with `?page=`/`?per_page=` (default 10, cap 50) + the per-screen filters.
- **GraphQL action mutations** (cancel/invoice/shipment/refund/place-order/cart writes/mass-actions) return **result fields**, not a generic `id`; inputs are camelCase; custom filter args are documented per page. See `reference/graphql.md`.
- **Don't hardcode dynamic data** (shipping/payment methods in Create-Order, config options) — fetch it.
