# Settings menu

The store's foundational configuration — the records every other menu depends on. Currencies and channels define *where* and *in what money* the store sells; locales decide *which languages*; tax rates and categories decide *how much tax*; inventory sources decide *where stock lives*; roles and users decide *who can do what*; themes decide *how the storefront looks*; and data-transfer imports bring catalog/customer data in by file. These are low-frequency, high-impact screens: most are edited rarely but break a lot when wrong, so the UI should favour clarity and confirmation over speed.

> **Source of truth for exact shapes:** this page gives the flow, the endpoints, and the UX. For the full request/response body of any call, open its api-docs page (linked per resource). **Never hardcode a payload from memory — open the page, confirm method/fields, then write the call.**

- **Auth, the `{ data, meta }` listing envelope, the list→detail→action pattern, pagination, permissions, and errors** are all covered once in [connecting-to-the-api](../connecting-to-the-api.md). Every endpoint below sends `Authorization: Bearer <id>|<token>`. Don't restate auth per screen.
- **GraphQL:** see [graphql.md](../graphql.md) — admin endpoint `POST /api/admin/graphql`, cursor pagination on lists, camelCase inputs, action mutations return result fields.

---

## 1. The shape of every Settings screen

Almost every resource here is the same **list → detail → CRUD** shape:

```
  LIST    GET /api/admin/settings/<resource>?page=&per_page=&<filters>  → { data, meta }
            │ pick a row
            ▼
  DETAIL  GET /api/admin/settings/<resource>/{id}                       → full record
            │ edit / delete
            ▼
  ACTION  POST   /api/admin/settings/<resource>           (create)
          PUT    /api/admin/settings/<resource>/{id}       (update)
          DELETE /api/admin/settings/<resource>/{id}       (delete)
          POST   /api/admin/settings/<resource>/mass-delete (bulk, where offered)
```

A few resources add their own actions (exchange-rate auto-sync, theme mass-update-status, user self-delete, the import pipeline). Those are called out under each resource.

