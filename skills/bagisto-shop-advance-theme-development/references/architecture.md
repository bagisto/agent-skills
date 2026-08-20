# Theme Architecture and Scaffold Modes

## Contents

- [Detect the installed architecture](#detect-the-installed-architecture)
- [Separate view and asset resolution](#separate-view-and-asset-resolution)
- [Choose a scaffold mode](#choose-a-scaffold-mode)
- [Build each mode](#build-each-mode)
- [Parameterize and merge safely](#parameterize-and-merge-safely)
- [Validate the architecture](#validate-the-architecture)

Read this reference before creating a theme, changing its package boundary, or deciding whether to copy Shop source.

## Detect the installed architecture

Treat the checked-out application as the source of truth.

1. Locate the theme registry instead of assuming its path:

   ```bash
   rg -n "'shop-default'|'views_path'|'assets_path'|'build_directory'" <project-root>/config <discovered-theme-package-root>
   ```

2. Locate the active-theme middleware and theme view finder:

   ```bash
   rg -n "getCurrentChannel.*theme|class ThemeViewFinder|addThemeNamespacePaths" <shop-root> <discovered-theme-package-root>
   ```

3. Locate the Shop view namespace and anonymous-component registration:

   ```bash
   rg -n "loadViewsFrom|anonymousComponentPath" <shop-root> --glob '*ServiceProvider.php'
   ```

4. Locate the current Shop frontend baseline:

   ```bash
   rg --files <shop-root> | rg '/?(package.json|vite.config|tailwind.config|postcss.config)'
   ```

5. Read the discovered files completely before generating configuration.
6. Derive dependency declarations, entry points, plugins, breakpoints, colors, and PostCSS module format from those files.
7. Detect the application release from Composer metadata or the installed package source.
8. Branch on discovered classes and config keys, not on a remembered release number.
9. Stop and report an unsupported architecture when required hooks are absent.

Use this source-of-truth order:

1. Installed PHP classes and providers.
2. Installed Shop build configuration and asset imports.
3. Application theme configuration.
4. Package documentation matching the installed release.
5. Generated examples only after reconciling them with the first four sources.

## Separate view and asset resolution

Do not describe view inheritance and asset inheritance as the same mechanism.

| Concern | Resolve from | Expected fallback |
|---|---|---|
| Page and partial views | Active theme view path or registered theme namespace | Fall back through configured parent paths and the Shop namespace when supported |
| Anonymous `shop` components | Shop component namespace plus themed view lookup | Fall back to the original Shop component |
| Unqualified `@bagistoVite` entries | Active theme's nested Vite settings | Do not assume parent-theme asset fallback |
| `bagisto_asset` without a namespace | Active theme's Vite manifest | Do not assume parent-theme asset fallback |
| Explicitly namespaced assets | The matching Vite registry entry | Fail when the registry entry is missing |

Follow these rules:

- Override only the view files that need different markup in an overlay.
- Preserve the relative path beneath the Shop view root.
- Place the main layout override at the same component path used by `<x-shop::layouts>`.
- Use `parent` only after verifying that the installed theme manager supports parent paths.
- Use `views_namespace` only after registering that namespace with `loadViewsFrom`.
- Keep `views_path` for a filesystem overlay when no package namespace is needed.
- Give every active theme that calls unqualified Vite helpers a valid hot-file and build-manifest configuration.
- Build a theme-owned asset bundle when changing CSS, JavaScript, fonts, images, or runtime plugins.
- Reuse an existing bundle only as an explicit, documented choice and verify that its manifest contains every requested entry.
- Keep the public build directory, hot-file name, and theme registry values identical across PHP and Vite configuration.

Understand the runtime order:

1. Resolve the current channel.
2. Read its selected theme code.
3. Fall back to the configured shop default only when the selected code is absent or invalid.
4. Set the active theme's view paths.
5. Resolve `shop::` views against the active overlay before the original Shop path.
6. Resolve unqualified assets against the active theme's Vite settings.

## Choose a scaffold mode

Choose one mode before writing files.

| Mode | Choose when | Copy views | Package boundary |
|---|---|---|---|
| `overlay` | Change a limited set of templates while intentionally keeping the active base theme's asset bundle and visual system | Copy only changed paths | Local resource tree; no package runtime |
| `package` | Create a distinct visual system with sparse overrides and a complete theme-owned asset runtime | Copy only maintained overrides; inherit the rest | Self-contained package source; local or Composer registration |
| `full-fork` | Deliberately own the complete installed Shop view and asset runtime | Copy the complete current Shop view tree | Same package boundary as `package`, with a larger upgrade surface |

Use `package` for a fully restyled production theme even when it overrides only a few views. Use `overlay` only when sharing the base CSS/JavaScript is an explicit constraint; view inheritance does not provide asset inheritance.

Choose the full fork only when the user accepts:

- a large maintenance diff;
- manual reconciliation after Shop upgrades;
- duplicated components and email templates;
- broader regression testing.

Choose Composer registration only when installation into a second clean application is part of acceptance. Keep scaffold mode and registration strategy separate.

## Build each mode

### Build an overlay

1. Create the view root before copying any file.
2. Copy only the required relative view paths.
3. Keep missing views available through Shop fallback.
4. Reuse the selected base theme's Vite settings deliberately; switch to `package` if independent CSS or JavaScript is required.
5. Register a new theme entry without replacing existing theme entries.
6. Leave the global default unchanged unless the user requests a global fallback change.
7. Record each overridden path and the complete Shop view/asset/discovered-build-contract inventory for upgrade review.
8. Return to the primary workflow's build, manifest, validator, and runtime gates. Activate on a test channel only from workflow step 7 after those gates pass.

Use a shape such as:

```text
<overlay-root>/
├── views/
│   ├── components/layouts/index.blade.php
│   └── home/index.blade.php
└── .bagisto-theme-baseline.json
```

### Build a sparse package

1. Create `Resources/views` plus a complete installed Shop asset runtime.
2. Copy only the Shop-relative views the theme will maintain.
3. Register package views with `loadViewsFrom` and a unique `views_namespace` when the installed finder supports it.
4. Keep the package namespace as the authoritative source. Publish views only when editable application copies or unnamespaced view resolution require it; never force-publish.
5. Preserve installed package, Vite, Tailwind, PostCSS, entry-point, and dependency contracts.
6. Choose exactly one registration strategy: checkout-local PSR-4/provider wiring or Composer installation/discovery.
7. Record original Shop hashes for copied views, assets, and build configuration, plus the complete Shop view/asset/discovered-build-contract inventory that detects upstream additions and removals.
8. Preserve the exact installed Bagisto license notice for copied/derived files and audit third-party asset/font licenses.

### Build a full fork

1. Create `Resources/views` and `Resources/assets` explicitly.
2. Copy the installed Shop source, not a stale embedded template.
3. Copy the installed package, Vite, Tailwind, and PostCSS configuration together.
4. Rename only package identity, hot file, server port when needed, and build directory.
5. Preserve all current Vite plugins, source globs, breakpoints, design tokens, and render hooks.
6. Add the selected autoload/provider registration with merge-aware edits.
7. Keep the fork's origin revision or source hash in installation metadata outside generated UI code.
8. Preserve the installed Bagisto license and all applicable third-party notices alongside the fork.
9. Run the complete Shop regression matrix after every upstream refresh.

### Make a package distributable

1. Add a package-level `composer.json`.
2. Declare PSR-4 autoloading for the chosen namespace.
3. Declare explicit supported Bagisto and Laravel ranges; do not publish a package whose compatibility is known only from the authoring checkout.
4. Register the service provider through package discovery when the host supports it.
5. Register package views with `loadViewsFrom` and a unique namespace.
6. Point `views_namespace` at that registered namespace when the installed theme finder supports it.
7. Publish views only when editable application copies are an explicit product requirement.
8. Choose one asset delivery contract:
   - build assets in the consuming application;
   - publish supported prebuilt assets;
   - provide both with an explicit precedence rule.
9. Provide mergeable installation configuration rather than replacing the host theme registry.
10. Test install, update, disable, and uninstall behavior in a second application.
11. Choose and declare the theme package's own license; separately retain the installed Bagisto license notice for copied/derived sources.
12. Inventory bundled images, fonts, icons, scripts, and styles and retain every applicable third-party notice or redistribution condition.

Do not call a package self-contained when it requires undocumented root-file edits or leaves its runtime assets outside the package without an installation step.

### Preserve source and asset licenses

Treat licensing as a release gate, not a generated afterthought.

- Discover the license shipped with the exact installed Bagisto source and preserve its full notice with every substantial copied or derived portion.
- Keep the upstream notice separate from the theme author's chosen license; one does not replace the other.
- Do not infer that a font, photograph, icon set, payment logo, or bundled dependency has Bagisto's license. Inspect its own metadata and distribution terms.
- Record provenance and allowed use for every new brand asset.
- For a distributable package, declare the chosen package license in Composer metadata and include all required license/notice files in the release artifact.
- Stop and request a licensing decision when ownership or redistribution permission is unknown.

## Parameterize and merge safely

Collect these values once:

- package display name;
- Composer package name;
- PHP namespace;
- theme code;
- package path;
- view namespace;
- view path;
- asset path;
- hot-file name;
- build directory;
- development port;
- parent theme, when applicable.

Derive filenames and class names from those values.

Validate each value before mutation:

- Require a lowercase, stable theme code.
- Reject path separators in identifiers.
- Reject an existing package or theme code unless update mode is explicit.
- Detect namespace collisions.
- Detect occupied development ports when starting Vite.

Apply edits idempotently:

- Insert one PSR-4 entry without replacing the autoload map.
- Insert one provider without reordering unrelated providers.
- Insert one theme without replacing sibling themes.
- Insert one Vite registry only when explicit namespace resolution needs it.
- Preserve comments and user formatting where practical.
- Show the planned diff before deleting or overwriting files.
- Avoid `rm -rf` in the normal development path.
- Quote every generated filesystem path.

## Validate the architecture

Verify all of the following before styling:

- Resolve the selected theme code on the intended channel.
- Resolve one overridden `shop::` page from the theme.
- Resolve one non-overridden page from Shop fallback.
- Resolve one overridden anonymous component.
- Render the active theme's Vite entry points.
- Find the production manifest at the configured build directory.
- Load an image and font referenced from compiled CSS.
- Confirm that no existing theme entry disappeared.
- Confirm that the global fallback changed only when requested.
- Run Composer autoload validation for package classes.
- Run PHP formatting checks on generated providers.
- Run the production frontend build.
- Clear cached configuration and compiled views.
- Exercise the storefront with browser console and failed-request capture.

Re-run discovery after every Bagisto upgrade, then compare the current Shop baseline before refreshing a fork.
