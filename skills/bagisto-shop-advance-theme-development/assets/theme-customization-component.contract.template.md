# Theme-Customization Component Contract

Use this before adding a merchant-editable component under **Admin → Settings → Themes**. Replace every placeholder with values discovered from the target checkout. Do not retain example identities, numeric IDs, paths, URLs, or locale lists.

## Decision

- Requested merchant outcome:
- Use installed type or custom type:
- Reason an installed type is insufficient, if custom:
- Package that owns the extension:

## Identity and scope

- Stable custom type code:
- Administrator label and translation keys:
- Target channel resolution:
- Target theme-code resolution:
- Installed/package type collision check:
- Status and sort-order behavior:
- Shared fields:
- Locale-specific fields:

## Option schema

| Field | Shape | Required | Locale-specific | Validation | Empty-state rendering |
|---|---|---:|---:|---|---|
| `<field>` | `<scalar/list/object>` | `<yes/no>` | `<yes/no>` | `<rule>` | `<behavior>` |

## Administrator editor

- Installed extension point or package-scoped override:
- Controller/store/update behavior for custom type:
- Update dispatch uses persisted type; requested type changes are rejected:
- Stock type delegation/regression strategy:
- Route names, methods, URI, middleware, ACL, and CSRF verified from installed source:
- Form/view integration point:
- Error and success behavior:
- Translation/RTL considerations:

## Media and links

- Allowed media fields, formats, size/dimensions, disk, and storage path:
- Text-only update preserves existing media:
- Replacement and deletion ownership/cleanup:
- Link validation, target, and rel policy:
- HTML/trust/sanitization policy:

## Storefront renderer

- Repository/controller retrieval path:
- Channel/theme/status/sort/locale filters:
- Type-to-Blade mapping:
- Missing data/media/entity fallback:
- Responsive, semantic, keyboard, and accessibility behavior:
- Cache invalidation and cache-key scope:

## Content lifecycle

- Empty state accepted:
- Starter content requested and approved:
- Idempotent natural key or merge behavior:
- No-delete/default conflict policy:
- Upgrade/uninstall/rollback plan:

## Verification

- Admin create/update/validation:
- Stock type regression:
- Route, ACL, CSRF, and events:
- Upload/replacement/deletion:
- Channel/theme/locale isolation:
- Sort/enable/empty state:
- Storefront, mobile, RTL, accessibility, and cache behavior:
