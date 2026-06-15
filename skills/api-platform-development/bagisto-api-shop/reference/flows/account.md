# Account flow

The customer's home base after login: their **profile** (name, contact details, password) and their **address book** (the saved billing/shipping addresses that pre-fill checkout). This is the "My Account" area minus orders — order history, invoices, and downloadables live on their own page, [customer-orders.md](./customer-orders.md).

> **Source of truth for exact shapes:** this page gives you the flow, the endpoints, and the UX. For the full request/response body of any call, open its api-docs page (linked per step). **Never hardcode a payload from memory — open the page.**

Every endpoint here is **customer-token only** — they all require `Authorization: Bearer <customerToken>` alongside the storefront key. See [authentication.md](./authentication.md) for how that token is minted, and [connecting-to-the-api.md](../connecting-to-the-api.md) for the header model (not repeated here).

---

## 1. Flow architecture & structure

The account area is two self-contained sub-surfaces hanging off a dashboard shell. Both read from the customer token; neither depends on the other:

```
   logged-in customer (Bearer <customerToken>)
        │
        ▼
   ┌──────────────────────────┐
   │   ACCOUNT DASHBOARD       │  shell: nav (Profile / Addresses / Orders…) + content pane
   └──────────────────────────┘
        ├── PROFILE
        │     GET  /api/shop/customer-profiles          → current customer
        │     PUT  /api/shop/customer-profile-updates/{id}   (edit details / password)
        │     POST /api/shop/customer-profile-deletes/{id}   (delete account)
        │
        └── ADDRESS BOOK
              GET    /api/shop/customer-addresses        → list
              GET    /api/shop/customer-addresses/{id}   → one
              POST   /api/shop/customer-addresses        → create
              PUT    /api/shop/customer-addresses/{id}   → update
              DELETE /api/shop/customer-addresses/{id}   → delete
```

**Recommended client architecture**

- **Routing** — a dashboard layout (`/account`) with nested routes (`/account/profile`, `/account/addresses`, `/account/addresses/new`, `/account/addresses/[id]`). All nested routes inherit the auth guard from the layout.
- **State** — keep the resolved `customer` and the address list in a customer-scoped query cache (e.g. TanStack Query keyed `['customer','profile']` and `['customer','addresses']`). **Invalidate the relevant key after every mutation** so the UI reflects the server, not a stale local copy.
- **Guarding** — the whole `/account` subtree is behind the protected-route gate; a 401 from any call clears the session and routes to login (see authentication page).
- **One component per concern** — `ProfileForm`, `AddressList`, `AddressCard`, `AddressForm` — each owning its own loading/error state.

---

## 2. Profile

### Read profile
- **REST:** `GET /api/shop/customer-profiles` (the singular alias `GET /api/shop/customer-profile` also resolves)
- **GraphQL:** query `getCustomerProfile`
- **Returns:** the authenticated customer — name, email, phone, gender, date of birth, newsletter flag, group, etc. The token identifies whose profile (no id needed).
- **Docs:** [get customer profile](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-profile), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/get-customer-profile).

### Update profile (including password)
- **REST:** `PUT /api/shop/customer-profile-updates/{id}`
- **GraphQL:** mutation `createCustomerProfileUpdate`
- **Send:** the editable fields — `firstName`, `lastName`, `email`, `phone`, `gender`, `dateOfBirth`, `subscribedToNewsLetter`. For a **password change**, additionally send `currentPassword`, `password`, `confirmPassword` (the backend verifies `currentPassword` first; `confirmPassword` must equal `password`).
- **Returns:** the updated customer (+ success/message).
- **Docs:** [update profile](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/update-customer-profile), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/update-customer-profile), [change password (REST)](https://api-docs.bagisto.com/api/rest-api/shop/customers/change-password).
- **Note:** there is no separate "change password" endpoint — it's this update call carrying the password trio. Keep the password change as its own form section/screen so a profile-detail save doesn't require the current password.

### Delete account
- **REST:** `POST /api/shop/customer-profile-deletes/{id}`
- **GraphQL:** mutation `createCustomerProfileDelete`
- **Send:** typically the customer's password to confirm (open the docs page for the exact required field).
- **Returns:** a success/message; on success the token is dead — clear all auth state and route to home.
- **Docs:** [delete customer profile](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-customer-profile), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/delete-customer-profile).

---

## 3. Address book

A customer can hold many saved addresses; one is the **default**. These are the addresses surfaced as "pick a saved address" during checkout — keeping the book tidy directly improves checkout speed.

| Operation | REST | GraphQL field | Body essentials |
|-----------|------|---------------|-----------------|
| List addresses | `GET /api/shop/customer-addresses` | `getCustomerAddresses` | — (token in Bearer) |
| Get one address | `GET /api/shop/customer-addresses/{id}` | (resolve via the list / item query) | — |
| Create address | `POST /api/shop/customer-addresses` | `createAddUpdateCustomerAddress` | address fields (see below) |
| Update address | `PUT /api/shop/customer-addresses/{id}` | `createAddUpdateCustomerAddress` | id + changed fields |
| Delete address | `DELETE /api/shop/customer-addresses/{id}` | `createDeleteCustomerAddress` | id |

