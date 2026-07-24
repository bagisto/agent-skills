# Admin-Managed Theme-Customization Components

## Contents

- [Choose the right mechanism](#choose-the-right-mechanism)
- [Discover the installed contract](#discover-the-installed-contract)
- [Define the component contract](#define-the-component-contract)
- [Extend the Admin workflow safely](#extend-the-admin-workflow-safely)
- [Render the component on the storefront](#render-the-component-on-the-storefront)
- [Handle media and optional starter content](#handle-media-and-optional-starter-content)
- [Validate, upgrade, and remove safely](#validate-upgrade-and-remove-safely)
- [Avoid unsafe shortcuts](#avoid-unsafe-shortcuts)

Read this reference when a request requires a new, merchant-editable section or settings form under **Admin → Settings → Themes**. Use it for homepage sections as well as other theme-customization content. Do not use it merely to select or register a Shop theme.

## Choose the right mechanism

Start from the merchant outcome, not from a desired controller override.

1. Inspect the installed customization types and their forms.
2. Reuse an installed type when it supports the requested data and gives merchants a clear editing experience.
3. Create a custom type only when it needs a distinct structured schema, validation, editor, or storefront renderer.
4. Keep purely presentational, fixed theme markup in Blade/CSS when merchants do not need to manage it.
5. Use CMS or system configuration when that is the installed and more appropriate ownership model.

Complete `assets/theme-customization-component.contract.template.md` before changing code. Use a package-local registry or equivalent single source of truth for custom type codes and their Admin labels. Derive all identifiers from the requested theme/package; do not use an example theme, project, channel, locale, host, record ID, or component name.

## Discover the installed contract

Treat the target checkout as authoritative. Locate and read the installed source before choosing an extension seam:

```bash
rg -n "ThemeCustomization|theme_customizations|theme-customizations" <package-roots> --glob '*.php' --glob '*.blade.php'
rg -n "settings/themes|admin\.settings\.themes|theme_customization" <admin-source> --glob '*.php' --glob '*.blade.php'
rg -n "theme_code|channel_id|sort_order|translateOrNew|options" <theme-and-shop-source> --glob '*.php' --glob '*.blade.php'
```

Inspect all of the following in the installed version:

- the customization model, translations, migration/schema, repository, and upload/normalization behavior;
- the stock Admin index, create dialog, edit templates, controller validation, routes, middleware, ACL, authorization, events, and success/error behavior;
- the package/provider load order and view namespace or render-event mechanisms;
- the homepage controller and every existing renderer that consumes customization records;
- the installed cache listener or invalidation mechanism; and
- existing tests and fixtures for Admin settings and the storefront.

Record the exact existing type values and option shapes. A string column can permit a value in the database while the stock controller, form, DataGrid, or renderer still rejects or mishandles it.

Prefer documented render events, configuration hooks, or extension points. If none can support the requirement, use the narrowest package-scoped extension that preserves the installed public Admin contract.

## Define the component contract

Give the custom type one stable lower-snake-case code, unique within the application. Collision-check it against installed and package-defined types. Do not repeat it as uncoordinated literals across controllers, forms, renderers, tests, and seeders.

Define the schema before building the form:

| Concern | Specify before implementation |
|---|---|
| Scope | Current channel, selected theme code, enabled status, sort order, and whether every field is shared or locale-specific |
| Text | Required/optional fields, length limits, translation behavior, plain-text or trusted-HTML policy |
| Repeated data | Item keys, minimum/maximum count, stable ordering, and empty-state behavior |
| Links | Internal/external policy, URL validation, target/rel attributes, and optional labels |
| Media | Allowed formats, size/dimensions if required, storage disk/path policy, replacement, and deletion ownership |
| Commerce references | Product/category/entity identifiers, validation, missing/deleted-item behavior, and channel compatibility |
| Rendering | Blade component/partial mapping, semantics, responsive behavior, accessibility, and no-data fallback |

Do not alter core model constants or copy core source merely to store a custom code. Keep custom codes and Admin labels in the extension package. Use the installed translation mechanism for merchant-facing labels and validation messages; preserve all enabled application locales when adding translation keys.

Keep configuration data separate from content. A component definition describes fields and rendering. A customization record contains the merchant's content for one channel/theme/locale context.

## Extend the Admin workflow safely

### Prefer an extension point

First look for a supported Admin render event or a registered component mechanism that can add the type option and editor without replacing stock code. Preserve the surrounding UI, form conventions, file upload behavior, authorization, and event lifecycle.

### Use a narrow package-scoped override only when necessary

When the installed controller has a fixed type allowlist and no usable hook exists:

1. Create the extension controller in the theme or companion package; do not modify the installed Admin controller.
2. Delegate every stock type and branch to the parent implementation unchanged.
3. Validate the custom type, its common record fields, and its locale-specific option schema explicitly. Validate the channel against installed channels, the theme code against configured Shop themes, and the locale against the selected channel's enabled locales.
4. Preserve the installed route names, URI shape, HTTP methods, middleware, CSRF protection, ACL/authorization behavior, events, redirects, JSON responses, and error conventions.
5. Re-register only the exact endpoint(s) that need the extension, after the installed Admin route registration. Do not replace unrelated Admin routes, route groups, or middleware.
6. Load package-owned Admin views through the installed namespace/precedence convention. Override the smallest possible template surface and retain stock type choices and editing paths.
7. Add a custom edit form only for the custom code. On update, select the custom branch from the persisted record type, not an untrusted request value; reject type changes. Keep built-in component forms and their behavior unchanged.

Do not assume that later route registration, controller inheritance, view namespace precedence, or cache listeners work the same in another Bagisto version. Verify the installed route collection and provider load order, then add a regression test proving the intended controller and view are selected.

Validate uploaded files only when an actual uploaded file is present. Preserve stored media paths on an edit that changes only text. Authorize deletion only for media owned by the edited record, normalize stored paths before deletion, and never delete a shared or arbitrary user-supplied path.

Treat administrator-supplied HTML according to the application's existing trust and sanitization policy. Do not introduce raw HTML output or relax validation only for the custom editor.

Use the existing success messages, error rendering, and events where possible; fire each installed lifecycle event exactly once. Invalidate the same cache keys/listeners the installed workflow uses; include every affected channel/theme/host/locale/currency variant. Use a broader cache clear only when the target cache cannot safely invalidate those variants and the user accepts that operational cost.

## Render the component on the storefront

Keep the storefront mapping explicit and defensive:

1. Retrieve records through the installed repository/controller contract.
2. Filter by current channel, current theme code, enabled status, and installed sort order.
3. Resolve translated options for the current locale using the installed translation behavior.
4. Map the custom type code to a package-owned Blade component or partial.
5. Validate or escape output according to field policy; render safe empty states for missing optional fields, media, or referenced catalog entities.
6. Preserve the existing rendering path for every stock type.

Never render all records for a type without the channel and theme filters. Never use request input to choose an arbitrary template. Do not make the homepage depend on a starter record existing; an empty or disabled customization set must remain a valid state.

Keep component data serializable and request-scoped. Do not cache one channel's content or assets in global mutable state, and test each configured channel hostname separately.

## Handle media and optional starter content

Keep filesystem work, database content, and theme scaffolding separate.

When the user requests starter content:

1. Obtain explicit approval to create, copy, merge, or replace records.
2. Resolve the target channel by stable code and the theme by discovered configuration, never numeric IDs or hostnames embedded in a package.
3. Make the operation idempotent with a documented natural key or safe merge rule.
4. Do not delete merchant-created records by default.
5. Preserve translated values and only create files that the package is licensed to distribute.
6. Report created, updated, skipped, and conflicting records.

Do not seed media paths without ensuring their storage objects exist. Define cleanup for partially failed uploads and for record deletion. Do not package environment-specific CDN URLs, storage URLs, or database IDs.

## Validate, upgrade, and remove safely

Cover the custom component with the installed test stack:

- Admin creation and update with valid data, invalid data, and a stock component regression;
- correct route/controller resolution, middleware, CSRF, ACL, and event behavior;
- required versus optional locale values, including a right-to-left locale when enabled;
- media upload, text-only update preserving media, replacement, and safe deletion;
- current-channel and current-theme isolation, enabled/disabled behavior, and sort order;
- missing/deleted linked entities and empty component data;
- storefront output, semantics, keyboard behavior, responsive layout, and no cross-channel leakage;
- cache invalidation in every deployed host/channel variant; and
- package upgrade, uninstall, and migration/rollback behavior without corrupting stock records.

Before an upgrade, re-inspect the installed controller, route definitions, views, model/repository behavior, and cache listener. Treat changed extension seams as a compatibility task; do not blindly retain an override that was built for an earlier Bagisto release.

## Avoid unsafe shortcuts

Do not:

- edit the core Admin, Theme, or Shop packages only to add a theme component;
- add an undocumented type string to a database row without Admin and renderer support;
- replace the entire theme-settings controller or route group for one custom type;
- loosen validation, authorization, file rules, or HTML handling for convenience;
- overwrite or delete merchant content during a normal theme install or deploy;
- hardcode a project identity, a theme identity, locale list, channel ID, host, or storage URL; or
- mistake custom component registration for visual theme registration or channel activation.