**Recommended client architecture** — one route per resource list (`/settings/currencies`, `/settings/users`, …), a detail/edit route per record, a shared data-table component driven by `{ data, meta }` + `?page`/`?per_page`, and a shared form component per resource. Cache lists keyed by filters+page; invalidate the list after any create/update/delete so the table reflects the change. Surface **403** as "you don't have permission for this" (the token is capped by its admin's role).

---

## 2. Currencies

The money the store transacts in. The base currency of a channel must exist here; exchange rates (below) convert from it.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/currencies` | `adminSettingsCurrencies` |
| Detail | `GET /api/admin/settings/currencies/{id}` | `adminSettingsCurrency` |
| Create | `POST /api/admin/settings/currencies` | `createAdminSettingsCurrency` |
| Update | `PUT /api/admin/settings/currencies/{id}` | `updateAdminSettingsCurrency` |
| Delete | `DELETE /api/admin/settings/currencies/{id}` | `deleteAdminSettingsCurrency` |
| Mass delete | `POST /api/admin/settings/currencies/mass-delete` | `createAdminSettingsCurrencyMassDelete` |

- **Code is set once** — it's accepted on create but ignored on update (the form should disable the code field when editing).
- **Delete is guarded:** the store refuses to delete the last remaining currency, or any currency a channel uses as its base. Surface the returned error rather than a generic failure.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/list), [detail](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/detail), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/update), [delete](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/delete), [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/settings/currencies/mass-delete). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/currencies/list), [create](https://api-docs.bagisto.com/api/graphql-api/admin/settings/currencies/create).

## 3. Channels

A storefront context — its own domain/hostname, theme, default locale + currency, allowed locales/currencies, inventory sources, and SEO/maintenance text. Translatable fields are stored per locale.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/channels` | `adminSettingsChannels` |
| Detail | `GET /api/admin/settings/channels/{id}` | `adminSettingsChannel` |
| Create | `POST /api/admin/settings/channels` | `createAdminSettingsChannel` |
| Update | `PUT /api/admin/settings/channels/{id}` | `updateAdminSettingsChannel` |
| Delete | `DELETE /api/admin/settings/channels/{id}` | `deleteAdminSettingsChannel` |

- A channel references locales, currencies, and inventory sources — the form's multi-selects should be populated from those resources' list endpoints. The default locale must be in the allowed locales; the base currency must be in the allowed currencies — the API rejects mismatches, so validate client-side too.
- **Delete is guarded:** the store refuses to delete the last channel or the default app channel. There is **no mass-delete** for channels.
- **Logo/favicon image upload is not exposed via the API** — the form accepts a path string only; use the admin panel for binary uploads.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/channels/list), [detail](https://api-docs.bagisto.com/api/rest-api/admin/settings/channels/detail), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/channels/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/channels/update). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/channels/list).

## 4. Locales

The languages the store renders in. A channel picks a default locale and a set of allowed locales from this list.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/locales` | `adminSettingsLocales` |
| Detail | `GET /api/admin/settings/locales/{id}` | `adminSettingsLocale` |
| Create | `POST /api/admin/settings/locales` | `createAdminSettingsLocale` |
| Update | `PUT /api/admin/settings/locales/{id}` | `updateAdminSettingsLocale` |
| Delete | `DELETE /api/admin/settings/locales/{id}` | `deleteAdminSettingsLocale` |
| Mass delete | `POST /api/admin/settings/locales/mass-delete` | `createAdminSettingsLocaleMassDelete` |

- Each locale carries a `direction` (`ltr`/`rtl`) — surface it so the UI can flip layout.
- **Delete is guarded:** the store refuses the last locale, or any locale a channel uses as its default. Mass-delete skips ineligible ids (with a reason) rather than failing the whole batch.
- **Logo image is a path string only** — binary upload isn't exposed.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/locales/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/locales/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/locales/update), [delete](https://api-docs.bagisto.com/api/rest-api/admin/settings/locales/delete), [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/settings/locales/mass-delete). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/locales/list).

## 5. Exchange Rates

The conversion rate from the channel's base currency to each target currency. Includes an auto-sync action that pulls fresh rates from the configured provider.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/exchange-rates` | `adminSettingsExchangeRates` |
| Detail | `GET /api/admin/settings/exchange-rates/{id}` | `adminSettingsExchangeRate` |
| Create | `POST /api/admin/settings/exchange-rates` | `createAdminSettingsExchangeRate` |
| Update | `PUT /api/admin/settings/exchange-rates/{id}` | `updateAdminSettingsExchangeRate` |
| Delete | `DELETE /api/admin/settings/exchange-rates/{id}` | `deleteAdminSettingsExchangeRate` |
| Mass delete | `POST /api/admin/settings/exchange-rates/mass-delete` | `createAdminSettingsExchangeRateMassDelete` |
| Auto-sync rates | `POST /api/admin/settings/exchange-rates/update-rates` | `createAdminSettingsExchangeRateUpdateRates` |

- Each rate targets one currency; the target currency must already exist. One rate per target currency.
- **Auto-sync** runs the configured rate provider and refreshes every row in one call — wire it to an "Update Rates" button. Provider/network failures come back as a `422` with the provider's message; show it.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/exchange-rates/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/exchange-rates/create), [update-rates](https://api-docs.bagisto.com/api/rest-api/admin/settings/exchange-rates/update-rates). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/exchange-rates/list), [update-rates](https://api-docs.bagisto.com/api/graphql-api/admin/settings/exchange-rates/update-rates).

## 6. Inventory Sources

The physical/warehouse locations stock is held at. Products carry per-source quantities; shipments draw from a chosen source; channels list the sources they can fulfil from.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/inventory-sources` | `adminSettingsInventorySources` |
| Detail | `GET /api/admin/settings/inventory-sources/{id}` | `adminSettingsInventorySource` |
| Create | `POST /api/admin/settings/inventory-sources` | `createAdminSettingsInventorySource` |
| Update | `PUT /api/admin/settings/inventory-sources/{id}` | `updateAdminSettingsInventorySource` |
| Delete | `DELETE /api/admin/settings/inventory-sources/{id}` | `deleteAdminSettingsInventorySource` |
| Mass delete | `POST /api/admin/settings/inventory-sources/mass-delete` | `createAdminSettingsInventorySourceMassDelete` |

- A source carries full address + contact fields, a `priority`, optional lat/lng, and a `status`.
- **Delete is guarded:** the store refuses the last remaining source, or any source that still holds product inventory. Mass-delete pre-checks the whole batch and rejects it if either condition would fire.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/inventory-sources/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/inventory-sources/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/inventory-sources/update). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/inventory-sources/list).

## 7. Tax Rates

A tax percentage scoped by country/state and either a single zip or a zip range. Tax categories (below) group rates.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/tax-rates` | `adminSettingsTaxRates` |
| Detail | `GET /api/admin/settings/tax-rates/{id}` | `adminSettingsTaxRate` |
| Create | `POST /api/admin/settings/tax-rates` | `createAdminSettingsTaxRate` |
| Update | `PUT /api/admin/settings/tax-rates/{id}` | `updateAdminSettingsTaxRate` |
| Delete | `DELETE /api/admin/settings/tax-rates/{id}` | `deleteAdminSettingsTaxRate` |
| CSV export | `GET /api/admin/settings/tax-rates/export` | — (REST only) |

- **Conditional zip fields:** when the rate is not zip-ranged, a single `zip_code` is required; when it is, `zip_from` + `zip_to` are both required. The form should toggle which zip fields it shows from the "is zip range" switch, and the API re-validates this — including when an edit flips the switch.
- **There is no mass-delete** for tax rates.
- **CSV export** streams a `text/csv` attachment honouring the same filters as the list. Send `Accept: text/csv`; `?format=` accepts only `csv`. REST only.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-rates/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-rates/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-rates/update), [export](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-rates/export). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/tax-rates/list).

