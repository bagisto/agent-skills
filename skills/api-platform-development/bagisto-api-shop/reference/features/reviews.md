# Reviews & ratings

Two related surfaces:

1. **Product reviews** — the rating + review list shown on a product page, and the form a customer uses to write one.
2. **The customer's own reviews** — a "My reviews" list in the account area, showing everything the signed-in customer has written.

> **Source of truth:** [get-product-reviews](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-product-reviews) · [create-product-review](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/create-product-review) · [update-product-review](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/update-product-review) · [delete-product-review](https://api-docs.bagisto.com/api/graphql-api/shop/mutations/delete-product-review) · [get-customer-reviews](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-reviews) · [get-customer-review](https://api-docs.bagisto.com/api/graphql-api/shop/queries/get-customer-review). REST: [create](https://api-docs.bagisto.com/api/rest-api/shop/product-reviews/create-product-review) · [list](https://api-docs.bagisto.com/api/rest-api/shop/product-reviews/get-product-reviews) · [get](https://api-docs.bagisto.com/api/rest-api/shop/product-reviews/get-product-review) · [update](https://api-docs.bagisto.com/api/rest-api/shop/product-reviews/update-product-review) · [delete](https://api-docs.bagisto.com/api/rest-api/shop/product-reviews/delete-product-review) · [customer-reviews](https://api-docs.bagisto.com/api/rest-api/shop/customer-reviews/get-customer-reviews) · [customer-review](https://api-docs.bagisto.com/api/rest-api/shop/customer-reviews/get-customer-review). Open the page for the exact body/response — never invent it.

### Product reviews

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List reviews (all) | `GET /api/shop/reviews` | `productReviews` |
| List reviews for one product | `GET /api/shop/products/{productId}/reviews` | `productReviews` (filter by product) |
| Get one review | `GET /api/shop/reviews/{id}` | `productReview` |
| Write a review | `POST /api/shop/reviews` | `createProductReview` |
| Edit a review | `PATCH /api/shop/reviews/{id}` | `updateProductReview` |
| Delete a review | `DELETE /api/shop/reviews/{id}` | `deleteProductReview` |

### The customer's own reviews

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List my reviews | `GET /api/shop/customer-reviews` | `customerReviews` |
| Get one of my reviews | `GET /api/shop/customer-reviews/{id}` | `customerReview` |

- **Reading product reviews** needs only the storefront key — public.
- **Writing / editing / deleting** a review, and the **customer-reviews** list, need `Authorization: Bearer <customerToken>`.

---

## 1. Flow

```
  Product page
     │  GET /api/shop/products/{productId}/reviews   → ratings summary + review list (public)
     │
     │  "Write a review"  (logged in?) ── no ──▶ login, return
     │            └─ yes
     ▼
  POST /api/shop/reviews { productId, rating, title, comment, ... }
     │   201 → review submitted (often "pending approval")  → thank-you + pending notice
     │   422 → validation (missing rating/comment)          → inline field errors
     ▼
  Account → My reviews:  GET /api/shop/customer-reviews
     ├─ edit    PATCH /api/shop/reviews/{id}
     └─ delete  DELETE /api/shop/reviews/{id}
```

New reviews are typically **moderated** — a submitted review may not appear in the public list until an admin approves it. Don't assume it shows up immediately; tell the user it's pending.

---

## 2. Status / behaviour handling

| Result | HTTP (REST) / GraphQL | UI |
|--------|-----------------------|----|
| Submitted | 201 + `success`/`message` | Thank-you state; if pending, say "Your review is awaiting approval." |
| Validation error | 422 | Inline errors on rating/title/comment; keep the user's text. |
| Not logged in (write) | 401 | Gate the "Write a review" CTA behind login; remember intent. |
| Not your review (edit/delete) | 403 | Hide edit/delete on reviews the customer doesn't own. |
| Review gone | 404 | Drop the row; refresh the list. |
| Read list (public) | 200 | Render ratings summary + paginated reviews. |

Always read `success` + `message`; surface the moderation/pending state honestly.

---

## 3. Ratings summary

The product detail / review payload exposes the rating data the PDP header needs (average rating, review count, and the per-star distribution where provided) — render the star average + count from the API, not a client-side recompute. Confirm the exact fields on the docs page; don't hardcode a scale.

---

## 4. UI/UX

- **PDP reviews block:** average stars + count near the title; a reviews section lower down with the paginated list (rating, title, body, author name, date). Sort/filter (most recent / highest / lowest) where the API supports it.
- **Write-a-review form:** required star rating (clear, large control), title, comment; optional attachments if the API accepts them. Gate behind login; some stores only allow reviews from customers who purchased — surface that rule rather than failing opaquely.
- **Pending notice:** after submit, explicitly tell the user the review needs approval before it's public — otherwise they'll think it failed.
- **My reviews (account):** list each review with the product it's on, the rating, status (pending/approved), and edit/delete actions on their own reviews only.
- **Empty states:** "No reviews yet — be the first" on a product; "You haven't written any reviews" in the account.
- **Mobile:** star input must be a comfortable tap target; review cards stack; truncate long bodies with "read more".
- **a11y:** the star input is a labelled radio group / slider with a text equivalent ("4 out of 5"); validation errors associated to fields; pending/success announced via `aria-live`.

---

## 5. GraphQL notes

- `productReviews` — cursor-paginated; filter to a product per the docs. `customerReviews` / `customerReview` — the signed-in customer's reviews (Bearer required).
- Mutations: `createProductReview`, `updateProductReview`, `deleteProductReview` — inputs camelCase (`productId`, `rating`, `title`, `comment`). Select the documented result fields (`success`/`message`/the review), not a blind `id`.
- Reading product reviews needs the storefront key only; writing/editing/deleting and `customerReviews` need the customer Bearer token.

---

## 6. Checklist

- [ ] PDP shows ratings summary + paginated review list from `GET /products/{productId}/reviews` (public).
- [ ] Write-a-review wired (`POST /reviews` / `createProductReview`); CTA gated behind login; eligibility rule surfaced.
- [ ] 201 shows a thank-you with a **pending-approval** notice; 422 shows inline field errors and keeps the user's text.
- [ ] Star input is required and accessible; validation associated to fields.
- [ ] "My reviews" account list wired (`GET /customer-reviews` / `customerReviews`, customer Bearer); edit (`PATCH /reviews/{id}`) + delete (`DELETE /reviews/{id}`) shown only on owned reviews.
- [ ] 403 hides edit/delete on others' reviews; 404 refreshes the list.
- [ ] Empty states on PDP and account; mobile star tap target + stacked cards.
- [ ] Storefront key always sent; writes/customer-reviews send the customer Bearer.