Docs: [get addresses](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-addresses), [create address](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-customer-address), [update address](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/update-customer-address), [delete address](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-customer-address) · REST: [list](https://api-docs.bagisto.com/api/rest-api/shop/customers/get-customer-addresses), [create](https://api-docs.bagisto.com/api/rest-api/shop/customers/create-customer-address), [update](https://api-docs.bagisto.com/api/rest-api/shop/customers/update-customer-address), [delete](https://api-docs.bagisto.com/api/rest-api/shop/customers/delete-customer-address).

### Address fields (what you collect)
First/last name, company (optional), one or more street/address lines, city, **country** then **state/region**, postcode, phone — plus a "default address" flag. Open the create/update docs page for the exact field names before writing the form; the country/state pair is dynamic (states depend on the chosen country — fetch them, see [storefront-context.md](../features/storefront-context.md)).

> **GraphQL note:** create and update share one mutation field — **`createAddUpdateCustomerAddress`**. Sending an id updates that address; omitting it creates a new one. The REST surface splits them into `POST` (create) and `PUT /{id}` (update).

---

## 4. UI/UX

### Account dashboard layout
- **Desktop:** a two-pane layout — a left sidebar nav (Profile · Addresses · Orders · Downloadables · Log out) and a content pane. Highlight the active item.
- **Mobile:** the nav collapses to a list/menu screen; tapping an item pushes the detail screen with a back affordance. Don't cram the sidebar onto a phone.
- A small greeting header ("Hi, {firstName}") reassures the user they're in the right account.

### Profile form
- Group fields logically: **Personal details** (name, email, phone, gender, DOB, newsletter) as one savable section, **Password** as a separate section/screen requiring `currentPassword`.
- Pre-fill from the read-profile call; show a dirty-state indicator and disable Save until something changes.
- Newsletter as a single toggle. Email change may have side effects (login identity) — confirm it explicitly.
- Validate on blur; success → a transient toast + refresh the cached profile.

### Address book
- Render saved addresses as **cards** in a responsive grid: name, formatted address, phone, a **"Default" badge** on the default one, and per-card **Edit** / **Delete** / **Set as default** actions.
- An **Add new address** card/button opens the address form (a modal on desktop, a full screen on mobile).
- **Empty state:** a friendly "No saved addresses yet" with a prominent add button — never a blank grid.
- **Delete:** confirm before deleting; optimistic removal is fine but reconcile to the API and restore the card on failure.
- After any create/update/delete, **re-fetch the list** (or reconcile from the response) so the default badge and card set stay correct.

### Validation UX
- Country first, then state (state list depends on country); postcode/phone formats can be country-specific — keep them lenient unless the backend rejects.
- Scroll to and focus the first invalid field on submit; keep all entered data on a validation failure.

### Accessibility
- Label every field; `aria-required` / `aria-invalid` + `aria-describedby` for errors; `aria-live="polite"` for save confirmations.
- Address cards are list items — use a list role; actions are real buttons with discernible names ("Edit home address").
- Keyboard: full tab order, visible focus, Escape closes the address modal.

---

## 5. Errors

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Not logged in / token expired | 401 | Clear session, redirect to login (see authentication page). |
| Editing another customer's profile/address | 403 | Block; the token scopes you to your own data — never surface another account's. |
| Missing/invalid field (profile, address) | 422 | Inline field errors; scroll to first; preserve input. |
| `currentPassword` wrong on password change | 422 | Inline on the current-password field; don't clear the form. |
| Address / profile id not found | 404 | Friendly not-found; usually a stale link — refresh the list. |
| Bad request shape | 400 | Fix the request; surface a generic message. |

Standard statuses: **200/201** success · **401** unauthenticated · **403** forbidden · **400** bad input · **404** not found · **422** validation.

---

## 6. GraphQL notes

- Shop endpoint: `POST /api/graphql` (storefront key + customer Bearer per call). See [graphql.md](../graphql.md).
- Field names: `getCustomerProfile` (read), `createCustomerProfileUpdate` (update/password), `createCustomerProfileDelete` (delete); addresses `getCustomerAddresses` (list), `createAddUpdateCustomerAddress` (create **and** update — id present = update), `createDeleteCustomerAddress` (delete).
- Inputs are **camelCase** (`firstName`, `subscribedToNewsLetter`, `currentPassword`); one field per line in selection sets.
- Update/delete are **action mutations** — select the documented result fields (the entity, `success`, `message`), not a generic `id`.

---

## 7. Checklist

**Profile**
- [ ] Profile read on entering the account area (`GET /customer-profiles`) and cached.
- [ ] Personal-details and password are separate form sections; password change sends `currentPassword`/`password`/`confirmPassword` via `PUT /customer-profile-updates/{id}`.
- [ ] Account deletion (`POST /customer-profile-deletes/{id}`) confirms intent, then clears all auth state on success.
- [ ] Profile cache invalidated after a successful update.

**Address book**
- [ ] List (`GET /customer-addresses`), create (`POST`), update (`PUT /{id}`), delete (`DELETE /{id}`) all wired.
- [ ] Country chosen before state; state list fetched dynamically.
- [ ] Default address badged; "set as default" supported; list re-fetched after each mutation.
- [ ] Empty-address state handled; delete is confirmed and reconciled to the API.

**Guarding & errors**
- [ ] Entire account subtree behind the auth guard; 401 clears session → login.
- [ ] 403 never leaks another customer's data; 422 shows field-level errors and keeps input; 404 refreshes the list.

**UI/UX & a11y**
- [ ] Dashboard nav (two-pane desktop / stacked mobile) with active highlighting and a greeting.
- [ ] Addresses as cards with per-card edit/delete/set-default; add-new flow as modal (desktop) / screen (mobile).
- [ ] Validation on blur, first error focused, input preserved; labels + `aria-required`/`aria-invalid`/`aria-live`; keyboard + Escape-to-close.

**Both transports**
- [ ] Works over REST and GraphQL; storefront key + customer Bearer always sent; GraphQL inputs camelCase with documented result fields.