## 8. Tax Categories

Named groups of tax rates that products are assigned to. A product picks a tax category; the matching rate within it applies at checkout based on the buyer's address.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/tax-categories` | `adminSettingsTaxCategories` |
| Detail | `GET /api/admin/settings/tax-categories/{id}` | `adminSettingsTaxCategory` |
| Create | `POST /api/admin/settings/tax-categories` | `createAdminSettingsTaxCategory` |
| Update | `PUT /api/admin/settings/tax-categories/{id}` | `updateAdminSettingsTaxCategory` |
| Delete | `DELETE /api/admin/settings/tax-categories/{id}` | `deleteAdminSettingsTaxCategory` |

- The create/update body carries the set of tax-rate ids to attach — populate that multi-select from the tax-rates list. The detail payload inlines the attached rates.
- **Delete is guarded:** the store refuses a category that still has rates attached — re-save with an empty rate set first. **No mass-delete.**
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-categories/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/tax-categories/create). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/tax-categories/list).

## 9. Roles

Permission sets admins are assigned to. A role is either "all access" or a custom set of permission keys; a token can never exceed its admin's role.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/roles` | `adminSettingsRoles` |
| Detail | `GET /api/admin/settings/roles/{id}` | `adminSettingsRole` |
| Create | `POST /api/admin/settings/roles` | `createAdminSettingsRole` |
| Update | `PUT /api/admin/settings/roles/{id}` | `updateAdminSettingsRole` |
| Delete | `DELETE /api/admin/settings/roles/{id}` | `deleteAdminSettingsRole` |

- A role's `permission_type` is `all` or `custom`; when `custom`, a non-empty permissions array is required. Switching to `all` clears the permissions list.
- **Delete is guarded:** the store refuses a role still assigned to an admin, or the last remaining role. **No mass-delete.**
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/roles/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/roles/create). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/roles/list).

## 10. Users (admins)

The back-office accounts. Each user has a role; passwords are write-only.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/users` | `adminSettingsUsers` |
| Detail | `GET /api/admin/settings/users/{id}` | `adminSettingsUser` |
| Create | `POST /api/admin/settings/users` | `createAdminSettingsUser` |
| Update | `PUT /api/admin/settings/users/{id}` | `updateAdminSettingsUser` |
| Delete | `DELETE /api/admin/settings/users/{id}` | `deleteAdminSettingsUser` |
| Self-delete | `POST /api/admin/settings/users/delete-self` | `createAdminSettingsUserDeleteSelf` |

- Create requires a password; update leaves the password unchanged when omitted. The password/token are never returned.
- **Delete guards:** the `{id}` delete refuses self-deletion and refuses the last remaining admin. To delete the token's own account use **self-delete**, which re-confirms the current password (and still refuses the last admin). Self-delete invalidates the calling token. **No mass-delete.**
- **Avatar image is a path string only** — binary upload isn't exposed.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/users/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/users/create), [delete-self](https://api-docs.bagisto.com/api/rest-api/admin/settings/users/delete-self). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/users/list).

## 11. Themes

Per-channel storefront customization blocks (image carousels, static content, footer links, etc.) — not installable disk themes. Each block has a `type` and per-locale options.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/themes` | `adminSettingsThemes` |
| Detail | `GET /api/admin/settings/themes/{id}` | `adminSettingsTheme` |
| Create | `POST /api/admin/settings/themes` | `createAdminSettingsTheme` |
| Update | `PUT /api/admin/settings/themes/{id}` | `updateAdminSettingsTheme` |
| Delete | `DELETE /api/admin/settings/themes/{id}` | `deleteAdminSettingsTheme` |
| Mass delete | `POST /api/admin/settings/themes/mass-delete` | `createAdminSettingsThemeMassDelete` |
| Mass update status | `POST /api/admin/settings/themes/mass-update-status` | `createAdminSettingsThemeMassUpdateStatus` |

