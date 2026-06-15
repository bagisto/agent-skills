# Customers menu

Everything the admin panel's **Customers** sidebar group manages: the customer records themselves (with their address books and notes), the customer **Groups** that price and segment them, the product **Reviews** queue, and the **GDPR** data-request queue. Build these as a set of `list → detail → action` screens; this page gives the flow, the per-resource endpoint tables, the UI/UX, and the checklists. **Open the linked api-docs page for each call's exact body/response — never invent a payload from memory.**

> **Auth & conventions:** every call carries the admin Integration Bearer token, listings come back as `{ data, meta }`, and a token is capped by its admin's role (a forbidden action → 403). All of that is in [`../connecting-to-the-api.md`](../connecting-to-the-api.md) — don't restate it per screen. GraphQL specifics (the action-mutation result-field rule, camelCase inputs, cursor pagination) are in [`../graphql.md`](../graphql.md). Doc base: `https://api-docs.bagisto.com`.

---

## 1. What this menu manages, and how it relates to the rest

| Sub-menu | Manages | Relates to |
|---|---|---|
| **Customers** | The customer record — profile, status, addresses, notes, plus "Login as Customer" (impersonate) | Every order is placed by a customer; the [Create-Order flow](../flows/create-order.md) starts by picking one here. Addresses prefill checkout. |
| **Groups** | Customer groups (general / wholesale / guest + your own) used to segment + price | [Cart Rules and Catalog Rules](./marketing.md) target groups; channels reference them; a customer always belongs to exactly one group. |
| **Reviews** | Moderation queue for product reviews written on the storefront | Reviews belong to a product (Catalog) and a customer; admin can only approve / disapprove / delete — they originate on the storefront. |
| **GDPR Requests** | The data-export / data-erasure request queue customers raise | Processing an erasure request cascades into deleting the customer record above. |

A customer record is the hub: it owns addresses, notes, orders, reviews, a wishlist, and a compare list. The detail endpoint embeds the headline counts so a customer "view" screen needs no follow-up calls.

---

## 2. The pattern (recap)

Each sub-menu is the same three-call shape covered in [`../connecting-to-the-api.md`](../connecting-to-the-api.md):

- **List** — `GET /api/admin/customers[/…]` → `{ data, meta }`; drive the table with `?page=` + `?per_page=` (default 10, cap 50) + that screen's filters (multiple filters are AND-combined).
- **Detail** — `GET …/{id}` → the full record with relations/counts embedded.
- **Action** — `POST/PUT/DELETE` for create/update/delete, plus per-record actions (impersonate, set-default address, process GDPR) and bulk mass-actions.

---

## 3. Customers

