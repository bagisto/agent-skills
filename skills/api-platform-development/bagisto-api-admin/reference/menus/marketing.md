# Marketing menu

Everything the admin panel's **Marketing** sidebar group manages, across its three sections: **Promotions** (cart rules + their coupons, catalog rules), **Communications** (email templates, events, campaigns, newsletter subscribers), and **Search & SEO** (search terms, search synonyms, URL rewrites, sitemaps). Each is a `list → detail → action` surface; this page gives the flow, the per-resource endpoint tables, the UI/UX, and the checklists. **Open the linked api-docs page for each call's exact body/response — never invent a payload from memory.**

> **Auth & conventions:** every call carries the admin Integration Bearer token, listings come back as `{ data, meta }`, and a token is capped by its admin's role (a forbidden action → 403). See [`../connecting-to-the-api.md`](../connecting-to-the-api.md). GraphQL specifics (action-mutation result fields, camelCase inputs, cursor pagination) are in [`../graphql.md`](../graphql.md). Doc base: `https://api-docs.bagisto.com`.

---

## 1. What this menu manages, and how it relates to the rest

| Section | Sub-menu | Manages | Relates to |
|---|---|---|---|
| **Promotions** | Cart Rules | Discounts applied to the **cart** at checkout, optionally gated by coupon codes | Apply per channel + customer group; coupons are a sub-resource. The discount shows up in cart/checkout totals. |
| | Catalog Rules | Discounts applied to **product prices** before the cart | Target products by condition; recalculate product prices per channel + group. |
| **Communications** | Email Templates | Reusable HTML email bodies | A **Campaign** picks a template to send. |
| | Events | Scheduled marketing dates that can drive campaigns | A campaign may reference an event. |
| | Campaigns | A newsletter send — template + audience | Resolves recipients from a customer group's subscribed members (or guest subscribers). |
| | Subscribers | The newsletter subscriber list | Created on the storefront; admin only toggles/removes. Mirrors onto the linked customer's subscription flag. |
| **Search & SEO** | Search Terms | What shoppers searched, with hit counts | Auto-recorded by the storefront search; admin edits the term + an optional redirect. |
| | Search Synonyms | Synonym sets that widen storefront search matches | Feed the storefront search engine. |
| | URL Rewrites | Redirects (301/302) for product / category / CMS-page URLs | SEO layer over the catalog + CMS. |
| | Sitemaps | XML sitemap definitions + generation | Walks public categories/products/pages to write XML files. |

---

## 2. The pattern (recap)

Each sub-menu is the same three-call shape from [`../connecting-to-the-api.md`](../connecting-to-the-api.md):

- **List** — `GET /api/admin/marketing/<resource>` → `{ data, meta }`; page with `?page=`/`?per_page=` (default 10, cap 50) + that screen's filters (AND-combined).
- **Detail** — `GET …/{id}` → the full record (rules embed conditions + channel/group associations).
- **Action** — `POST/PUT/DELETE` for CRUD, plus per-record actions (copy a rule, generate coupons, send a campaign, generate a sitemap) and mass-delete where the panel offers it.

---

## 3. Promotions

### Cart Rules

Cart-level discounts, optionally coupon-gated, scoped to channels + customer groups.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/cart-rules` | `adminMarketingCartRules` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-list) |
| Detail | `GET /api/admin/marketing/cart-rules/{id}` | `adminMarketingCartRule` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-detail) |
| Create | `POST /api/admin/marketing/cart-rules` | `createAdminMarketingCartRule` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-create) |
| Update | `PUT /api/admin/marketing/cart-rules/{id}` | `updateAdminMarketingCartRule` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-update) |
| Delete | `DELETE /api/admin/marketing/cart-rules/{id}` | `deleteAdminMarketingCartRule` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-delete) |
| Mass-delete | `POST /api/admin/marketing/cart-rules/mass-delete` | `createAdminMarketingCartRuleMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-mass-delete) |
| Copy | `POST /api/admin/marketing/cart-rules/{id}/copy` | `copyAdminMarketingCartRule` | [copy](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rules-copy) |

**Form essentials:** a rule needs at least one channel and one customer group; pick a coupon type (no-coupon vs a specific code) and an action type (by-percent / by-fixed / cart-fixed / buy-x-get-y); a percent discount is capped at 100. Dates (`starts_from` / `ends_till`) must be coherent. **Copy** replicates the rule disabled and name-prefixed "Copy of …" and returns the new rule's detail prefilled for editing — coupons are not copied (a code is unique). Update is a partial merge — send only the fields you change; supplying `channels` / `customer_groups` replaces those associations wholesale.