- Create is the first step (name/type/channel/sort/code); per-locale `options` are filled in via update. The detail payload inlines per-locale translations.
- **Image uploads inside carousel/services blocks are path strings only** — binary upload isn't exposed; use the admin panel for those.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/themes/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/themes/create), [update](https://api-docs.bagisto.com/api/rest-api/admin/settings/themes/update), [mass-update-status](https://api-docs.bagisto.com/api/rest-api/admin/settings/themes/mass-update-status). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/themes/list).

## 12. Data-Transfer Imports

Bulk-import catalog/customers/tax-rates/etc. from an uploaded file, then drive the import through its pipeline. **The upload (create/update) and the file downloads are REST-only** — multipart binary and file streams aren't expressible over GraphQL.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/settings/data-transfer/imports` | `adminSettingsDataTransferImports` |
| Detail | `GET /api/admin/settings/data-transfer/imports/{id}` | `adminSettingsDataTransferImport` |
| Create (multipart) | `POST /api/admin/settings/data-transfer/imports` | — (REST only) |
| Update (multipart) | `PUT /api/admin/settings/data-transfer/imports/{id}` | — (REST only) |
| Delete | `DELETE /api/admin/settings/data-transfer/imports/{id}` | `deleteAdminSettingsDataTransferImport` |
| Cancel | `POST /api/admin/settings/data-transfer/imports/{id}/cancel` | `cancelAdminSettingsDataTransferImportCancel` |
| Validate | `POST /api/admin/settings/data-transfer/imports/{id}/validate` | `validateAdminSettingsDataTransferImportValidate` |
| Start | `POST /api/admin/settings/data-transfer/imports/{id}/start` | `startAdminSettingsDataTransferImportStart` |
| Link | `POST /api/admin/settings/data-transfer/imports/{id}/link` | `linkAdminSettingsDataTransferImportLink` |
| Index | `POST /api/admin/settings/data-transfer/imports/{id}/index` | `indexAdminSettingsDataTransferImportIndex` |
| Stats | `GET /api/admin/settings/data-transfer/imports/{id}/stats` | `adminSettingsDataTransferImportStats` |
| Download source | `GET /api/admin/settings/data-transfer/imports/{id}/download` | — (REST only) |
| Download error report | `GET /api/admin/settings/data-transfer/imports/{id}/download-error-report` | — (REST only) |
| Download sample | `GET /api/admin/settings/data-transfer/imports/sample/{type}/{format}` | — (REST only) |

