# Authentication flow

Everything customer-scoped — the account dashboard, the saved address book, order history, the customer's own cart — hangs off one thing: a **customer token**. Authentication is the gate that mints it. This page covers the full lifecycle: register, login, logout, verify, forgot password, change password, and the one moment most storefronts get wrong — **merging the guest cart into the customer cart on login.**

> **Source of truth for exact shapes:** this page gives you the flow, the endpoints, the token model, and the UX. For the full request/response body of any call, open its api-docs page (linked per step). **Never hardcode a payload from memory — open the page.**

Auth headers are documented once in [connecting-to-the-api.md](../connecting-to-the-api.md) — every shop call sends `X-STOREFRONT-KEY`; customer-scoped calls also send `Authorization: Bearer <customerToken>`. This page won't repeat the header table; it focuses on the flow.

---

## 1. Flow architecture & token model

A storefront has **three auth states**, and every screen lives in exactly one:

```
   ┌─────────────┐
   │  ANONYMOUS  │  X-STOREFRONT-KEY only — can browse catalog
   └─────────────┘
        │  add to cart
        ▼
   ┌─────────────┐   POST /api/shop/cart-tokens ──▶ cartToken (guest cart, see cart.md)
   │   GUEST     │  X-STOREFRONT-KEY + Bearer <cartToken>
   └─────────────┘
        │  register → login
        ▼  POST /api/shop/customers   then   POST /api/shop/customer/login → top-level `token`
   ┌─────────────┐   ── CRITICAL: merge guest cart here (see §6) ──
   │  CUSTOMER   │  X-STOREFRONT-KEY + Bearer <customerToken>
   └─────────────┘  account, address book, orders, their cart
        │  logout
        ▼  POST /api/shop/customer/logout (token revoked)
   back to ANONYMOUS / GUEST
```

- **The customer token is the whole story.** Login returns a **top-level `token`** in the format `<id>|<secret>` (e.g. `3627|DfkAK11F…`). Send it verbatim as `Authorization: Bearer <token>` on every customer-scoped request. There is no refresh-token rotation — the token is valid until logout (or admin revocation).
- **Two distinct Bearer tokens exist:** the guest `cartToken` (from `cart-tokens`) and the `customerToken` (from login). They are NOT interchangeable. The moment a guest logs in, you switch the Bearer you send from the cart token to the customer token — after merging the cart (§6).
- **Storage:** persist the customer token in a secure client store. On web, prefer an httpOnly cookie set by your own backend-for-frontend if you have one; otherwise localStorage is the pragmatic choice for a pure SPA (accept the XSS trade-off and harden CSP). On native, use the platform keystore/keychain. Never log the token.

**Recommended client architecture**

- **Auth state container** (Context / Zustand / Redux) holding: `customerToken`, the resolved `customer` object, `isAuthenticated`, and loading/error flags. Hydrate it once on app boot by calling **verify** (§5) with any stored token.
- **A typed fetch wrapper** that always attaches `X-STOREFRONT-KEY` and the current Bearer token. One place to swap guest→customer token.
- **Route guarding** — protected routes (account, orders) redirect to login when `!isAuthenticated`; the login screen remembers the intended destination and returns to it post-login.

---

## 2. Register

- **REST:** `POST /api/shop/customers`
- **GraphQL:** mutation `createCustomer`
- **Send:** `firstName`, `lastName`, `email`, `password`, `confirmPassword` (required); optional `phone`, `gender`, `dateOfBirth`, `subscribedToNewsLetter`.
- **Returns:** the created customer (and a success/message). Registration does **not** auto-issue a login token in this API — follow registration with a login call (or auto-login the user by calling login with the same credentials).
- **Docs:** [customer registration](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/customer-registration), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/customer-registration).
- **UX:** minimal fields (name, email, password); a single password + confirm pair with a strength meter; inline "email already registered" handling (route them to login). Offer "subscribe to newsletter" as an unchecked opt-in. Validate on blur; disable submit while in flight.

---

## 3. Login