#### Cart Rule Coupons (sub-resource)

Coupons live under a specific cart rule. Create one at a time or bulk-generate.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/cart-rules/{cartRuleId}/coupons` | `adminMarketingCartRuleCoupons` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rule-coupons-list) |
| Create (single) | `POST /api/admin/marketing/cart-rules/{cartRuleId}/coupons` | `createAdminMarketingCartRuleCoupon` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rule-coupons-create) |
| Generate (bulk) | `POST /api/admin/marketing/cart-rules/{cartRuleId}/coupons/generate` | `createAdminMarketingCartRuleCouponGenerate` | [generate](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rule-coupons-generate) |
| Delete | `DELETE /api/admin/marketing/cart-rules/{cartRuleId}/coupons/{id}` | `deleteAdminMarketingCartRuleCoupon` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rule-coupons-delete) |
| Mass-delete | `POST /api/admin/marketing/cart-rules/{cartRuleId}/coupons/mass-delete` | `createAdminMarketingCartRuleCouponMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/cart-rule-coupons-mass-delete) |

**Single create:** the code must be unique; omitted usage-limits / expiry inherit from the parent rule. **Bulk generate:** specify length, format (alphabetic / alphanumeric / numeric), optional prefix/suffix, and quantity — it returns the generated codes. **Cross-rule isolation:** every coupon op checks the coupon belongs to the named cart rule (unknown parent → 404; foreign ids in a mass-delete are skipped). Build the coupons screen *inside* a cart rule's detail, never as a standalone list.

### Catalog Rules

Product-price discounts targeted by condition, scoped to channels + customer groups.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/catalog-rules` | `adminMarketingCatalogRules` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-list) |
| Detail | `GET /api/admin/marketing/catalog-rules/{id}` | `adminMarketingCatalogRule` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-detail) |
| Create | `POST /api/admin/marketing/catalog-rules` | `createAdminMarketingCatalogRule` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-create) |
| Update | `PUT /api/admin/marketing/catalog-rules/{id}` | `updateAdminMarketingCatalogRule` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-update) |
| Delete | `DELETE /api/admin/marketing/catalog-rules/{id}` | `deleteAdminMarketingCatalogRule` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-delete) |
| Mass-delete | `POST /api/admin/marketing/catalog-rules/mass-delete` | `createAdminMarketingCatalogRuleMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/promotions/catalog-rules-mass-delete) |

**Form essentials:** at least one channel + one group; an action type (by-percent / by-fixed / to-percent / to-fixed); percent discounts capped at 100; coherent dates; a free-form `conditions` array selecting which products the rule hits. Detail embeds the channels, groups, and full conditions. **Heads-up:** saving a catalog rule triggers a product-price recalculation on the store, which can be slow on a large catalog — show a saving/progress state and don't treat a slow response as a failure.

---

## 4. Communications

### Email Templates

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/templates` | `adminMarketingTemplates` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/templates-list) |
| Detail | `GET /api/admin/marketing/templates/{id}` | `adminMarketingTemplate` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/templates-detail) |
| Create | `POST /api/admin/marketing/templates` | `createAdminMarketingTemplate` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/templates-create) |
| Update | `PUT /api/admin/marketing/templates/{id}` | `updateAdminMarketingTemplate` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/templates-update) |
| Delete | `DELETE /api/admin/marketing/templates/{id}` | `deleteAdminMarketingTemplate` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/templates-delete) |

**Form:** name, status (active / inactive / draft), and an HTML content body (sent as a string — give the admin an HTML/rich-text editor). No mass-delete here.

### Events

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/events` | `adminMarketingEvents` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/events-list) |
| Detail | `GET /api/admin/marketing/events/{id}` | `adminMarketingEvent` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/events-detail) |
| Create | `POST /api/admin/marketing/events` | `createAdminMarketingEvent` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/events-create) |
| Update | `PUT /api/admin/marketing/events/{id}` | `updateAdminMarketingEvent` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/events-update) |
| Delete | `DELETE /api/admin/marketing/events/{id}` | `deleteAdminMarketingEvent` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/events-delete) |

**Form:** name, description, date — all required. No mass-delete.

