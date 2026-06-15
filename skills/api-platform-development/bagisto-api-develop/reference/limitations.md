# Limitations — what the API will and won't do

## Guiding principle — parity with admin, not a superset

The API mirrors **what the Bagisto admin panel / storefront can do, no more.** When core lacks a feature, the API **matches that gap with an explicit error** rather than half-extending. Why: integrators expect API ↔ UI consistency; extending beyond core means owning surface area that breaks when core catches up (forcing a later breaking change); a clear "not supported" error is more honest than a partial implementation. When core adds the feature, remove the block and follow core's shape.

Concretely: before building a feature, confirm the admin UI (or storefront) actually exposes it. If it doesn't (e.g. no mass-action on a given datagrid, no booking partial in Create-Order), the API doesn't add it either — block with a clear message.

## Known limitations to honour

- **Binary uploads are REST-only.** File/image uploads (product images, import files, multipart config fields) go through REST multipart; the matching GraphQL mutation rejects with 422 pointing to REST (JSON GraphQL can't carry binary). PDF print + CSV export endpoints are REST-only too (no GraphQL counterpart for binary streams).
- **GraphQL action mutations have no selectable `id`.** Cart writes, place-order, draft-cart, cancel, comment, mass-actions return result fields (`cartId`/`orderId`/`success`/`message`), not `id`. Selecting `id` errors.
- **GraphQL nested item lists are plain JSON arrays, not cursor connections** — query `items { id sku }`, not `items { edges { node } }`.
- **Booking products are blocked in admin Create-Order** (HTTP 400) — core ships no booking partial in the Create-Order screen, so the API matches that gap.
- **Admin Create-Order place-order accepts only `cashondelivery` / `moneytransfer`** — same restriction the core Create-Order screen hardcodes (gateway methods like Stripe/PayPal can't be admin-finalised).
- **Some actions are intentionally not exposed** where the admin UI has none (e.g. no mass-delete on resources whose datagrid lacks one; reviews/subscribers/search-terms have no create — they originate on the storefront). Always check the core datagrid/controller before assuming an action exists.
- **Configuration writes are scope-locked** — every key must start with the posted `slug.`; validation is resolved server-side from `system_config()`, never trusted from the client. Custom blade-rendered config fields are read-only.

## Deferred / out of scope (don't build without product sign-off)

- Elasticsearch branch of the admin product datagrid (DB path only for now).
- Hosted/remote MCP server (a local doc-search MCP is the only MCP in scope).
- Encrypted-at-rest config secrets (core has no encryption flag).
- Image/file upload for resources where only a path-string is currently accepted (locales logo, channel logo/favicon, theme images, user avatar) — use the admin panel for binary uploads until a dedicated sub-resource ships.

When unsure whether something is in scope, check the package `CLAUDE.md` (it records every conscious "intentionally not covered" decision with the reason) before building.
