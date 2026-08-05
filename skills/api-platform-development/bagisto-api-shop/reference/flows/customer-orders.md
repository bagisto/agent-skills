# Customer orders flow

Everything that happens *after* a customer places an order: the **order history** list, the **order detail** view (items, addresses, payment, shipments), and the post-purchase actions — **cancel**, **reorder**, **invoice PDFs**, and **downloadable-product** files. This is the "My Orders" area of the account.

> **Source of truth for exact shapes:** this page gives you the flow, the endpoints, and the UX. For the full request/response body of any call, open its api-docs page (linked per step). **Never hardcode a payload from memory — open the page.**

Every endpoint here is **customer-token only** — all require `Authorization: Bearer <customerToken>` plus the storefront key, and the server scopes results to the authenticated customer (a customer can never read another's orders). See [authentication.md](./authentication.md) for the token and [connecting-to-the-api.md](../connecting-to-the-api.md) for the header model.

---

## 1. Flow architecture & structure

Order history is a **list → detail** drill-down with branch actions off the detail view. Invoices and downloadables are sibling lists that reference the same orders:

```
   logged-in customer (Bearer <customerToken>)
        │
        ▼
   ┌──────────────────────┐  GET /api/shop/customer-orders            (paginated history)
   │   ORDER HISTORY       │
   └──────────────────────┘
        │  open an order
        ▼
   ┌──────────────────────┐  GET /api/shop/customer-orders/{id}
   │   ORDER DETAIL        │  embeds items · addresses · payment · shipments
   └──────────────────────┘
        ├── cancel        POST /api/shop/cancel-order   { orderId }   (if eligible)
        ├── reorder       POST /api/shop/reorder        { orderId }   → items back in cart → checkout.md
        └── shipments     GET  /api/shop/customer-order-shipments[/{id}]   (tracking)

   ┌──────────────────────┐  GET /api/shop/customer-invoices[/{id}]
   │   INVOICES            │  ──▶ PDF: GET /api/shop/customer-invoices/{id}/pdf
   └──────────────────────┘

   ┌──────────────────────┐  GET /api/shop/customer-downloadable-products[/{id}]
   │   DOWNLOADABLES       │  ──▶ file: GET /api/shop/customer-downloadable-products/{id}/download
   └──────────────────────┘
```

**Recommended client architecture**

- **Routing** — nested under the account shell: `/account/orders` (list), `/account/orders/[id]` (detail), `/account/invoices`, `/account/downloads`. All inherit the account area's auth guard.
- **State** — customer-scoped query cache keyed `['orders', page]`, `['order', id]`, `['invoices']`, `['downloads']`. Orders are mostly read-only, so cache aggressively; **invalidate `['order', id]` and `['orders']` after a cancel** (status changes) and **invalidate `['cart']` after a reorder** (items added).
- **Pagination** — the list uses the storefront pattern: `?page=N` + `?per_page=N` with `X-Total-Count` / `X-Page` / `X-Per-Page` / `X-Total-Pages` headers (GraphQL uses cursor pagination — `edges`/`pageInfo`). See the connecting + graphql pages.
- **One component per surface** — `OrderList`, `OrderRow`, `OrderDetail`, `OrderStatusTimeline`, `OrderItemsTable`, `InvoiceList`, `DownloadableList`.

---

## 2. Order history (list)

- **REST:** `GET /api/shop/customer-orders`
- **GraphQL:** query `customerOrders` (cursor: `first` / `after`, `edges { node }`, `pageInfo`)
- **Returns:** a paginated list of the customer's orders — per order: id, increment id, status, totals (with `formatted*`), item count, dates. Slim by design; open one for the full picture.
- **Docs:** [get customer orders](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-orders), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customer-orders/get-customer-orders).
- **UX:** a table/list (most recent first) with order number, date, status **chip** (color-coded: pending/processing/completed/cancelled), total, and a "View" action. Support paging + optional status filter. **Empty state:** "No orders yet" with a "start shopping" link.

---

## 3. Order detail

- **REST:** `GET /api/shop/customer-orders/{id}`
- **GraphQL:** query `customerOrder(id:)` — the `id` is the **IRI** (`/api/shop/customer-orders/{id}`), **not** `incrementId`. Read a row's `id` from the `customerOrders` list (it returns both `id` and `incrementId`) and pass that IRI here.
- **Returns:** the full order with **embedded** sub-objects — `items` (with product info, qty, line totals, and type-specific extras), `addresses` (billing + shipping), `payment` (method + title), and `shipments` (with their items). No follow-up calls needed for the core view.
- **Docs:** [get customer order](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-order), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customer-orders/get-customer-order).
- **UX (the order page):**
  - **Header:** order number, placed date, status, and the available actions (cancel / reorder).
  - **Status timeline:** a horizontal stepper (Placed → Processing → Shipped → Completed; or a Cancelled state) derived from the order status — gives the customer "where is my order?" at a glance.
  - **Items table:** thumbnail, name + variant options, unit price, qty, line total (use the API `formatted*` fields).
  - **Addresses:** billing + shipping cards.
  - **Totals breakdown:** subtotal, discount, tax, shipping, grand total — all from `formatted*`.
  - **Shipments panel:** carrier/tracking + which items shipped (see §6).
  - **Invoices panel:** link each invoice to its PDF (see §5).