### Campaigns

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/campaigns` | `adminMarketingCampaigns` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-list) |
| Detail | `GET /api/admin/marketing/campaigns/{id}` | `adminMarketingCampaign` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-detail) |
| Create | `POST /api/admin/marketing/campaigns` | `createAdminMarketingCampaign` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-create) |
| Update | `PUT /api/admin/marketing/campaigns/{id}` | `updateAdminMarketingCampaign` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-update) |
| Delete | `DELETE /api/admin/marketing/campaigns/{id}` | `deleteAdminMarketingCampaign` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-delete) |
| Send | `POST /api/admin/marketing/campaigns/{id}/send` | `createAdminMarketingCampaignSend` | [send](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/campaigns-send) |

**Form:** name, subject, an email template, a channel, and a customer group; an event is optional. **Send** queues the newsletter to the resolved audience — the customer group's subscribed members (or the guest subscriber list when the group is "guest") — and returns how many were queued. It refuses an inactive campaign (422). Treat **Send** as a confirm-gated action separate from save. No mass-delete.

### Newsletter Subscribers

Read-mostly moderation surface. **No create** — subscriptions originate on the storefront.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/subscribers` | `adminMarketingSubscribers` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/subscribers-list) |
| Detail | `GET /api/admin/marketing/subscribers/{id}` | `adminMarketingSubscriber` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/subscribers-detail) |
| Toggle subscription | `PUT /api/admin/marketing/subscribers/{id}` | `updateAdminMarketingSubscriber` | [toggle](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/subscribers-toggle) |
| Delete | `DELETE /api/admin/marketing/subscribers/{id}` | `deleteAdminMarketingSubscriber` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/communications/subscribers-delete) |

Toggling the `is_subscribed` flag also mirrors onto the linked customer's own subscription flag; deleting unsubscribes that customer first. No mass-delete.

---

## 5. Search & SEO

### Search Terms

Auto-recorded by storefront search. **No create** — admin only edits/deletes.

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/search-terms` | `adminMarketingSearchTerms` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-terms-list) |
| Detail | `GET /api/admin/marketing/search-terms/{id}` | `adminMarketingSearchTerm` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-terms-detail) |
| Update | `PUT /api/admin/marketing/search-terms/{id}` | `updateAdminMarketingSearchTerm` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-terms-update) |
| Delete | `DELETE /api/admin/marketing/search-terms/{id}` | `deleteAdminMarketingSearchTerm` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-terms-delete) |
| Mass-delete | `POST /api/admin/marketing/search-terms/mass-delete` | `createAdminMarketingSearchTermMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-terms-mass-delete) |

Only the term + an optional redirect URL are editable (hit/result counts are auto-recorded). Sort by usage to surface popular searches.

### Search Synonyms

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/search-synonyms` | `adminMarketingSearchSynonyms` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-list) |
| Detail | `GET /api/admin/marketing/search-synonyms/{id}` | `adminMarketingSearchSynonym` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-detail) |
| Create | `POST /api/admin/marketing/search-synonyms` | `createAdminMarketingSearchSynonym` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-create) |
| Update | `PUT /api/admin/marketing/search-synonyms/{id}` | `updateAdminMarketingSearchSynonym` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-update) |
| Delete | `DELETE /api/admin/marketing/search-synonyms/{id}` | `deleteAdminMarketingSearchSynonym` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-delete) |
| Mass-delete | `POST /api/admin/marketing/search-synonyms/mass-delete` | `createAdminMarketingSearchSynonymMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/search-synonyms-mass-delete) |

**Form:** a name + a `terms` set (comma-separated synonyms, e.g. `shirt,tshirt,tee`) — both required.