- **The import pipeline is a sequence:** create (upload file + pick type/action) → validate → start (loop the pending batches) → link → index. Drive it as a wizard with a progress view that polls **stats** between steps. The detail payload carries the row counts, error list, and state.
- **Cancel** only works while the import is `pending` or `processing`. The downloads stream the source file, the error report, and a sample template for a given type/format respectively.
- Docs: [list](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/list), [create](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/create), [validate](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/validate), [start](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/start), [link](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/link), [index](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/index), [stats](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/stats), [download-sample](https://api-docs.bagisto.com/api/rest-api/admin/settings/data-transfer-imports/download-sample). GraphQL: [list](https://api-docs.bagisto.com/api/graphql-api/admin/settings/data-transfer-imports/list), [start](https://api-docs.bagisto.com/api/graphql-api/admin/settings/data-transfer-imports/start).

---

## 13. UI/UX

**Datagrids (every list).** A shared table component driven by `{ data, meta }` + `?page`/`?per_page` (default 10, cap 50). Each list documents its own filters (AND-combined — more filters = more restrictive); render them as a filter bar with debounced text inputs and dropdowns for the enum filters. Column-header sort maps to the list's sort param. Use the `X-Total-*` headers (or `meta.total`) for the result count. On mobile, collapse the table into stacked cards (primary field + a couple of secondary fields + a row menu).

**Forms (create/edit).** One shared form per resource; the edit form pre-fills from the detail payload. Disable write-once fields on edit (currency `code`). Populate cross-references from the related list endpoints — channel forms pull locales/currencies/inventory-sources; tax-category forms pull tax-rates; user forms pull roles. Toggle conditional fields client-side (tax-rate zip mode) but trust the API's re-validation. Show inline field errors from `422` responses.

**Destructive actions.** Delete and mass-delete need a confirmation dialog naming what's being removed. Because several deletes are guarded (last currency/locale/channel/role/source, in-use tax category, self/last admin), present the returned guard message clearly — these aren't generic failures, they're business rules the user must act on.

**Multipart & binary.** The import upload (create/update) is `multipart/form-data` with the file part; the import downloads, the tax-rates CSV export, and sample templates are binary `GET`s — trigger them as file downloads (set `Accept` appropriately), don't try to render them as JSON. None of these have a GraphQL counterpart.

**Pipeline view (imports).** A stepper (Upload → Validate → Start → Link → Index) with live counts from the stats endpoint; a "Cancel" button enabled only while pending/processing; a "Download error report" link when the import produced errors.

---

## 14. Errors

| Status | When | UX |
|--------|------|----|
| 200 / 201 | Success | — |
| 204 | Deleted (no body) | Remove the row |
| 400 | Guarded delete / bad input (last currency, in-use source, etc.) | Show the returned message verbatim |
| 401 | Missing/expired/revoked token | Re-issue the token in the admin panel |
| 403 | Role lacks the permission | "You don't have permission for this" |
| 404 | Unknown id | — |
| 406 | Export requested without `Accept: text/csv` | Set the Accept header |
| 422 | Validation / ineligible action (zip-mode mismatch, unsupported export format, cancel a finished import) | Inline field/eligibility message |

---

## 15. Build checklist

**Foundation (currencies / channels / locales)**
- [ ] Currency list/CRUD + mass-delete; disable `code` on edit; surface last-currency / channel-base guards.
- [ ] Locale list/CRUD + mass-delete; show `direction`; surface last-locale / channel-default guards.
- [ ] Channel list/CRUD; populate locale/currency/inventory-source multi-selects; validate default-locale ∈ locales and base-currency ∈ currencies; no mass-delete.

**Money & tax (exchange rates / tax rates / tax categories)**
- [ ] Exchange-rate CRUD + mass-delete + an "Update Rates" auto-sync button; show provider errors.
- [ ] Tax-rate CRUD + CSV export; toggle single-zip vs zip-range fields; send `Accept: text/csv` for export; no mass-delete.
- [ ] Tax-category CRUD; attach tax-rate ids; surface the in-use delete guard; no mass-delete.

**Access (roles / users)**
- [ ] Role CRUD; `all` vs `custom` with a permission picker for `custom`; surface in-use / last-role guards; no mass-delete.
- [ ] User CRUD; require password on create, optional on update; wire self-delete (re-confirm password); surface self/last-admin guards; no mass-delete.

**Storefront & inventory (themes / inventory sources)**
- [ ] Theme list/CRUD + mass-delete + mass-update-status; two-step create-then-options; image fields path-only.
- [ ] Inventory-source CRUD + mass-delete; surface last-source / in-use guards.

**Imports (data transfer)**
- [ ] Import list/detail; multipart upload (create/update, REST only); the validate→start→link→index pipeline as a stepper polling stats; cancel (pending/processing only); the three binary downloads.

**Cross-cutting**
- [ ] Shared `{ data, meta }` table + per-resource filter bar (default 10, cap 50).
- [ ] Confirmation dialogs on every delete/mass-delete; render guard messages, not generic errors.
- [ ] Map `403` to a permission message; invalidate list/detail caches after each mutation.
