---
name: bagisto-shop-advance-theme-development
description: Use when building a storefront feature against the advanced shop theme workflow — the non-negotiable rules and the end-to-end procedure for delivering one. Trigger phrases include "shop advance theme", "advanced theme", "storefront feature", "theme workflow", "definition of done".
requires: bagisto-shop-theme-development, bagisto-coding-standards
license: MIT
---

# Shop Advance Theme Development

Build a distinctive storefront while preserving the installed Bagisto commerce, extension, content, and runtime contracts. Follow official Bagisto conventions, reconcile documentation with the target checkout, and prove behavior before activation.

## Non-negotiable rules

- Read every applicable repository instruction file before acting.
- Treat installed code/configuration as the executable source of truth; use official version-matched Bagisto sources for intent.
- Parameterize or discover every theme code, display name, namespace, package path, channel, locale, build path, tool version, and command.
- Never edit Bagisto Shop source, `vendor/`, generated build output, dependencies, lockfiles, or live channel state unless the user and repository policy authorize it.
- Prefer a sparse view overlay/package. Create a full fork only after the user accepts its upgrade surface.
- Derive the complete asset runtime from the installed Shop package; view fallback does not imply Vite/JavaScript/CSS inheritance.
- Preserve layout runtime responsibilities, render events, controller variables, routes, form fields, API shapes, product-type behavior, and enabled extensions.
- Make configuration edits merge-only. Never erase sibling themes/providers/autoload mappings or silently change `shop-default`.
- Use dry runs and collision checks. Never force-publish, delete, replace a directory with a symlink, seed destructive data, or overwrite a conflict automatically.
- Preserve the exact installed Bagisto license notice for copied/derived sources, choose the theme's own license explicitly before distribution, and verify every bundled asset's redistribution terms.
- Treat generated design recommendations as candidates, not authority. Reject any suggestion that weakens commerce clarity, accessibility, performance, licensing, merchant control, installed dependencies, or Bagisto runtime contracts.
- Use only this skill's bundled `bagisto-ui-ux` knowledge and generator for design intelligence. Do not require, discover, import, or call another design skill at runtime.
- Treat “dynamic,” “admin-controlled,” and “all functionality works” as evidence claims. Inventory every visible surface and installed/enabled commerce journey; do not infer them from a successful build or homepage screenshot.
- Do not add an animation library, UI framework, icon package, remote font, external script, or other dependency merely because a design tool recommends it. Discover the installed capability first and obtain authorization for dependency or network changes.
- Build and validate before selecting the theme on any channel. Keep rollback explicit.

## Reference files — load only what the current task needs

| File | Load when |
|---|---|
| [workflow.md](workflow.md) | The full workflow and the definition of done |

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
