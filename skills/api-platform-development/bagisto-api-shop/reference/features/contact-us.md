# Contact form

A single endpoint backing the storefront "Contact us" page — name, email, phone, message → submit. Public, one call, returns `success`/`message`.

> **Source of truth:** [create-contact-us](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-contact-us). Open it for the exact field names/response before wiring the call. (GraphQL docs only; for REST, mirror the same fields against the live endpoint.)

- **Submit — REST:** `POST /api/shop/contact-us` · **GraphQL:** `createContactUs(input: { name, email, … })`
- **Auth:** `X-STOREFRONT-KEY`. Public — no token required. Send the customer Bearer if a logged-in customer is submitting and you want it attributed, but it isn't needed.
- **Returns:** `success` + `message`.

---

## 1. Flow

```
  Contact page form:  name, email, contact number, message
     ▼
  POST /api/shop/contact-us { name, email, ... , message }
     │   200 + success:true → success state (thank-you, clear the form)
     │   422               → inline field errors, keep all entered values
```

A plain submit-and-confirm. There's no thread/reply surface in this API — the store receives the message; the storefront's job is to collect, validate, submit, and confirm.

---

## 2. Status / behaviour handling

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Submitted | 200 + `success: true` | Replace the form (or show a banner) with a thank-you; clear the fields. |
| Validation error | 422 | Inline errors per field (required name/email/message, bad email); **keep everything the user typed**. |
| Rate-limited / spam guard | 429 / 422 | Friendly "please try again" message; don't lose the input. |
| Server error | 5xx | Generic "Couldn't send your message, try again" — no technical text. |

Branch on `success` + `message` from the response.

---

## 3. UI/UX

- **Form fields:** name, email, contact number, message — mark required fields, validate email format and message length client-side before submitting.
- **Spam protection:** a captcha or honeypot is common on public contact forms; if the backend enforces one, wire it and handle its failure as a recoverable validation case.
- **Submit feedback:** disable the button + show a spinner while in flight; debounce to prevent double-submits.
- **Success state:** clear, prominent confirmation in place ("Thanks — we'll get back to you"). Optionally show the store's support email/phone as a fallback channel.
- **Error state:** inline per-field errors from the response; never discard the user's typed message on failure (losing a long message is the worst contact-form UX).
- **Mobile:** single-column, full-width fields; `type="email"` + `inputmode` for the right keyboards; comfortable tap targets.
- **a11y:** every field has a visible label; errors associated via `aria-describedby`; the success/error result announced via `aria-live`; focus moves to the confirmation (or the first error) on submit.

---

## 4. GraphQL notes

- `createContactUs(input: { name, email, … , message })` — confirm the exact input fields on the docs page. Inputs camelCase.
- Action mutation — select the result fields (`success`/`message`), not a generic `id`.
- Storefront key required; no token needed.

---

## 5. Checklist

- [ ] Submit wired (`POST /api/shop/contact-us` / `createContactUs`); fields verified against the docs page.
- [ ] Required fields + email-format + message-length validated client-side; 422 maps to inline per-field errors.
- [ ] User's input preserved on every failure path.
- [ ] Success state clears the form and shows a clear confirmation; button disabled + debounced while in flight.
- [ ] Captcha/honeypot wired if the backend enforces it; its failure handled as recoverable.
- [ ] Mobile single-column layout; accessible labels; `aria-live` result; focus management on submit.
- [ ] Storefront key always sent.
