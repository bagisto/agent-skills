# Official sources and precedence

Use this reference whenever a task depends on Bagisto behavior that may have changed.

## Precedence

1. Read repository instructions and the target checkout.
2. Read the exact installed Bagisto package code and configuration.
3. Consult the official documentation for intended workflow and terminology.
4. Consult the matching official Git branch/tag when the documentation and checkout differ.
5. Record the discrepancy; do not silently force documentation examples onto a different installed contract.

Never copy dependency versions, view inventories, layout bodies, locale counts, or relative root depths from this skill. Discover them from the target checkout.

## Theme development

- Getting started: https://devdocs.bagisto.com/theme-development/getting-started.html
- Store themes: https://devdocs.bagisto.com/theme-development/creating-store-theme.html
- Theme packages: https://devdocs.bagisto.com/theme-development/creating-custom-theme-package.html
- Vite assets: https://devdocs.bagisto.com/theme-development/vite-powered-theme-assets.html
- Layouts: https://devdocs.bagisto.com/theme-development/understanding-layouts.html
- Blade components: https://devdocs.bagisto.com/theme-development/blade-components.html
- Blade Tracer: https://devdocs.bagisto.com/theme-development/blade-tracer.html
- Validation: https://devdocs.bagisto.com/theme-development/validation
- Email templates: https://devdocs.bagisto.com/theme-development/email-template.html
- Render events: https://devdocs.bagisto.com/advanced/view-render-events.html
- Testing: https://devdocs.bagisto.com/advanced/testing.html
- Package development: https://devdocs.bagisto.com/package-development/getting-started.html
- Package localization: https://devdocs.bagisto.com/package-development/localization.html

## Official agent guidance

- Bagisto shop-theme-development skill: https://github.com/bagisto/agent-skills/blob/main/skills/shop-theme-development/SKILL.md

Use the official agent skill as an intent and coverage cross-check. Keep this skill's precedence unchanged: target repository instructions and installed source still override generic examples.

## Official source repository

- Repository: https://github.com/bagisto/bagisto
- Supported branch requested by the user: select the matching branch or tag; do not assume `master`.
- Theme engine: `packages/Webkul/Theme/src/`
- Shop frontend: `packages/Webkul/Shop/src/Resources/`
- Shop provider and routes: `packages/Webkul/Shop/src/Providers/` and `src/Routes/`
- Theme configuration: `config/themes.php`
- Named Vite registry: `config/bagisto-vite.php`

## Drift checks

Compare documentation examples with the installed:

- `composer.json` and package manifests;
- `package.json`, Vite, Tailwind, and PostCSS configuration;
- Shop application entry point and plugins;
- master layout and render-event anchors;
- component tree and props;
- locale directories and direction configuration;
- enabled packages, product types, payment methods, and tests.

If a documented command is destructive, forced, or overwrites published files, replace it with a collision check, dry run, backup/rollback decision, and explicit user authorization.