### URL Rewrites

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/url-rewrites` | `adminMarketingUrlRewrites` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-list) |
| Detail | `GET /api/admin/marketing/url-rewrites/{id}` | `adminMarketingUrlRewrite` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-detail) |
| Create | `POST /api/admin/marketing/url-rewrites` | `createAdminMarketingUrlRewrite` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-create) |
| Update | `PUT /api/admin/marketing/url-rewrites/{id}` | `updateAdminMarketingUrlRewrite` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-update) |
| Delete | `DELETE /api/admin/marketing/url-rewrites/{id}` | `deleteAdminMarketingUrlRewrite` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-delete) |
| Mass-delete | `POST /api/admin/marketing/url-rewrites/mass-delete` | `createAdminMarketingUrlRewriteMassDelete` | [mass-delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/url-rewrites-mass-delete) |

**Form:** entity type (product / category / cms_page), request path, target path, redirect type (301 / 302), and a locale.

### Sitemaps

| Operation | REST | GraphQL field | Docs |
|---|---|---|---|
| List | `GET /api/admin/marketing/sitemaps` | `adminMarketingSitemaps` | [list](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-list) |
| Detail | `GET /api/admin/marketing/sitemaps/{id}` | `adminMarketingSitemap` | [detail](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-detail) |
| Create | `POST /api/admin/marketing/sitemaps` | `createAdminMarketingSitemap` | [create](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-create) |
| Update | `PUT /api/admin/marketing/sitemaps/{id}` | `updateAdminMarketingSitemap` | [update](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-update) |
| Delete | `DELETE /api/admin/marketing/sitemaps/{id}` | `deleteAdminMarketingSitemap` | [delete](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-delete) |
| Generate | `POST /api/admin/marketing/sitemaps/{id}/generate` | `createAdminMarketingSitemapGenerate` | [generate](https://api-docs.bagisto.com/api/rest-api/admin/marketing/search-seo/sitemaps-generate) |

**Form:** a file name (ends with `.xml`) + a storage path (starts and ends with `/`). **Creating/updating does NOT auto-generate** — that's a deliberate, explicit **Generate** step that walks public categories/products/pages and writes the XML, returning the generated file paths + timestamp. If the store's sitemap feature is disabled, Generate still succeeds but returns no files. Delete removes the generated files too.

---

## 6. UI/UX

- **Datagrids everywhere:** each sub-menu is a paginated table with that screen's filters (cart rules: id/name/coupon-code/status/dates; catalog rules: id/name/status/dates; campaigns: name/status/template/event/channel/group; subscribers: email/channel/subscribed; search terms: term/channel/locale; etc.). Multiple filters narrow the result (AND).
- **Mass-actions** appear only where the panel offers them — cart rules, catalog rules, coupons (within a rule), search terms, synonyms, URL rewrites. Templates, events, campaigns, subscribers, sitemaps have **per-row delete only**.
- **Rule editors** are the heaviest forms: a channel + customer-group multi-select, an action-type picker with the discount field (clamp percent ≤ 100), a date range, and (catalog rules) a conditions builder. Show the embedded associations + conditions when editing.
- **Coupons live inside a cart rule** — render them as a tab/section on the rule's detail, with single-add + bulk-generate + per-row and bulk delete. Never as a top-level menu.
- **Action buttons** (copy rule, send campaign, generate sitemap) are confirm-gated and distinct from save; show the returned result (new rule id, queued count, generated file paths).
- **Read-mostly screens** (subscribers, search terms) hide the create affordance — they're storefront-fed. For search terms, default-sort by usage.
- **Mobile:** single-column cards; pin the primary filter; rule/condition builders collapse into stacked sections; destructive + send/generate actions confirm-gated.

---

## 7. Errors

| Failure | HTTP / GraphQL | Handle by |
|---|---|---|
| Validation (missing/invalid field, duplicate coupon code, percent > 100, incoherent dates, bad sitemap name/path) | 422 | Inline field errors. |
| Send an inactive campaign | 422 | Block Send until the campaign is active. |
| Coupon op across cart rules | 404 (or skipped in mass-delete) | Scope coupon calls to the owning rule. |
| Mass-action skips some ids | 200 (with skipped/deleted lists) | Show which rows were skipped. |
| Role lacks the permission | 403 | "You don't have permission for this." |
| Unauthenticated (missing/expired token) | 401 | Re-issue the token in the panel. |
| Not found | 404 | — |

---

## 8. Checklist

**Promotions**
- [ ] Cart Rules CRUD + mass-delete + **copy**; channels/groups multi-select, action-type + discount (percent ≤ 100), coherent dates.
- [ ] Coupons rendered inside a cart rule: single-create, bulk-generate (length/format/qty), delete, mass-delete; cross-rule isolation handled.
- [ ] Catalog Rules CRUD + mass-delete with conditions builder; slow-save (price recalc) shown as progress, not failure.

**Communications**
- [ ] Email Templates CRUD (name/status/HTML body).
- [ ] Events CRUD (name/description/date).
- [ ] Campaigns CRUD + **Send** (confirm-gated, queued-count shown, inactive → 422).
- [ ] Subscribers list/detail/toggle/delete; **no create** surface; toggle mirrors onto the customer.

**Search & SEO**
- [ ] Search Terms list/detail/update/delete/mass-delete; **no create**; term + redirect only editable; sort-by-usage.
- [ ] Search Synonyms CRUD + mass-delete (name + comma-separated terms).
- [ ] URL Rewrites CRUD + mass-delete (entity type / paths / redirect type / locale).
- [ ] Sitemaps CRUD + explicit **Generate** (no auto-generate on save; returns file paths; disabled-feature returns empty).

**Both transports**
- [ ] Admin Bearer on every call; REST listings read `{ data, meta }`, GraphQL uses cursor pagination.
- [ ] GraphQL mutations select documented result fields (not a generic `id`); inputs camelCase; custom list filter args per the docs.