- **REST:** `POST /api/shop/customer/login`
- **GraphQL:** mutation `createCustomerLogin`
- **Send:** `email`, `password`.
- **Returns:** a **flat** response with a top-level `token` (format `<id>|<secret>`) plus the customer. (REST also returns a long-lived `apiToken`; for a standard storefront session use `token`.)
- **Docs:** [customer login](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/customer-login), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/customer-login).
- **On success:** (1) store the token, (2) **merge the guest cart** (§6), (3) populate auth state, (4) redirect to the intended page (or account dashboard).
- **UX:** email + password; "remember me" simply governs how long you persist the token; a prominent "forgot password?" link; show a generic "invalid email or password" on failure (don't reveal which field was wrong); disable submit + show spinner while in flight; never double-submit.

---

## 4. Logout

- **REST:** `POST /api/shop/customer/logout`
- **GraphQL:** mutation `createLogout`
- **Send:** empty body (the token in the Bearer identifies the session).
- **Returns:** a success/message; the token is revoked server-side.
- **Docs:** [customer logout](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/customer-logout), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/customer-logout).
- **On success:** clear the stored token, reset auth state, drop any customer-cart references, and redirect to home or login. Also clear cached customer-scoped queries (orders, profile, addresses) so a fast re-login doesn't flash stale data.
- **UX:** logout is usually a header/account-menu action — confirm only if there's unsaved work. Even if the network call fails, clear local state (the user expects to be logged out).

---

## 5. Verify token

- **REST:** `POST /api/shop/verify-tokens`
- **GraphQL:** mutation `createVerifyToken`
- **Send:** empty body; the token rides in the `Authorization: Bearer` header.
- **Returns:** the customer details if the token is valid; an error if it's expired/revoked.
- **Docs:** [verify token](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/customer-verify-token), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/customer-verify-token).
- **When to call:** on app boot / page reload to rehydrate `isAuthenticated` from a stored token, and as a cheap "is my session still good?" check before entering a protected area. If it fails, clear the token and treat the user as anonymous/guest.
- **UX:** invisible — runs during the splash/loading state, not a screen the user sees.

---

## 6. Guest → customer cart merge (CRITICAL)

This is the single most-missed step. When a guest has items and then logs in, their guest cart and the customer cart are **separate carts**. If you don't merge, the guest's items silently vanish the moment you switch to the customer token.

```
guest cart (token + _id)  ──login──▶  customer token issued
                                          │
                                          ▼  POST /api/shop/merge-carts
                               cartId = guest cart _id, Bearer = customerToken
                                          │
                                          ▼
                              merged customer cart  → drop the guest token
```

1. Before logging in, capture the guest cart's `_id` (you already have it from the cart flow).
2. Log in → receive the customer token.
3. Call **merge** (`POST /api/shop/merge-carts` / `createMergeCart`) with the guest cart `_id` as `cartId`, using the **customer** Bearer token.
4. Continue with the merged cart; discard the old guest cart token.

