# Shop GraphQL rules

Read this if the client chose GraphQL. The shapes still come from the api-docs endpoint pages — this page is the must-know behaviour.

## Endpoint & auth

- **`POST /api/graphql`** (shop — separate from `/api/admin/graphql`). Always send `X-STOREFRONT-KEY`; add `Authorization: Bearer <cartToken | customerToken>` for cart/account/checkout operations.
- An interactive playground is served at `/api/graphiql`.

## The result-field / `id` rule (most common mistake)

GraphQL resources fall into two kinds:

- **Fetchable (noun) resources** — product, customer, order, category, page. These expose a selectable `id` (and `_id` for the raw integer) plus their fields.
- **Action / result mutations** — add-to-cart, update/remove item, apply/remove coupon, set address/shipping/payment, place order, merge cart. These return a **small result object**, not a fetchable entity.

**On an action mutation, select the documented result fields** — e.g. the cart (`items`, totals, `couponCode`), or `success` / `message`, or `orderId` / `paymentGatewayUrl`. **Use exactly the fields shown on that mutation's docs page**; don't assume a generic `id` selection works the same across mutations (some expose `id`, some don't — the docs example is authoritative).

## Inputs & selection sets

- **Inputs are camelCase** — `productId`, `selectedConfigurableOption`, `bundleOptions`, `couponCode`, `billingFirstName`, `shippingMethod`, `paymentMethod`.
- **One field per line** in selection sets (matches the docs examples) — don't cram several fields onto one line.
- Mutations wrap their input in `input: { … }`; the payload is nested under the operation name (e.g. `createAddProductInCart { … }`).

## Cursor pagination (collections)

GraphQL list queries are cursor-paginated:

```graphql
query {
  <collection>(first: 20, after: "<cursor>") {
    edges { node { id _id name } }
    pageInfo { hasNextPage endCursor }
  }
}
```

REST uses `?page`/`?per_page` + `X-Total-*` headers instead; pick per the client's transport.

## Finding the exact field name

GraphQL operation names follow the package's convention (e.g. `createAddProductInCart`, `collectionShippingRates`, `createCheckoutOrder`). **Don't guess — open the endpoint's GraphQL docs page** (or the `/api/graphiql` schema) to confirm the operation name, arguments, and selectable fields before writing the query.
