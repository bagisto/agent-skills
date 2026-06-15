# Coupons (apply / remove)

Promo-code entry on the cart and checkout. Two endpoints, both returning the **full updated cart** so the discount and new totals render immediately.

> **Source of truth:** [apply-coupon](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/apply-coupon) · [remove-coupon](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/remove-coupon). This page gives the flow, statuses, and UX.

- **Apply — REST:** `POST /api/shop/apply-coupon` · **GraphQL:** `createApplyCoupon(input: { couponCode })`
- **Remove — REST:** `POST /api/shop/remove-coupon` · **GraphQL:** `createRemoveCoupon(input: {})`
- **Auth:** `X-STOREFRONT-KEY` + `Authorization: Bearer <cartToken | customerToken>` (same cart as the items).
- **Returns:** the full cart — `couponCode` (set/cleared), recalculated `discountAmount` / `grandTotal` (+ `formatted*`), `success`, `message`.

---

## 1. Flow

```
  cart with items
     │  user enters code → Apply
     ▼
  POST /api/shop/apply-coupon { couponCode }
     │   200 → cart now carries couponCode + discountAmount      → show applied state + new total
     │   404 → code doesn't exist / inactive                     → inline "invalid code"
     │   422 → already applied / not eligible (min spend, etc.)  → inline reason
     ▼
  Remove:  POST /api/shop/remove-coupon  → cart with couponCode cleared, totals recalculated
```

A cart holds **one active coupon** (`couponCode`). Applying recalculates discount/tax/totals server-side; removing reverses it.

---

## 2. Status handling (mirrors the API)

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Applied | 200 + `success: true`, cart has `couponCode` + discount | Show applied chip + new total; clear the input. |
| Unknown / inactive code | 404 | Inline error: "This code isn't valid." Keep the input. |
| Already applied / not eligible | 422 | Inline reason (e.g. minimum-spend not met). |
| Removed | 200, `couponCode: null` | Remove the chip; restore totals. |

Always read `success` + `message` from the response — a `couponCode` echoed back with `success: true` is the confirmation it actually applied.

---

## 3. UI/UX

- **Placement:** a collapsible "Have a coupon?" field on the cart page and the checkout review — not always-expanded (reduces friction / coupon-hunting abandonment).
- **Applied state:** show the code as a removable chip with the discount amount and a clear "remove" affordance.
- **Feedback:** inline success/error next to the field (not a global toast); keep the typed code on failure so the user can fix a typo.
- **Loading:** disable Apply while in flight; debounce so double-clicks don't double-submit.
- **Totals:** re-render the whole summary from the returned cart's `formatted*` fields — discount, tax, and grand total all move.
- **a11y:** associate the error with the input (`aria-describedby`); announce apply/remove via `aria-live`.

---

## 4. GraphQL notes

- `createApplyCoupon(input: { couponCode })` and `createRemoveCoupon(input: {})`; select the cart/result fields (`couponCode`, totals, `success`, `message`).
- Input is camelCase (`couponCode`); one field per line.
- Same cart token/customer token as the rest of the cart calls.

---

## 5. Checklist

- [ ] Apply wired (`POST /apply-coupon` / `createApplyCoupon { couponCode }`); remove wired (`/remove-coupon` / `createRemoveCoupon`).
- [ ] 200 / 404 / 422 mapped: applied chip / invalid-code / not-eligible reason.
- [ ] `success` + `message` read from the response to confirm application.
- [ ] Totals re-rendered from the returned cart (discount + tax + grand total).
- [ ] Collapsible coupon field on both cart page and checkout review.
- [ ] Applied state shows a removable chip with the discount.
- [ ] Input retains the code on failure; Apply disabled while in flight (no double-submit).
- [ ] Error associated to the input; apply/remove announced via `aria-live`.
- [ ] Works for guest (`cartToken`) and logged-in (`customerToken`); storefront key always sent.