The core record. Datagrid lists slim rows; detail adds the address/order/spend totals.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers` | `adminCustomers` | [list](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/list) |
| Detail | `GET /api/admin/customers/{id}` | `adminCustomer` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/detail) |
| Create | `POST /api/admin/customers` | `createAdminCustomer` | [create](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/create) |
| Update | `PUT /api/admin/customers/{id}` | `updateAdminCustomer` | [update](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/update) |
| Delete | `DELETE /api/admin/customers/{id}` | `deleteAdminCustomer` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/delete) |
| Mass-delete | `POST /api/admin/customers/mass-delete` | `createAdminCustomerMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/mass-delete) |
| Mass-update-status | `POST /api/admin/customers/mass-update-status` | `createAdminCustomerMassUpdateStatus` | [mass-update-status](https://api-docs.bagisto.com/api/rest-api/admin/customers/main/mass-update-status) |
| Impersonate (Login as Customer) | `POST /api/admin/customers/{customerId}/impersonate` | `createAdminCustomerImpersonate` | [impersonate](https://api-docs.bagisto.com/api/rest-api/admin/customers/impersonate/create) |

**Create rules to surface in the form:** a customer group is required; choose to either auto-send credentials (the customer gets an email with a generated password) or supply a password yourself (required when not auto-sending). Email must be unique.

**Delete is guarded:** a customer with pending/processing orders can't be deleted (400). In mass-delete, blocked ids are skipped with a reason rather than aborting the whole batch — show the skipped list to the admin.

**Impersonate = "Login as Customer", headless.** In the panel this is a session login that drops the admin into the storefront as the customer. On the API there's no session, so this endpoint instead returns a short-lived **customer token** (expires in ~1 hour). Hand that token to your storefront client as the customer's Bearer to act on their behalf against the Shop API. Treat the returned token like a secret — show/copy it once, don't log it.

### Customer Addresses (sub-resource)

The customer's address book — also the source for prefilling Create-Order.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers/{customerId}/addresses` | `adminCustomerAddresses` | [list](https://api-docs.bagisto.com/api/rest-api/admin/customers/addresses) |
| Detail | `GET /api/admin/customers/{customerId}/addresses/{id}` | `adminCustomerAddress` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/customers/addresses/detail) |
| Create | `POST /api/admin/customers/{customerId}/addresses` | `createAdminCustomerAddress` | [create](https://api-docs.bagisto.com/api/rest-api/admin/customers/addresses/create) |
| Update | `PUT /api/admin/customers/{customerId}/addresses/{id}` | `updateAdminCustomerAddress` | [update](https://api-docs.bagisto.com/api/rest-api/admin/customers/addresses/update) |
| Delete | `DELETE /api/admin/customers/{customerId}/addresses/{id}` | `deleteAdminCustomerAddress` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/addresses/delete) |
| Set default | `POST /api/admin/customers/{customerId}/addresses/{id}/set-default` | `setDefaultAdminCustomerAddress` | — (mirrors update; empty body) |

**Ownership is enforced:** the `{customerId}` in the path must own the address `{id}`, or the call returns 403 — don't let a client edit addresses across customers via a fabricated URL. Setting one address default zeroes the default flag on the customer's others; you can also flip the default inline on create/update.

### Customer Notes (sub-resource)

Append-only internal notes shown on the customer view screen.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers/{customerId}/notes` | `adminCustomerNotes` | — (newest-first; `{ data, meta }`) |
| Create | `POST /api/admin/customers/{customerId}/notes` | `createAdminCustomerNote` | [create](https://api-docs.bagisto.com/api/rest-api/admin/customers/notes/create) |

Notes are append-only — each create inserts a new row, never overwrites. A note can optionally be flagged as "customer notified". An empty note is rejected (422).

---

## 4. Customer Groups

Segments that price and group customers. Three system groups (general / wholesale / guest) ship by default and are partly locked.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers/groups` | `adminCustomerGroups` | [list](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/list) |
| Detail | `GET /api/admin/customers/groups/{id}` | `adminCustomerGroup` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/detail) |
| Create | `POST /api/admin/customers/groups` | `createAdminCustomerGroup` | [create](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/create) |
| Update | `PUT /api/admin/customers/groups/{id}` | `updateAdminCustomerGroup` | [update](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/update) |
| Delete | `DELETE /api/admin/customers/groups/{id}` | `deleteAdminCustomerGroup` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/delete) |
| Mass-delete | `POST /api/admin/customers/groups/mass-delete` | `createAdminCustomerGroupMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/groups/mass-delete) |

**System-group rules (surface these as disabled/locked fields):**
- API-created groups are always user-defined — you can't make a system group through the API.
- On a system group, only the **name** is editable; changing its code is rejected (422).
- A system group **can't be deleted** (400), nor can any group that still **has customers** (400). Mass-delete skips blocked ids with a reason.
- Code must be unique and is validated (letters first, then letters/digits/underscore).

Detail adds a `customersCount`; the listing leaves it null to stay cheap.

---

## 5. Reviews

The moderation queue for product reviews written on the storefront. **No create** — reviews originate from customers; admin only moderates.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers/reviews` | `adminCustomerReviews` | [list](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/list) |
| Detail | `GET /api/admin/customers/reviews/{id}` | `adminCustomerReview` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/detail) |
| Update status | `PUT /api/admin/customers/reviews/{id}` | `updateAdminCustomerReview` | [update](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/update) |
| Delete | `DELETE /api/admin/customers/reviews/{id}` | `deleteAdminCustomerReview` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/delete) |
| Mass-delete | `POST /api/admin/customers/reviews/mass-delete` | `createAdminCustomerReviewMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/mass-delete) |
| Mass-update-status | `POST /api/admin/customers/reviews/mass-update-status` | `createAdminCustomerReviewMassUpdateStatus` | [mass-update-status](https://api-docs.bagisto.com/api/rest-api/admin/customers/reviews/mass-update-status) |

**Only the status is editable** — the title/comment/rating/images belong to the storefront author. Status is one of `pending` / `approved` / `disapproved`; any other value is rejected (422). The detail payload embeds the customer name/email, the product sku/name, and the review's images; the listing leaves images null.

---

## 6. GDPR Requests

The queue of customer-raised data requests (export or erasure). List → detail → set status / process / delete, plus an ad-hoc data export.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/customers/gdpr-requests` | `adminCustomerGdprRequests` | [list](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/list) |
| Detail | `GET /api/admin/customers/gdpr-requests/{id}` | `adminCustomerGdprRequest` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/detail) |
| Update | `PUT /api/admin/customers/gdpr-requests/{id}` | `updateAdminCustomerGdprRequest` | [update](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/update) |
| Delete | `DELETE /api/admin/customers/gdpr-requests/{id}` | `deleteAdminCustomerGdprRequest` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/delete) |
| Process | `POST /api/admin/customers/gdpr-requests/{id}/process` | `createAdminCustomerGdprProcess` | [process](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/process) |
| Download data | `POST /api/admin/customers/{customerId}/gdpr-download-data` | `createAdminCustomerGdprDownloadData` | [download-data](https://api-docs.bagisto.com/api/rest-api/admin/customers/gdpr/download-data) |

**Two distinct write paths — keep them separate in the UI:**
- **Update** is a pure metadata change — set the request `status` (allowed: pending / processing / declined / approved / revoked) and an optional message. Use it for "mark processing" or "decline". No destructive side effect.
- **Process** is the explicit, irreversible action — it approves the request and, for an **erasure** request, cascades the customer delete. It refuses to re-run on an already-approved or revoked request (422). Gate this behind a confirmation dialog.

**Download data** is ad-hoc (not tied to a request id) — it returns a JSON bundle of everything held about the customer (profile with secrets stripped, addresses, orders, reviews, wishlist, notes). Offer it as a "Download data" button on the customer view, not just inside the GDPR queue.

---

## 7. UI/UX

### Customers datagrid

- **Columns:** id, name, email, group, status, plus created date. The detail view is where order/address/spend totals live — don't expect them in the list rows.
- **Filters (AND-combined):** name (matches first/last), email, phone, customer group, status, channel, date-of-birth range, created-at range. More filters = a narrower result.
- **Sort:** id (default, newest first), email, first name.
- **Mass-actions:** select rows → mass-delete, mass-update-status (enable/disable). Surface the per-row skip reasons mass-delete returns.
- **Row actions:** view, edit, delete, and **Login as Customer** (impersonate) — the last opens the storefront with the returned customer token.

### Customer detail / edit

- Tabbed view: **profile** (with status + group), **addresses** (the address-book sub-resource, with set-default + add/edit/delete), **notes** (append-only list + add), and read-only headline counts (orders, addresses, amount spent).
- Edit form mirrors create minus the credentials choice; email uniqueness excludes the record itself.

### Groups / Reviews / GDPR datagrids

- **Groups:** small datagrid (code / name / user-defined flag). Lock code + delete on system groups; disable the delete button when `customersCount > 0`.
- **Reviews:** moderation table with status filter + rating + product/customer filters; a single-status dropdown per row and a bulk approve/disapprove/delete. Show the product and review body in the detail drawer.
- **GDPR:** queue filtered by status / type. Two buttons per row — a status dropdown (Update) and a prominent **Process** (confirm-gated) — plus a customer-level **Download data**.

### Mobile

- Single-column cards instead of wide tables; the most-used filter (name/email) pinned at top; row actions in an overflow menu. Confirm-gate every destructive/irreversible action (delete, mass-delete, GDPR process) with a clear sheet.

---

## 8. Errors

| Failure | HTTP / GraphQL | Handle by |
|---|---|---|
| Validation (missing/invalid field, duplicate email, bad group code, bad review status) | 422 | Inline field errors. |
| Delete customer with active orders | 400 | "This customer has pending orders and can't be deleted." |
| Delete system group / group in use | 400 | Disable the delete affordance; explain why. |
| Mass-action skips some ids | 200 (with `skipped`) | Show which rows were skipped and why. |
| Address edited across customers | 403 | Scope address calls to the owning customer. |
| GDPR process re-run on approved/revoked request | 422 | Disable Process once handled. |
| Role lacks the permission | 403 | "You don't have permission for this." |
| Unauthenticated (missing/expired token) | 401 | Re-issue the token in the panel. |
| Not found | 404 | — |

---

## 9. Checklist

**Customers**
- [ ] Datagrid wired with filters (name/email/phone/group/status/channel/DOB/created) + sort + pagination.
- [ ] Detail shows profile + address book + notes + order/address/spend totals.
- [ ] Create handles the credentials choice (auto-send vs supply password) + required group + unique email.
- [ ] Delete + mass-delete handle the active-orders guard (skip reasons surfaced).
- [ ] Mass-update-status (enable/disable) wired.
- [ ] **Login as Customer** (impersonate) returns + securely hands off the short-lived customer token.

**Addresses & notes**
- [ ] Address CRUD scoped to the owning customer; set-default wired; ownership 403 handled.
- [ ] Notes list (newest-first) + append-only create; empty note rejected.

**Groups**
- [ ] CRUD + mass-delete wired; system-group locks (code immutable, no delete) enforced in the UI.
- [ ] Delete disabled when the group has customers (`customersCount`).

**Reviews**
- [ ] List + detail + status update (pending/approved/disapproved) + delete + mass variants.
- [ ] No create surface (storefront-originated); only status is editable.

**GDPR**
- [ ] List/detail wired; Update (status) and Process (confirm-gated, irreversible erasure) kept distinct.
- [ ] Process re-run guard (422) handled; customer-level Download-data button surfaced.

**Both transports**
- [ ] Admin Bearer on every call; REST listings read `{ data, meta }`, GraphQL uses cursor pagination.
- [ ] GraphQL mutations select documented result fields (not a generic `id`); inputs camelCase.
