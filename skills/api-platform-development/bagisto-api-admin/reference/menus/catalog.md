# Catalog menu

The Catalog menu manages the **merchandise** an admin sells and the **structure** that describes it. It has four sub-menus, and they relate functionally — not as isolated screens:

- **Products** — the items in the store. Every product is built from an **Attribute Family**, browsed/filtered through **Categories**, and described by the fields its family exposes.
- **Categories** — the navigable tree a shopper browses; a product is assigned to one or more categories.
- **Attributes** — the dynamic fields a product can carry (name, price, color, size, brand, meta, …). Attributes of type select/multiselect/checkbox carry **options**.
- **Attribute Families** — named groupings of attributes (organised into attribute groups). When an admin creates a product, they pick a family; that family decides which attribute fields the product edit form renders.

So the build order matters: attributes and families are the **schema**, products are the **data**, categories are the **navigation**. An admin tool usually surfaces Products first (the daily workhorse) and treats Attributes / Families as configuration screens.

> **Source of truth:** this page gives the flow, endpoints, and UX. For the exact request/response body of any call, open its api-docs page (linked per resource). **Never invent a payload from memory** — open the page, confirm method/fields, then write the call.

**Auth, listing envelope, list→detail→action pattern, pagination, permissions, errors:** all in [`../connecting-to-the-api.md`](../connecting-to-the-api.md). GraphQL specifics (result-field rule, camelCase inputs, cursor pagination): [`../graphql.md`](../graphql.md). Every call carries the admin Integration Bearer token; each action is capped by the admin's role (a forbidden action returns **403**).

Each resource below is the same **list → detail → action** shape: a datagrid listing (`{ data, meta }` envelope, `?page` + `?per_page` + filters), a detail GET with relations embedded, and create/update/delete plus per-resource actions (copy, mass-actions, image/inventory/price sub-panels).

---

## Products

The core catalog screen. There are **two distinct product endpoints** — don't confuse them:

- **`GET /api/admin/catalog/products`** — the full **datagrid listing** documented here (all columns, 11 filters, sort, mass-actions). This is the Products management screen.
- **`GET /api/admin/products`** — a **slim Add-Product search** used by the Create-Order flow (sku/name/price/image/saleable only). It is *not* the product listing; see [`../flows/create-order.md`](../flows/create-order.md).

Products span seven types (simple / virtual / downloadable / grouped / bundle / configurable / booking). Create is a **two-step wizard**: step 1 creates a barebones row from `sku` + `attribute_family_id` (+ `type`, + `super_attributes` for configurable); step 2 (update) fills in the family's attribute fields, type structures, categories, etc. Mirror that — don't try to send the whole product in one call.

### Product CRUD & actions

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List (datagrid) | `GET /api/admin/catalog/products` | `adminCatalogProducts` |
| Detail | `GET /api/admin/catalog/products/{id}` | `adminCatalogProduct` |
| Create (step 1) | `POST /api/admin/catalog/products` | `createAdminCatalogProduct` |
| Update (step 2) | `PUT /api/admin/catalog/products/{id}` | `updateAdminCatalogProduct` |
| Delete | `DELETE /api/admin/catalog/products/{id}` | `deleteAdminCatalogProduct` |
| Copy | `POST /api/admin/catalog/products/{sourceId}/copy` | `createAdminCatalogProductCopy` |
| Mass-delete | `POST /api/admin/catalog/products/mass-delete` | `createAdminCatalogProductMassDelete` |
| Mass-update-status | `POST /api/admin/catalog/products/mass-update-status` | `createAdminCatalogProductMassUpdateStatus` |
| Export (CSV) | `GET /api/admin/catalog/products/export?format=csv` | — (REST-only binary) |

