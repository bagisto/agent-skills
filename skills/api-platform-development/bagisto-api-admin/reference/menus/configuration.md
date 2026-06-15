# Configuration menu

The store's flat key/value settings — everything under **Configuration** in the admin (general, catalog, sales, customer, email, payment methods, shipping, etc.). Unlike the rest of the admin API, Configuration is **not one endpoint per screen**: its schema is registered at runtime by every installed package, so the API exposes **three generic endpoints** that work across any current or future config section. You build the config UI by reading the schema, reading the current values, and writing changes back — all keyed by a **slug** (a dotted section path like `sales.order_settings` or `general.content`).

> **Source of truth for exact shapes:** this page gives the flow and the endpoints. For the full request/response body, open the linked api-docs page. **Never hardcode a payload from memory.**

- Auth, the listing pattern, permissions, and errors are covered once in [connecting-to-the-api](../connecting-to-the-api.md). GraphQL behaviour is in [graphql.md](../graphql.md). Every call sends `Authorization: Bearer <id>|<token>`.

---

## 1. The three endpoints

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| Menu (schema) | `GET /api/admin/configuration/menu` | `menuAdminConfigurationMenu` |
| Values | `GET /api/admin/configuration?slug=…` | `valuesAdminConfigurationValues` |
| Update | `POST /api/admin/configuration` | `createAdminConfigurationUpdate` |

Docs: [menu](https://api-docs.bagisto.com/api/rest-api/admin/configuration/menu), [values](https://api-docs.bagisto.com/api/rest-api/admin/configuration/values), [update](https://api-docs.bagisto.com/api/rest-api/admin/configuration/update), [overview](https://api-docs.bagisto.com/api/rest-api/admin/configuration/index). GraphQL: [menu](https://api-docs.bagisto.com/api/graphql-api/admin/configuration/menu), [values](https://api-docs.bagisto.com/api/graphql-api/admin/configuration/values), [update](https://api-docs.bagisto.com/api/graphql-api/admin/configuration/update).

---

## 2. The flow: schema → values → update

```
  GET /api/admin/configuration/menu                  → the section/group/field tree (build the nav + forms)
       │  (optionally ?slug=<section> to scope, ?include_values=true to embed values)
       ▼
  GET /api/admin/configuration?slug=<section.group>  → { slug, channel, locale, values: { "dotted.code": "value" } }
       │  render a form pre-filled from values
       ▼
  POST /api/admin/configuration                      → { slug, channel?, locale?, values: { "dotted.code": newValue } }
       │  validated server-side, then returns the freshly-resolved values
       ▼
  re-render the form from the returned values
```

- **Menu** returns the whole configuration tree: sections → groups → fields, each field with its `code`, `type`, `title`, default, validation, and whether it's channel-/locale-based. Use it to build the left-hand config nav **and** to know what input control each field needs. Pass `?slug=<section>` to fetch just one node; pass `?include_values=true` (with optional `?channel=`/`?locale=`) to embed the effective value alongside each field so you can render a populated form from a single call.
- **Values** returns just the current values for a slug as a flat `{ dottedCode: stringValue }` map (falling back to each field's default where no value is stored). **The slug is required** — the endpoint refuses to dump the whole table.
- **Update** writes a `values` map for a slug. It returns the freshly-resolved values so the form can refresh without a follow-up GET.

---

## 3. Field types

The menu's field `type` tells you which control to render: `boolean` → toggle; `select`/`multiselect` → dropdown(s) populated from the field's options; `text`/`textarea`/`password` → inputs; `image`/`file` → an upload control; `color` → a colour picker; and a small set of admin-rendered custom views (`type: "custom"` with a `customView`). **Custom-view fields are read-only over the API** — surface them but route the user to the admin panel to edit them.

**Channel- and locale-based fields** vary per storefront context. When a field is marked channel-based or locale-based, your form needs channel/locale switchers, and your **values** + **update** calls must pass the matching `?channel=` / `?locale=` (or the `channel`/`locale` keys in the update body) so you read and write the right context.

---

## 4. Writing config — two hard rules

**1. Every key must start with the slug.** When you `POST` an update, every key in `values` must be prefixed with that request's `slug.` (e.g. `slug: "sales.order_settings"`, keys like `sales.order_settings.reorder.admin`). The server refuses any key that escapes the slug — this prevents accidentally overwriting an unrelated section. Build the keys from the slug you're editing, never from a stale or hand-typed path.

**2. File/image fields are REST-only.** Config fields of type `image`/`file` are uploaded via a **multipart** `POST /api/admin/configuration`, with the file in the `values[<dotted.code>]` part. The GraphQL update rejects file-type fields — for any screen with an upload field, use REST. Scalar-only updates work fine over either transport.

Validation is enforced server-side from each field's own validation rule (it isn't trusted from the client), so a bad value returns a `422` with the offending field — show it inline.

---

## 5. UI/UX

- **Two-pane layout** (desktop): the config section tree (from **menu**) on the left, the selected section's form on the right. On mobile, the tree becomes a drill-down list → form screens.
- **Build forms from the schema, not from hardcoded fields.** Iterate the menu's fields and render a control per `type`; this keeps the UI correct as packages add config. Group fields by their group node; show each field's `title` and help text.
- **Context switchers:** a channel selector (and a locale selector where relevant) at the top of any section that contains channel-/locale-based fields; re-read values when the context changes.
- **Custom-view fields:** render as read-only with a "manage in admin panel" hint.
- **Save** posts only the changed slug's values; re-render from the returned values. Disable Save while in flight; show inline `422` field errors.

---

## 6. Errors

| Status | When | UX |
|--------|------|----|
| 200 | Read/update OK | — |
| 400 | Missing required `slug` on values, or a key that escapes the slug | Friendly message; rebuild keys from the slug |
| 401 | Missing/expired/revoked token | Re-issue the token in the admin panel |
| 403 | Role lacks configuration permission | "You don't have permission for this" |
| 422 | A value failed its field validation, or a file field sent over GraphQL | Inline field error; use REST for uploads |

---

## 7. Build checklist

- [ ] Fetch the **menu** schema once; build the config section nav and the per-`type` form controls from it.
- [ ] Per section, read **values** with the required `slug` (+ `channel`/`locale` for context-based fields); pre-fill the form.
- [ ] Add channel/locale switchers for sections with channel-/locale-based fields; re-read on switch.
- [ ] **Update** posts the slug + a `values` map whose keys all start with `slug.`; re-render from the returned values.
- [ ] Use **multipart REST** for image/file fields; mark custom-view fields read-only.
- [ ] Map `403` to a permission message; show `422`/`400` field messages inline.
