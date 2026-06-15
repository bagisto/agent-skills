# CMS menu

The CMS menu manages **static content pages** — About Us, Privacy Policy, Terms, Contact, and any other editorial page a shopper reads on the storefront. A CMS Page is per-channel (you choose which sales channels it belongs to) and **fully translatable** (each locale has its own URL key, title, HTML body, and meta fields). It's the simplest admin menu: one resource, the standard list → detail → action shape.

CMS Pages relate to the rest of the store loosely: they're linked from storefront navigation/footer and can be the target of a **URL Rewrite** (Marketing menu). They carry no products or pricing — they're pure content.

> **Source of truth:** this page gives the flow, endpoints, and UX. For the exact request/response body of any call, open its api-docs page (linked below). **Never invent a payload from memory** — open the page, confirm method/fields, then write the call.

**Auth, listing envelope, pagination, permissions, errors:** all in [`../connecting-to-the-api.md`](../connecting-to-the-api.md). GraphQL specifics: [`../graphql.md`](../graphql.md). Every call carries the admin Integration Bearer token; each action is capped by the admin's role (forbidden → **403**).

---

## CMS Pages

| Operation | REST | GraphQL field |
|-----------|------|---------------|
| List | `GET /api/admin/cms/pages` | `adminCmsPages` |
| Detail | `GET /api/admin/cms/pages/{id}` | `adminCmsPage` |
| Create | `POST /api/admin/cms/pages` | `createAdminCmsPage` |
| Update | `PUT /api/admin/cms/pages/{id}` | `updateAdminCmsPage` |
| Delete | `DELETE /api/admin/cms/pages/{id}` | `deleteAdminCmsPage` |
| Mass-delete | `POST /api/admin/cms/pages/mass-delete` | `createAdminCmsPageMassDelete` |
| Export (CSV) | `GET /api/admin/cms/pages/export?format=csv` | — (REST-only binary) |

Docs: [list](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/queries/list), [detail](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/queries/detail), [create](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/mutations/create), [update](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/mutations/update), [delete](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/mutations/delete), [mass-delete](https://api-docs.bagisto.com/api/graphql-api/admin/cms/pages/mutations/mass-delete), [export](https://api-docs.bagisto.com/api/rest-api/admin/cms/pages/export).

- **Detail** returns the full payload: `translations: [{ locale, url_key, page_title, html_content, meta_title, meta_keywords, meta_description }]` and the assigned `channels: [{ id, code, name }]`, both inlined — no follow-up calls.
- **Create vs Update bodies differ** — this is the one quirk to know:
  - **Create** takes **top-level** fields (`url_key`, `page_title`, `html_content`, `meta_*`) plus `channels: [ids]`. Those top-level translated values are broadcast to **every** configured locale.
  - **Update** takes a **locale-nested** body: `{ "<locale>": { url_key, page_title, html_content, meta_* }, channels: [ids], locale: "<code>" }`. Only the named locale is touched.

  So a create form is single-locale-then-broadcast; an edit form is locale-tabbed. Build them to match.
- **Validation:** `url_key` is required, slug-safe, and unique across page translations (excluding self on update); `page_title` and `html_content` required; `channels` must be non-empty and reference existing channel IDs. The `channels` set is **replaced** on every write (passing an empty/absent set detaches all channels) — always send the full intended channel list. Permission: cms-create / -edit.
- **Delete** removes the page (204); **mass-delete** takes `{ indices: int[] }` and silently skips non-existent IDs (empty/missing indices → 422). Permission: cms-delete.
- **Export** downloads the listing as a CSV attachment (ID, Page Title, URL Key, Channel, Locale) honouring the listing filters — send `Accept: text/csv`; only `?format=csv` is supported. REST-only (no GraphQL — binary).

---

## UI/UX

### Pages datagrid
- **Columns:** ID, URL Key, Page Title, Channel, Locale, Created At.
- **Filters:** ID, Page Title, URL Key, Channel, Locale. AND-combined — more filters = narrower result.
- **Sort:** ID (default), Page Title, URL Key, Created At. `?page` + `?per_page` (default 10, cap 50).
- **Mass-action:** row checkboxes → bulk delete (confirm first). Optional CSV export button (`Accept: text/csv`).

### Create / edit form
- A **rich-text (HTML) editor** for `html_content` is the centrepiece — pages are editorial. Treat the body as HTML; the storefront renders it as-is.
- **Channels:** a multi-select of available channels; always submit the full intended set (the write replaces it).
- **SEO panel:** `meta_title` / `meta_keywords` / `meta_description` per page.
- **Locale handling:** on **create**, one locale's content is captured and broadcast to all locales — present a single content form. On **edit**, render a **locale tab strip**; each tab edits one locale and the update call targets that locale only. Don't reuse the create body shape for edits.
- **URL key:** validate slug format inline; surface the uniqueness error (422) on the field.

### Mobile
- List → cards (title + url key + channel/locale pills); the HTML editor is awkward on small screens — consider a simplified editor or read-only preview with edit-on-desktop guidance; sticky save.

---

## Errors

| Failure | HTTP | Handle by |
|---|---|---|
| Validation (missing/invalid url_key, title, body, empty channels) | 422 | Inline field message; flag duplicate url_key on the field. |
| Empty mass-delete `indices` | 422 | Disable bulk-delete until rows are selected. |
| Role lacks the permission | 403 | "You don't have permission for this action." |
| Unknown id | 404 | — |
| Unsupported export format | 422 | Only `?format=csv`; send `Accept: text/csv`. |

Standard statuses: **200/201** · **204** (delete) · **401** · **403** · **422** · **404**. (See [`../connecting-to-the-api.md`](../connecting-to-the-api.md).)

---

## Checklist

- [ ] Datagrid listing (`GET /cms/pages`) with filters (ID/Page Title/URL Key/Channel/Locale), sort, `?page`/`?per_page`, bulk-delete checkboxes.
- [ ] Detail (`GET /cms/pages/{id}`) drives the edit form from the embedded `translations` + `channels` — no follow-up calls.
- [ ] **Create** uses the top-level broadcast body; **Update** uses the locale-nested body — two different form shapes.
- [ ] `channels` always sent as the full intended set (writes replace it); url_key slug + uniqueness validated inline.
- [ ] HTML editor for `html_content`; per-locale tabs on edit; SEO meta panel.
- [ ] Mass-delete (`{ indices }`) + optional CSV export (`Accept: text/csv`) wired.
- [ ] **Both transports:** admin Bearer token on every call; 403 surfaced; GraphQL — `adminCmsPage(s)` queries select `id`/`_id`+fields, mutations select documented result fields, inputs camelCase, cursor pagination on the list. See [`../graphql.md`](../graphql.md).