Docs: [list](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/list), [detail](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/products-detail), [create](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/create), [update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/update), [delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/delete), [copy](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/copy), [mass-delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/mass-delete), [mass-update-status](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/mass-update-status), [export](https://api-docs.bagisto.com/api/rest-api/admin/catalog/products/export).

- **Create** validates `sku` (required, unique, slug-safe) and `attribute_family_id` (required, exists). For `configurable`, `super_attributes` (a map of attribute code/id → option IDs) is required and the backend generates the full variant matrix. Booking sub-types are configured in step 2. Permission: product-create.
- **Update** is a true partial PATCH — send only the fields you change; every family attribute is editable by its code. Translatable values write to the requested locale (`?locale=&channel=`). Type-structure keys (`variants`, `bundle_options`, `links`, `downloadable_*`, `booking`) *replace* that structure. `categories` / `channels` / up/cross/related-sells replace their set when sent, preserved when omitted. Images / videos / inventories / customer-group-prices are ignored here — they have dedicated endpoints (below). Permission: product-edit.
- **Copy** refuses variants (a variant can't be copied standalone) → 422. Returns the new product's id + auto-suffixed sku. Permission: product-create.
- **Mass-delete / mass-update-status** take `{ indices: int[] }` (+ `value: 0|1` for status). Best-effort: missing IDs are silently skipped. Permission: delete / edit respectively.
- **Export** downloads the datagrid as a CSV attachment honouring the listing filters — send `Accept: text/csv`; only `?format=csv` is supported (else 422). REST-only (no GraphQL — binary).

### Product sub-panels (images, inventory, prices)

These mirror the tabs on the product edit screen. Each is parent-scoped under `/catalog/products/{productId}/…`.

| Sub-panel | Operation | REST | GraphQL field |
|-----------|-----------|------|---------------|
| **Images** | Upload | `POST /api/admin/catalog/products/{productId}/images` | `createAdminCatalogProductImage` (REST-only upload) |
| | Reorder | `PUT /api/admin/catalog/products/{productId}/images/reorder` | `reorderAdminCatalogProductImage` |
| | Delete | `DELETE /api/admin/catalog/products/{productId}/images/{id}` | `deleteAdminCatalogProductImage` |
| **Inventory** | List | `GET /api/admin/catalog/products/{productId}/inventories` | `adminCatalogProductInventories` |
| | Bulk update | `PUT /api/admin/catalog/products/{productId}/inventories` | `updateAdminCatalogProductInventory` |
| **Customer-group prices** | List | `GET /api/admin/catalog/products/{productId}/customer-group-prices` | `adminCatalogProductCustomerGroupPrices` |
| | Create | `POST /api/admin/catalog/products/{productId}/customer-group-prices` | `createAdminCatalogProductCustomerGroupPrice` |
| | Update | `PUT /api/admin/catalog/products/{productId}/customer-group-prices/{id}` | `updateAdminCatalogProductCustomerGroupPrice` |
| | Delete | `DELETE /api/admin/catalog/products/{productId}/customer-group-prices/{id}` | `deleteAdminCatalogProductCustomerGroupPrice` |

Docs: [image upload](https://api-docs.bagisto.com/api/rest-api/admin/catalog/products/images-upload), [image reorder](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/images-reorder), [image delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/images-delete), [inventory list](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/inventories-list), [inventory update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/inventories-update), [group-price list](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/customer-group-prices-list), [group-price create](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/customer-group-prices-create), [group-price update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/customer-group-prices-update), [group-price delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/products/customer-group-prices-delete).

- **Image upload is REST multipart only** — a binary `image` part (bmp/jpeg/jpg/png/webp, ≤4 MB) plus optional `position`. GraphQL cannot transport the binary, so the GraphQL upload mutation rejects with a pointer to the REST route. Reorder takes `{ order: [{id, position}] }`; delete removes the row and the file. Permission: product-edit.
- **Inventory** lists per-source quantities (`meta.totalQty` sums across sources); bulk update takes `{ inventories: { sourceId: qty } }` — omitted sources are left untouched, `qty=0` zeroes a source. Permission: product-edit.
- **Customer-group prices** are per-tier discount rows (`{ qty, value_type: fixed|discount, value, customer_group_id }`; null group = all groups). `(qty, customer_group_id)` must be unique per product. Permission: product-edit.

---

## Categories

The browsable tree. Categories have two listing shapes — a **flat datagrid** and a **nested tree** — plus full CRUD and mass-actions. There is **no separate move endpoint**: moving a category is an update with `parent_id` + `position`.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List (flat datagrid) | `GET /api/admin/catalog/categories` | `adminCategories` |
| Tree (nested) | `GET /api/admin/catalog/categories/tree` | `adminCategoryTrees` |
| Detail | `GET /api/admin/catalog/categories/{id}` | `adminCategory` |
| Create | `POST /api/admin/catalog/categories` | `createAdminCategory` |
| Update (incl. move) | `PUT /api/admin/catalog/categories/{id}` | `updateAdminCategory` |
| Delete | `DELETE /api/admin/catalog/categories/{id}` | `deleteAdminCategory` |
| Mass-delete | `POST /api/admin/catalog/categories/mass-delete` | `createAdminCategoryMassDelete` |
| Mass-update-status | `POST /api/admin/catalog/categories/mass-update-status` | `createAdminCategoryMassUpdateStatus` |

Docs: [listing](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-listing), [tree](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-tree), [detail](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-detail), [create](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-create), [update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-update), [delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-delete), [mass-delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-mass-delete), [mass-update-status](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/categories/categories-mass-update-status).

- **Flat vs tree:** use the flat datagrid for a searchable table; use the tree (full nested structure, filterable by locale/status/root) to render a draggable category tree. Detail returns **all locale translations** inlined plus the filterable-attribute IDs.
- **Create** validates slug/name/position/attributes (and the description per display mode); slug must be unique. **Update** uses a locale-nested body (`<locale>.slug`, `<locale>.name`, …). Permission: category-create / -edit.
- **Delete guards:** the root category (id 1) and any channel root category cannot be deleted → 400. Mass-delete pre-validates the whole batch and rejects up front if any ID is undeletable. Permission: category-delete.

---

## Attributes

The dynamic fields products carry. Attributes of type select/multiselect/checkbox own a set of **options** (with their own translations), managed as a sub-resource.

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/catalog/attributes` | `adminAttributes` |
| Detail | `GET /api/admin/catalog/attributes/{id}` | `adminAttribute` |
| Create | `POST /api/admin/catalog/attributes` | `createAdminAttribute` |
| Update | `PUT /api/admin/catalog/attributes/{id}` | `updateAdminAttribute` |
| Delete | `DELETE /api/admin/catalog/attributes/{id}` | `deleteAdminAttribute` |
| Mass-delete | `POST /api/admin/catalog/attributes/mass-delete` | `createAdminAttributeMassDelete` |
| Option — create | `POST /api/admin/catalog/attributes/{attributeId}/options` | `createAdminAttributeOption` |
| Option — update | `PUT /api/admin/catalog/attributes/{attributeId}/options/{optionId}` | `updateAdminAttributeOption` |
| Option — delete | `DELETE /api/admin/catalog/attributes/{attributeId}/options/{optionId}` | `deleteAdminAttributeOption` |

Docs: [listing](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-listing), [detail](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-detail), [create](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-create), [update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-update), [delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-delete), [mass-delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attributes-mass-delete), [options](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/attributes/attribute-options).

- **Create** validates code (unique, code-rule), admin name, type. **Update** is partial; supplying `options` replaces the full option set (upsert existing by id, delete omitted, insert new). System-attribute immutable fields (code/type) are not changed.
- **Options** are only allowed on select/multiselect/checkbox attributes; deleting an option referenced by a product is refused (409).
- **Delete guards:** a system attribute (403) or an attribute still used by a family (409) cannot be deleted. Mass-delete rejects up front if any ID is a system attribute. Permission: attribute-create / -edit / -delete.

---

## Attribute Families

Named groupings of attributes (organised into attribute groups). A family is chosen at product-create time and decides which attribute fields the product edit form renders — so families are the bridge between **Attributes** (the fields) and **Products** (the data).

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/catalog/families` | `adminAttributeFamilies` |
| Detail | `GET /api/admin/catalog/families/{id}` | `adminAttributeFamily` |
| Create | `POST /api/admin/catalog/families` | `createAdminAttributeFamily` |
| Update | `PUT /api/admin/catalog/families/{id}` | `updateAdminAttributeFamily` |
| Delete | `DELETE /api/admin/catalog/families/{id}` | `deleteAdminAttributeFamily` |

Docs: [listing](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/families/families-listing), [detail](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/families/families-detail), [create](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/families/families-create), [update](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/families/families-update), [delete](https://api-docs.bagisto.com/api/graphql-api/admin/catalog/families/families-delete).

- Detail returns `attributeGroups: [{ code, name, column, position, attributes: [...] }]` inlined — render this as the column layout of the product form.
- **Create / update** validate the family code (unique, code-rule), name, and each group's code/name/column. Update keys existing groups by id and new groups by a generated marker; omitted groups (and omitted attributes within a group) are removed. Permission: family-create / -edit.
- **Delete guards:** the last remaining family, or a family with any product attached, cannot be deleted → 400. Permission: family-delete. (No mass-delete — the admin screen has none.)

---

## UI/UX

### Products datagrid
- **Columns:** image, SKU, name, type, attribute family, status, price, ID (plus cheap meta fields — short description, weight, featured/new flags, special price, timestamps). Heavy relations (full images, categories, inventories, variants, customer-group prices) are detail-only — fetch them from the detail GET.
- **Filters (the datagrid's own set):** Channel, Name, SKU, Attribute Family, Price (range), ID, Status, Type. Multiple filters are **AND**-combined — more filters = a narrower result. Surface them as a filter bar; don't add filters the datagrid doesn't expose.
- **Sort:** name, sku, attribute family, price, quantity, ID (default, desc), status, type, channel. Both `?sort=name-asc` and `?sort=name&order=desc` forms work.
- **Mass-actions:** row checkboxes → bulk delete + bulk enable/disable (mass-update-status). Confirm destructive actions.
- **Create wizard:** screen 1 = type + family + sku; screen 2 = the family-driven edit form (the detail's `attributes`/`attributeGroups` block tells you which fields + their types + options to render). For configurable, present the super-attribute option picker on screen 1.
- **Edit form tabs:** General / Description / Meta / Settings / Price (from the family's attribute groups), plus Images (drag-drop upload + reorder), Inventory (per-source qty grid), Customer-Group Prices (tier table), Categories, Channels, Linked products. Each tab maps to its sub-endpoint.

### Categories
- Offer a **tree view** (drag to re-parent → update with new `parent_id`+`position`) and a **flat datagrid** (search/filter). Datagrid filters/sort per the listing docs.
- Edit form is locale-tabbed (name/slug/description per locale) + display-mode + position + filterable attributes + logo/banner paths.
- Guard the root + channel-root categories in the UI (no delete button) to avoid 400s.

### Attributes & Families
- Attributes: datagrid + edit form (code/admin-name/type/flags) with an **options editor** (add/edit/delete rows, translations) shown only for select-type attributes.
- Families: datagrid + a **group/column builder** (drag attributes into groups, set the 1/2 column) — drive it off the detail `attributeGroups` shape.

### Mobile
- Products list → cards (image + name + price + status pill); filters in a sheet; create wizard one step per screen; image upload from the camera/gallery; sticky save.

---

## Errors

| Failure | HTTP | Handle by |
|---|---|---|
| Validation / ineligible (bad sku, duplicate slug, invalid option type) | 422 | Inline field message; for create, surface which field failed. |
| Business-rule refusal (delete root category, last family, system attribute, in-use attribute/family) | 400 / 403 / 409 | Disable the action in the UI for known-undeletable rows; show the returned reason. |
| Copy a variant | 422 | Hide Copy on variant rows. |
| GraphQL image upload | 422 | Use the REST multipart route for binary uploads. |
| Role lacks the permission | 403 | "You don't have permission for this action." |
| Unknown id | 404 | — |
| Unsupported export format | 422 | Only `?format=csv`; send `Accept: text/csv`. |

Standard statuses: **200/201** · **204** (delete) · **401** · **403** · **400** · **404** · **422**. (See [`../connecting-to-the-api.md`](../connecting-to-the-api.md).)

---

## Checklist

**Products**
- [ ] Datagrid listing (`GET /catalog/products`) with the datagrid's own filters (Channel/Name/SKU/Family/Price/ID/Status/Type), sort, `?page`/`?per_page`, mass-action checkboxes.
- [ ] Don't confuse the datagrid with the slim `GET /api/admin/products` Create-Order picker.
- [ ] Detail (`GET /catalog/products/{id}`) drives the edit form; relations read from the embedded payload, not follow-up GETs.
- [ ] Create = two-step wizard (step 1 sku+family+type [+super_attributes]; step 2 update); configurable variant matrix understood.
- [ ] Update sent as partial PATCH; type-structure keys replace; `?locale=` targets a locale; images/inventory/prices routed to their own endpoints.
- [ ] Copy / mass-delete / mass-update-status / CSV export wired; export sends `Accept: text/csv`.
- [ ] Image upload via REST multipart; reorder + delete wired; inventory bulk-update + group-price CRUD wired.

**Categories**
- [ ] Flat datagrid + nested tree both rendered; move = update with `parent_id`+`position` (no /move endpoint).
- [ ] Locale-nested update body; create slug uniqueness; root + channel-root delete guarded in the UI.

**Attributes & Families**
- [ ] Attribute CRUD + options sub-resource (select-types only); system/in-use delete guards handled.
- [ ] Family CRUD with group/column builder driven by the detail `attributeGroups`; last-family / product-attached delete guards handled.

**Both transports**
- [ ] Admin Bearer token on every call; 403 (no permission) surfaced per action.
- [ ] GraphQL: fetchable resources select `id`/`_id`+fields; action/mass mutations select documented result fields; inputs camelCase; cursor pagination on lists. See [`../graphql.md`](../graphql.md).
