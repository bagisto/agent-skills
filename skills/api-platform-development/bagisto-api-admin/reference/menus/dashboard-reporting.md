# Dashboard & Reporting menu

The analytics surface — the landing **Dashboard** that greets an admin on login, and the deeper **Reporting** screens (Sales, Customers, Products) behind it. Both are **read-only** and **type-driven**: a single endpoint per screen returns one of several stat groups, picked by a `?type=` parameter, scoped by a date window and channel. There are no writes here — build dashboards, charts, and tables.

> **Source of truth for exact shapes:** this page gives the flow and the endpoints. For the precise stat structure each `type` returns, open the linked api-docs page. **Never hardcode a response shape from memory.**

- Auth, permissions, and errors are covered once in [connecting-to-the-api](../connecting-to-the-api.md); GraphQL behaviour in [graphql.md](../graphql.md). Every call sends `Authorization: Bearer <id>|<token>`. These screens have **no permission gate** beyond a valid token — any authenticated admin can read them.

---

## 1. The shared parameters

Every endpoint below accepts the same window controls:

- **`?type=`** — **the key parameter.** It selects *which* stat group to return (e.g. total sales vs. top-selling products). Each screen has its own set of valid types; a default applies when omitted. Treat one `type` as one widget/panel and fire one call per panel.
- **`?start=` / `?end=`** — ISO dates bounding the window (default: roughly the last 30 days). The helpers compare the chosen window against the previous one to compute progress.
- **`?channel=`** — a channel code to scope the figures to one storefront.

GraphQL passes the same as query args. Build a single shared "date range + channel" control at the top of the analytics area and feed it to every panel's call.

---

## 2. Dashboard

The login landing screen — headline KPIs and recent-activity widgets.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| Stats | `GET /api/admin/dashboard/stats?type=` | `statsAdminDashboard` |

- `?type=` selects one of the dashboard's stat groups (overall figures, today's figures, top-selling products, etc.); the default is the overall group. Each returns a `type` + the date range + a `statistics` payload shaped for that group.
- An unknown `type` returns `400` — drive your panels from a fixed list of the valid types, not user input.
- One of the today's-orders widgets returns pre-rendered HTML for its line items — render it as markup or ignore it; don't try to parse it as structured data.
- Docs: [stats](https://api-docs.bagisto.com/api/rest-api/admin/dashboard/stats). GraphQL: [stats](https://api-docs.bagisto.com/api/graphql-api/admin/dashboard/stats).

---

## 3. Reporting

Three deep-dive screens plus an overview, each driven by `?type=`. Sales/Customers/Products additionally expose a **View Details** table form and a **CSV export**.

| Screen | Stats (panel data) | View Details (full table) | CSV export |
|--------|--------------------|---------------------------|------------|
| Overview | `GET /api/admin/reporting/stats?type=` | — | — |
| Sales | `GET /api/admin/reporting/sales?type=` | `GET /api/admin/reporting/sales/view?type=` | `GET /api/admin/reporting/sales/export?type=&format=csv` |
| Customers | `GET /api/admin/reporting/customers?type=` | `GET /api/admin/reporting/customers/view?type=` | `GET /api/admin/reporting/customers/export?type=&format=csv` |
| Products | `GET /api/admin/reporting/products?type=` | `GET /api/admin/reporting/products/view?type=` | `GET /api/admin/reporting/products/export?type=&format=csv` |

GraphQL fields:

| Screen | Stats query | View query |
|--------|-------------|------------|
| Overview | `statsAdminReportingOverview` | — |
| Sales | `statsAdminReportingSales` | `viewStatsAdminReportingSales` |
| Customers | `statsAdminReportingCustomers` | `viewStatsAdminReportingCustomers` |
| Products | `statsAdminReportingProducts` | `viewStatsAdminReportingProducts` |

- **Overview** returns a small shortlist of headline figures across all three concerns — use it for the Reporting landing page. Sales/Customers/Products each expose a richer set of `?type=` stat groups (total sales, orders, refunds, tax/shipping collected, top payment methods; customer counts, traffic, top customers/groups; sold quantities, top sellers by revenue/quantity, most-reviewed/visited products, search terms). Open the screen's docs page for its full type list.
- **Stats vs. View Details:** the `/stats` call returns the **summary** for a panel (charts + top-N). The `/view` call returns the same `?type=` in **table form** — full columns + the complete record set behind the panel, for a "View Details" drill-down screen.
- **CSV export** streams the table form of a stat as a `text/csv` attachment. It's **REST-only** (binary), accepts only `?format=csv`, and takes the same `?type=` as the screen. Send `Accept: text/csv`.
- Docs: [overview](https://api-docs.bagisto.com/api/rest-api/admin/reporting/overview), [sales](https://api-docs.bagisto.com/api/rest-api/admin/reporting/sales), [customers](https://api-docs.bagisto.com/api/rest-api/admin/reporting/customers), [products](https://api-docs.bagisto.com/api/rest-api/admin/reporting/products). GraphQL: [sales](https://api-docs.bagisto.com/api/graphql-api/admin/reporting/sales), [products](https://api-docs.bagisto.com/api/graphql-api/admin/reporting/products).

---

## 4. UI/UX

- **Dashboard = a grid of widgets**, one call per widget keyed by `type`. Render KPI cards (value + the progress-vs-previous figure the API computes), a trend chart, and the recent-activity / top-sellers lists. Lazy-load panels so a slow stat doesn't block the page.
- **Reporting = panel screen + drill-down.** Each reporting screen shows its `?type=` panels (cards + charts) from `/stats`; a "View Details" link opens the full table from `/view` (same `type`, table shape) with client-side paging/sort; an "Export" button downloads the CSV.
- **Shared window control.** One date-range picker (+ channel selector) at the top of the analytics area; changing it re-fires every visible panel's call. Cache panel responses keyed by `type + start + end + channel`.
- **Charts.** Map the `statistics` series to your chart library; show the date range the response echoes so the user knows the window. Format money/percentages from the values as given.
- **Mobile.** Stack KPI cards one-per-row; make charts horizontally scrollable or swap to compact sparklines; collapse the View Details table into stacked cards.
- **Empty windows.** A date range with no activity returns zeroed/empty stats — render a friendly "no data for this period" rather than a broken chart.

---

## 5. Errors

| Status | When | UX |
|--------|------|----|
| 200 | Stats returned | — |
| 400 | Unknown `?type=` | Drive panels from a fixed valid-type list, not free input |
| 401 | Missing/expired/revoked token | Re-issue the token in the admin panel |
| 406 | Export requested without `Accept: text/csv` | Set the Accept header |
| 422 | Export `?format=` other than `csv` | Only `csv` is supported |

---

## 6. Build checklist

- [ ] One shared date-range + channel control feeding every panel's `start`/`end`/`channel`.
- [ ] Dashboard: a widget grid, one call per `type` from a fixed valid-type list; render KPI cards + charts + activity lists; handle the HTML line-item widget.
- [ ] Reporting overview: a landing page from `statsAdminReportingOverview` / `GET /reporting/stats`.
- [ ] Sales / Customers / Products: `?type=` panels from `/stats`; a "View Details" table from `/view`; an "Export" CSV button (`Accept: text/csv`, `format=csv`, REST only).
- [ ] Cache panels keyed by `type + start + end + channel`; render empty-window states; map `400` to "invalid view".
