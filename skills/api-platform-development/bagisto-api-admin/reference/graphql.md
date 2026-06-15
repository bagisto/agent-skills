# Admin GraphQL rules

Read this if the client chose GraphQL. Shapes still come from the api-docs endpoint pages — this is the must-know behaviour.

## Endpoint & auth

- **`POST /api/admin/graphql`** — admin only, **separate** from the shop `/api/graphql`. Send only `Authorization: Bearer <id>|<token>`; **no storefront key** (sending an admin token to the shop endpoint is rejected, and vice-versa).
- Interactive playground at `/api/admin/graphiql`.

## The result-field / `id` rule (most common mistake)

- **Fetchable (noun) resources** — order, product, customer, category, page, invoice, etc. — expose a selectable `id` (IRI) and `_id` (raw integer) plus their fields.
- **Action / result mutations** — cancel order, add comment, create invoice/shipment/refund, place order, the Create-Order cart writes (add/update/remove item, save address, set shipping/payment, apply/remove coupon), and **mass-actions** (mass-delete, mass-update-status) — return a **result object**, not a fetchable entity.

**On an action mutation, select the documented result fields** (`success` / `message` / `orderId` / `cartId` / `incrementId` / the refreshed record), per that mutation's docs page. Don't assume a generic `id` selection works across all mutations.

## Inputs, filters & selection sets

- **Inputs are camelCase** — `customerId`, `orderId`, `productId`, `value`, `indices`.
- **Custom filter args must be declared per query** — list queries expose their filters as explicit arguments (documented on each menu page); they are **not** auto-discoverable, so use the names the docs show.
- **One field per line** in selection sets (matches the docs examples).
- Mutation names follow the package convention — e.g. queries `adminOrders`, `adminCatalogProducts`, `adminCustomers`; mutations `createAdminInvoice`, `createAdminCustomer`, `updateAdminCatalogProduct`, `createAdminCatalogProductMassDelete`. **Confirm the exact name on the endpoint's docs page** (or the `/api/admin/graphiql` schema) — don't guess.

## Collections: cursor pagination

```graphql
query {
  adminOrders(first: 20, after: "<cursor>") {
    edges { node { id _id status grandTotal } }
    pageInfo { hasNextPage endCursor }
  }
}
```

REST uses the `{ data, meta }` envelope + `?page`/`?per_page` instead — pick per the client's transport.

## Nested data

Some admin detail payloads expose nested lists (order items, invoice items, addresses) as **plain JSON** rather than cursor connections — query them as bare fields (`items { sku qtyOrdered }`), not `{ edges { node } }`. The endpoint's docs example shows the correct selection; follow it.