Full mechanics live in the cart page — see **[cart.md → Guest→customer merge](./cart.md#4-guestcustomer-merge-critical)**. Wire the merge into your login success handler so it's automatic, not a thing a developer has to remember to call.

---

## 7. Forgot password vs change password

These are **two different flows** — don't conflate them.

### Forgot password (password unknown — emails a reset link)
- **REST:** `POST /api/shop/forgot-passwords`
- **GraphQL:** mutation `createForgotPassword`
- **Send:** `email`.
- **Returns:** a success/message; the backend emails a reset link if the account exists.
- **Docs:** [forgot password](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/forgot-password), [REST](https://api-docs.bagisto.com/api/rest-api/shop/customers/forgot-password).
- **Important:** the storefront API has **no token-based password-reset endpoint** — the customer completes the reset on the web link the email contains. Your storefront's job ends at "we've sent you an email if that account exists." Show that neutral message regardless of whether the email matched (don't leak account existence).

### Change password (password known — done while logged in)
- This is the **profile-update** call carrying the password trio.
- **REST:** `PUT /api/shop/customer-profile-updates/{id}`
- **GraphQL:** mutation `createCustomerProfileUpdate`
- **Send:** `currentPassword`, `password`, `confirmPassword`. The backend verifies `currentPassword` before applying, and `confirmPassword` must equal `password`.
- **Docs:** [change password](https://api-docs.bagisto.com/api/rest-api/shop/customers/change-password), [update profile (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/update-customer-profile).
- This lives on the account screen, not the auth screen — see [account.md](./account.md). It's listed here so you don't go hunting for a separate "change password" endpoint that doesn't exist.

---

## 8. UI/UX

### Forms
- One component per flow: `RegisterForm`, `LoginForm`, `ForgotPasswordForm`. Keep them small and individually testable.
- **Validation:** validate on blur, re-validate on submit, scroll to the first error. Email format client-side; password rules surfaced as helper text, not a wall of errors.
- **Password fields:** a show/hide toggle; a strength indicator on register; never autofill the confirm field.
- **Loading + disabled:** disable the submit button and show a spinner the instant the call is in flight; this prevents double-submits and double-registration.

### Error states (user-friendly, never raw)
- Login failure → "The email or password you entered is incorrect." (single generic message).
- Register with existing email → "An account with this email already exists." + a "log in instead" link.
- Network/timeout → "Something went wrong. Please try again." + a retry that doesn't clear the form.

### Accessibility
- Label every field; `aria-required` on required fields; `aria-invalid` + an `aria-describedby` error message on failed fields.
- `aria-live="polite"` region for form-level success/error so screen readers announce it.
- Full keyboard operability; logical tab order; visible focus rings.

### Mobile
- Single column; `type="email"` / `type="password"` / `inputmode` so the right keyboard appears; large touch targets (≥44px).
- Keep the submit button reachable above the keyboard; avoid layout jumps when validation messages appear.

---

## 9. Protected-route gating

- Gate every customer-scoped route (account, addresses, orders, invoices, downloadables) on `isAuthenticated`. If false → redirect to login, remembering the destination.
- On a customer-scoped API call returning **401**, treat the session as dead: clear the token, reset auth state, send the user to login. Don't loop retrying.
- On app boot, run **verify** (§5) against any stored token before rendering a protected route, so you don't flash a logged-in shell that then bounces to login.

---

## 10. Errors

| Failure | HTTP (REST) / GraphQL | Handle by |
|---|---|---|
| Missing storefront key | 401 | Misconfiguration — ensure the key is attached to every call (see connecting page). |
| Invalid login credentials | 401 / error | Generic "email or password incorrect"; keep the email field filled. |
| Expired / revoked customer token | 401 | Clear token, reset auth, redirect to login. |
| Register with duplicate email | 422 | Inline "email already exists" + link to login. |
| Missing/invalid field (register, change-password) | 422 | Inline field errors; scroll to the first; keep input. |
| `currentPassword` wrong (change password) | 422 | Inline on the current-password field; don't clear the form. |
| Accessing another customer's resource | 403 | Block/redirect; never expose another account's data. |
| Resource not found | 404 | Friendly not-found; usually a stale link. |

Standard statuses: **200/201** success · **401** unauthenticated · **403** forbidden · **400** bad input · **404** not found · **422** validation.

---

## 11. GraphQL notes

- Shop endpoint: `POST /api/graphql` (storefront key required; Bearer token per call). See [graphql.md](../graphql.md).
- Auth mutation field names: `createCustomer` (register), `createCustomerLogin` (login), `createLogout` (logout), `createVerifyToken` (verify), `createForgotPassword` (forgot). Change-password is `createCustomerProfileUpdate`.
- Inputs are **camelCase** (`firstName`, `confirmPassword`, `currentPassword`); one field per line in selection sets.
- These are **action mutations** — select the documented **result fields** (the customer object, `success`, `message`, the top-level `token` on login), not a generic `id`.

---

## 12. Checklist

**Token lifecycle**
- [ ] Login stores the top-level `token` (`<id>|<secret>`) and sends it as `Authorization: Bearer <token>` on customer-scoped calls.
- [ ] Guest `cartToken` and `customerToken` kept distinct; Bearer swapped to the customer token after login.
- [ ] Token persisted securely (keystore/httpOnly cookie/localStorage); never logged.
- [ ] On boot, stored token rehydrated via **verify** before rendering protected routes.

**Register / login / logout**
- [ ] Register (`POST /customers`) then login; or auto-login post-register.
- [ ] Login success → merge guest cart → set auth state → redirect to intended page.
- [ ] Logout (`POST /customer/logout`) clears token + auth state + customer-scoped caches, even if the network call fails.

**Guest→customer merge (CRITICAL)**
- [ ] On login, guest cart merged via `merge-carts` (guest `_id` as `cartId`, customer Bearer) — wired into the login handler, not optional.

**Passwords**
- [ ] Forgot-password (`POST /forgot-passwords`) shows a neutral "email sent if account exists" message; no in-app token reset.
- [ ] Change-password done via `PUT /customer-profile-updates/{id}` with `currentPassword`/`password`/`confirmPassword`.

**Guarding & errors**
- [ ] Protected routes redirect to login when unauthenticated; intended destination remembered.
- [ ] 401 on any customer call clears the session and routes to login (no retry loop).
- [ ] 401/403/422 mapped to friendly, field-level messages; form input preserved.

**UI/UX & a11y**
- [ ] Validation on blur; first error focused/scrolled; submit disabled while in flight (no double-submit).
- [ ] Generic login-failure message; duplicate-email routes to login.
- [ ] Labels + `aria-required`/`aria-invalid`/`aria-live`; keyboard navigable; correct mobile keyboards + ≥44px targets.

**Both transports**
- [ ] Works over REST and GraphQL; storefront key always sent; GraphQL inputs camelCase, documented result fields selected.