---

## 4. Cancel & reorder

These are the two write actions on an order. Both take the order id and are gated by eligibility.

### Cancel order
- **REST:** `POST /api/shop/cancel-order`
- **GraphQL:** mutation `createCancelOrder`
- **Send:** `{ orderId }` (the numeric order id).
- **Returns:** a success/message; the order moves to a cancelled state.
- **Docs:** [cancel order](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/cancel-customer-order).
- **Eligibility:** only some statuses are cancellable (e.g. pending/processing — not shipped/completed/already-cancelled). **Only show the Cancel button when the order is cancellable**; if the server still rejects, surface its message rather than a generic error. Confirm before cancelling; on success, invalidate the order + list caches so the status chip updates.

### Reorder
- **REST:** `POST /api/shop/reorder`
- **GraphQL:** mutation `createReorderOrder`
- **Send:** `{ orderId }` (the source order's numeric id).
- **Returns:** a success/message; the order's items are placed back into the customer's cart.
- **Docs:** [reorder](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/reorder-customer-order).
- **UX:** a "Buy again" / "Reorder" button on each past order. On success, **invalidate the cart query** and route the user to the cart (or open the mini-cart) so they see the re-added items, then continue via [checkout.md](./checkout.md). Some items may no longer be saleable — surface what couldn't be added rather than failing silently.

---

## 5. Invoices

- **List REST:** `GET /api/shop/customer-invoices` · **GraphQL:** query `customerInvoices`
- **Detail REST:** `GET /api/shop/customer-invoices/{id}` · **GraphQL:** query `customerInvoice`
- **Download PDF (REST):** `GET /api/shop/customer-invoices/{id}/pdf`
- **Returns:** invoice records (totals, dates, the parent order) — and crucially a **`downloadUrl`** field on the GraphQL invoice queries that points directly at the PDF endpoint above.
- **Docs:** [get invoices](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-invoices), [get invoice](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-invoice), [download invoice](https://api-docs.bagisto.com/api/graphql-api/shop/queries/download-invoice), [download PDF (REST)](https://api-docs.bagisto.com/api/rest-api/shop/customer-invoices/download-customer-invoice-pdf).
- **How download works:** the PDF lives behind an authenticated `GET …/{id}/pdf`. Over GraphQL you don't stream the binary — you read the `downloadUrl` from the invoice query and then fetch that URL **with the customer Bearer header** to get the PDF. There is no GraphQL "download" mutation; binary streams aren't expressible over GraphQL.
- **UX:** invoices appear as a panel on the order detail and/or a standalone invoices list. Each row → a **Download PDF** button that hits the authenticated PDF URL (open in a new tab / trigger a file download). Show a spinner while fetching; handle a 404 (invoice not yet generated) gracefully.

---

## 6. Shipments (tracking)

- **List REST:** `GET /api/shop/customer-order-shipments` · **GraphQL:** query `customerOrderShipments`
- **Detail REST:** `GET /api/shop/customer-order-shipments/{id}` · **GraphQL:** query `customerOrderShipment`
- **Returns:** shipment records — carrier title, tracking number, the shipped items and quantities, dates.
- **Docs:** [get shipments](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-order-shipments), [get shipment](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-order-shipment).
- **UX:** within the order detail's shipments panel, list each shipment with its carrier + tracking number (link out to the carrier's tracking page when you can) and which line items it covered. A partially-shipped order has multiple shipments — show them distinctly.

---

## 7. Downloadable products

For digital products, after the order is paid/completed the customer can fetch the actual files.

- **List REST:** `GET /api/shop/customer-downloadable-products` · **GraphQL:** query `customerDownloadableProducts`
- **Detail REST:** `GET /api/shop/customer-downloadable-products/{id}` · **GraphQL:** query `customerDownloadableProduct`
- **Download file (REST):** `GET /api/shop/customer-downloadable-products/{id}/download`
- **Returns:** purchase records — product name, the source order, download status/availability, and a **`downloadUrl`** on the GraphQL queries pointing at the download endpoint above.
- **Docs:** [get downloadable products](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-downloadable-products), [get downloadable product](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-downloadable-product), [download product](https://api-docs.bagisto.com/api/graphql-api/shop/queries/download-downloadable-product).
- **How download works:** same pattern as invoices — read `downloadUrl` from the query, then `GET` that URL **with the customer Bearer header** to fetch the file. Availability can be gated (download count limits, order not yet completed) — only enable the button when the record says it's downloadable, and surface the reason when it isn't.
- **UX:** a "My Downloads" list — product name, purchase date, remaining downloads (if limited), and a **Download** button per row. Disable + explain when not yet available (e.g. "Available once your order is completed").

---

## 8. UI/UX cross-cutting

- **Status as color-coded chips** everywhere an order status appears (list rows, detail header, timeline) — consistent palette across the app.
- **Actions reflect eligibility:** render Cancel only when cancellable, Download only when available, Reorder always (but report unavailable items). Don't show a button the API will reject.
- **Mobile:** the orders table collapses to stacked cards (number + date + status + total + chevron); the detail view is a single scroll column; download/PDF buttons trigger the platform's file handling.
- **Accessibility:** the orders list is a table/list with proper roles; status chips carry a text label (not color alone); action buttons have discernible names ("Cancel order #1042", "Download invoice PDF"); `aria-live` announces cancel/reorder results; keyboard-operable throughout.
- **Loading/empty:** skeleton rows while the list loads; friendly empty states for no-orders / no-invoices / no-downloads.

---

## 9. Errors

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Not logged in / token expired | 401 | Clear session, redirect to login (see authentication page). |
| Accessing another customer's order/invoice/file | 403 | Block; the token scopes you to your own data — never expose another account's. |
| Order/invoice/shipment/download id not found | 404 | Friendly not-found; usually a stale link — refresh the list. |
| Cancel on an ineligible order | 422 | Hide the button when ineligible; surface the server's message if it still rejects. |
| Reorder with no-longer-saleable items | 422 | Add what's available, tell the user what couldn't be re-added. |
| PDF/file not yet generated/available | 404 / 422 | Disable the button with a reason; retry once available. |
| Bad request shape | 400 | Fix the request; surface a generic message. |

Standard statuses: **200/201** success · **401** unauthenticated · **403** forbidden · **400** bad input · **404** not found · **422** validation.

---

## 10. GraphQL notes

- Shop endpoint: `POST /api/graphql` (storefront key + customer Bearer per call). See [graphql.md](../graphql.md).
- Field names: `customerOrders` / `customerOrder` (history + detail), `createCancelOrder` / `createReorderOrder` (actions, input `orderId`), `customerInvoices` / `customerInvoice`, `customerOrderShipments` / `customerOrderShipment`, `customerDownloadableProducts` / `customerDownloadableProduct`.
- **Binary downloads aren't GraphQL operations.** Invoice PDFs and downloadable files are fetched via the authenticated REST URL exposed as the `downloadUrl` field on the GraphQL invoice/download queries — read the field, then `GET` the URL with the Bearer header.
- Cursor pagination on the list queries (`first`/`after`, `edges`/`node`, `pageInfo`); inputs camelCase; one field per line.

---

## 11. Checklist

**History & detail**
- [ ] Order list (`GET /customer-orders`) paginated; status chips; most-recent-first; empty state.
- [ ] Order detail (`GET /customer-orders/{id}`) renders embedded items, addresses, payment, shipments — no extra round-trips for the core view.
- [ ] Status timeline + totals breakdown from API `formatted*` fields.

**Actions**
- [ ] Cancel (`POST /cancel-order { orderId }`) shown only when eligible; confirmed; order+list caches invalidated on success.
- [ ] Reorder (`POST /reorder { orderId }`) adds items to cart; cart query invalidated; user routed to cart; unavailable items reported.

**Invoices & shipments**
- [ ] Invoice list/detail wired; PDF fetched via the authenticated `…/{id}/pdf` URL (or the GraphQL `downloadUrl`) with the Bearer header.
- [ ] Shipments shown per order with carrier + tracking + covered items; partial shipments handled.

**Downloadables**
- [ ] Download list wired; file fetched via `…/{id}/download` (or GraphQL `downloadUrl`) with the Bearer header.
- [ ] Download button disabled with a reason when not yet available; download-count limits surfaced.

**Auth & errors**
- [ ] All endpoints sent with the customer Bearer; entire area behind the auth guard; 401 → login.
- [ ] 403 never leaks another customer's data; 404 refreshes the list; cancel/reorder 422s surfaced with clear messages.

**UI/UX & a11y**
- [ ] Color-coded status chips with text labels; actions reflect eligibility; mobile cards + single-column detail.
- [ ] List/table roles; named action buttons; `aria-live` on action results; keyboard-operable; skeletons + empty states.

**Both transports**
- [ ] Works over REST and GraphQL; storefront key + customer Bearer always sent; binary downloads via the authenticated REST URL (never a GraphQL stream); cursor pagination + camelCase on GraphQL.
