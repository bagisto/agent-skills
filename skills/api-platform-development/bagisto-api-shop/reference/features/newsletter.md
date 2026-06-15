# Newsletter subscribe

A single endpoint to subscribe an email address to the store newsletter — usually wired to the footer "Subscribe" field, and optionally a checkbox at registration or checkout.

> **Source of truth:** [subscribe (REST)](https://api-docs.bagisto.com/api/rest-api/shop/newsletter/subscribe) · [create-newsletter (GraphQL)](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-newsletter). Open the page for the exact body/response — never invent a payload.

- **Subscribe — REST:** `POST /api/shop/newsletters` · **GraphQL:** `createNewsletter(input: { customerEmail })`
- **Auth:** `X-STOREFRONT-KEY`. Public — no customer token required (a guest can subscribe with just an email). A logged-in customer can subscribe too; send their Bearer if you have it.
- **Returns:** `success` + `message` — read both to decide the UI state.

---

## 1. Flow

```
  footer field:  email ──▶ Subscribe
     ▼
  POST /api/shop/newsletters { email }
     │   200 + success:true   → "You're subscribed" confirmation, clear the field
     │   already subscribed   → friendly "You're already on the list" (success message, not an error)
     │   422                  → invalid email → inline validation, keep input
```

This is a fire-and-forget single call — there's no list/read/unsubscribe surface in this API. Treat **already-subscribed** as a soft success (it's not a failure the user should see as red), and surface it via the `message` rather than an error toast.

---

## 2. Status / behaviour handling

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Subscribed | 200 + `success: true` | Replace the field with a confirmation; optionally keep a quiet "subscribed" state. |
| Already subscribed | 200 + `message` (success) | Friendly "You're already subscribed" — not an error. |
| Invalid / missing email | 422 | Inline validation under the field; keep the typed value. |
| Server error | 5xx | Generic "Couldn't subscribe, try again" — don't expose technical text. |

Branch on `success` + `message`, not on guessing from the status code alone — confirm the exact shape against the live endpoint (per the banner).

---

## 3. UI/UX

- **Placement:** the footer is the canonical home — a single email input + Subscribe button, present on every page. Optionally offer an opt-in checkbox during registration/checkout (subscribe via the same call after the primary action succeeds).
- **Inline confirmation:** swap the field for a short success message in place; don't navigate away or pop a modal for a footer subscribe.
- **Email validation:** validate format client-side before calling; on 422 show the server message inline and keep the value.
- **Loading:** disable the button while in flight; debounce so a double-click doesn't double-submit.
- **No false errors:** "already subscribed" is a positive outcome — never show it red.
- **Privacy:** a one-line consent note / link to the privacy policy next to the field where required.
- **Mobile:** full-width field + button; comfortable tap target; keyboard `type="email"` + `inputmode="email"`.
- **a11y:** the field has a visible label (or a labelled placeholder + `aria-label`); the result is announced via `aria-live`; errors associated with the input via `aria-describedby`.

---

## 4. GraphQL notes

- `createNewsletter(input: { customerEmail })` → result fields `success` / `message`. Inputs are camelCase. See the [create-newsletter](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-newsletter) page.
- It's an **action mutation** — select `success`/`message`, not a generic `id`.
- Storefront key required; customer Bearer optional.

---

## 5. Checklist

- [ ] Subscribe wired (`POST /api/shop/newsletters` / `createNewsletter` with `customerEmail`).
- [ ] Branches on `success` + `message`: subscribed / already-subscribed (soft success) / invalid (422).
- [ ] "Already subscribed" shown as a friendly success, never an error.
- [ ] Footer field with inline confirmation; button disabled + debounced while in flight.
- [ ] Client-side email format check; 422 shows the server message inline and keeps input.
- [ ] Optional registration/checkout opt-in reuses the same call.
- [ ] Consent/privacy note where required; `type="email"` + accessible label + `aria-live` result.
- [ ] Storefront key always sent.
