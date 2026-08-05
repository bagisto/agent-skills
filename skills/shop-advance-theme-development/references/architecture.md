# Theme Architecture and Scaffold Modes

## Contents

- [Detect the installed architecture](#detect-the-installed-architecture)
- [Separate view and asset resolution](#separate-view-and-asset-resolution)
- [Choose a scaffold mode](#choose-a-scaffold-mode)
- [Build each mode](#build-each-mode)
- [Design the package installer](#design-the-package-installer)
- [Self-register theme configuration from the package](#self-register-theme-configuration-from-the-package)
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
7. Add `src/Console/Commands/InstallCommand.php` and register it from the service provider only while the application runs in console.
8. Record original Shop hashes for copied views, assets, and build configuration, plus the complete Shop view/asset/discovered-build-contract inventory that detects upstream additions and removals.
9. Preserve the exact installed Bagisto license notice for copied/derived files and audit third-party asset/font licenses.

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

## Design the package installer

Use this package shape for every generated package or full fork:

```text
<package-root>/
└── src/
    ├── Config/
    │   ├── themes.php          # theme entry, self-registered (see below)
    │   ├── bagisto-vite.php    # Vite registry entry — only with namespaced asset calls
    │   └── imagecache.php      # image-cache templates — only with theme-owned filters
    ├── CacheFilters/           # only when shipping a theme-owned imagecache.php
    │   ├── Small.php
    │   ├── Medium.php
    │   └── Large.php
    ├── Console/
    │   └── Commands/
    │       └── InstallCommand.php
    ├── Providers/
    │   └── <DerivedPackage>ServiceProvider.php
    └── Resources/
        └── views/
```

Derive the PHP namespace, class import, theme code, display name, publish tag, configured paths, and Artisan signature from validated scaffold inputs. Use `<theme-code>-theme:install`, without duplicating the `-theme` suffix when the theme code already ends with it.

Keep the default installer deliberately narrow:

- Register `InstallCommand` only inside the provider's console-runtime guard.
- Require the derived theme entry to be present before installation.
- Publish only the derived theme-view tag and never pass `--force`.
- Clear application caches after publishing.
- Warn when the configured production manifest is absent.
- Never select a channel, change `shop-default`, seed catalog data, rebuild indexes, create storage links, install dependencies, or run a frontend build.
- Return a failure status when publishing or cache clearing fails.

Treat an existing package command as a structural reference, not a template. Do not copy its namespace, signature, brand messages, seeders, demo options, product assumptions, or deployment tasks. Extend the generated installer only when the target package owns the corresponding migrations, seeders, publish groups, and rollback behavior, and the requested installation contract explicitly includes them.

### Preserve source and asset licenses

Treat licensing as a release gate, not a generated afterthought.

- Discover the license shipped with the exact installed Bagisto source and preserve its full notice with every substantial copied or derived portion.
- Keep the upstream notice separate from the theme author's chosen license; one does not replace the other.
- Do not infer that a font, photograph, icon set, payment logo, or bundled dependency has Bagisto's license. Inspect its own metadata and distribution terms.
- Record provenance and allowed use for every new brand asset.
- For a distributable package, declare the chosen package license in Composer metadata and include all required license/notice files in the release artifact.
- Stop and request a licensing decision when ownership or redistribution permission is unknown.

## Self-register theme configuration from the package

A distributable theme should register its own theme entry, Vite registry, and — when it ships image filters — image-cache templates from files **inside the package**, so a fresh install needs no hand edits to the application root `config/`. Ship these under `<package-root>/src/Config/`, keyed by theme code, and wire them from the provider's `register()`:

- `src/Config/themes.php` — the theme block (`name`, `assets_path`, `views_path`, `vite`).
- `src/Config/bagisto-vite.php` — the Vite registry entry (`hot_file`, `build_directory`, `package_assets_directory`), only when the theme makes namespaced `bagisto_asset()` / `bagisto_vite()` calls.
- `src/Config/imagecache.php` — image-cache `route` / `paths` / `templates` / `lifetime` / `cache_driver`, only when the theme ships its own `src/CacheFilters/` classes.

Keep every file keyed by the derived theme code (`'<theme-code>' => [ ... ]`) and every namespace derived from scaffold inputs — never hard-code a specific theme's code, class namespace, or paths.

**Match the installed config shape, not another package's.** Inspect the checkout before writing the provider: some Bagisto builds nest shop themes under `config('themes.shop.<code>')` and Vite registries under `config('bagisto-vite.viters.<code>')`, while some stock theme packages ship top-level-keyed files. Register into whatever the installed `Webkul\Theme` / `Webkul\ImageCache` code actually reads:

```bash
rg -n "config\('themes|config\('bagisto-vite|config\('imagecache" <shop-root> packages/
```

**Know your framework's `mergeConfigFrom` depth before relying on it.** Laravel's `ServiceProvider::mergeConfigFrom()` is a shallow `array_merge($packageConfig, $existingConfig)` — package values first, existing app config second — so the application wins every key collision. Consequences:

- It safely ADDS a brand-new top-level key (a theme code not present yet).
- It CANNOT insert a child into an already-populated nested array (e.g. `themes.shop`, `bagisto-vite.viters`): the existing array wins and the theme's entry is silently dropped.
- It appends to numeric-indexed lists (e.g. the `core` system-config groups), which is why `system.php` merges cleanly.

Choose the registration call by target. For a child inside an existing nested array, use a deterministic deep set that preserves siblings instead of `mergeConfigFrom`:

```php
public function register(): void
{
    $config = $this->app['config'];

    // Nested child keys → config()->set() (deep, sibling-preserving).
    foreach (require __DIR__.'/../Config/themes.php' as $code => $theme) {
        $config->set("themes.shop.{$code}", $theme);
    }

    foreach (require __DIR__.'/../Config/bagisto-vite.php' as $name => $viter) {
        $config->set("bagisto-vite.viters.{$name}", $viter);
    }

    // Global, theme-owned image cache (only when shipping CacheFilters).
    $config->set('imagecache', require __DIR__.'/../Config/imagecache.php');

    // Numeric-indexed / append-only groups → shallow merge is correct.
    $this->mergeConfigFrom(__DIR__.'/../Config/system.php', 'core');
}
```

Rules:

- Do the wiring in `register()` so the values are captured when the app builds `config:cache`. Verify each survives `php artisan config:cache` and clears cleanly.
- Own image dimensions in `src/CacheFilters/{Small,Medium,Large}.php` under the theme namespace. Mirror the installed filters' `applyFilter()` logic (URL-context branches, admin-config dimensions) so rendered sizes are unchanged unless a size change is an explicit requirement.
- `imagecache` is a single GLOBAL config; setting it makes the theme's filters authoritative app-wide. Acceptable for a single-theme storefront — flag it when multiple shop themes must coexist, and prefer leaving the installed filters in place there.
- Merge-only always: never wipe sibling themes, viters, or unrelated `imagecache` keys. When the application root config already hard-codes the theme, move that block into the package and replace the root block with a pointer comment — do not leave two sources of truth.
- Verify after wiring: the theme code resolves on its channel with siblings intact, the Vite manifest still loads the theme build, and the image-cache route returns `image/*` for `<route>/small|medium|large/<path>`.

## Parameterize and merge safely

Collect these values once:

- package display name;
- Composer package name;
- PHP namespace;
- theme code;
- installation command signature and publish tag;
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
- Insert one theme without replacing sibling themes. Prefer self-registering it from the package's `src/Config/themes.php` (see "Self-register theme configuration from the package") over editing the application root config.
- Insert one Vite registry only when explicit namespace resolution needs it; ship it from the package's `src/Config/bagisto-vite.php` when so.
- Register nested config children with a deep `config()->set()`, not shallow `mergeConfigFrom`, so siblings survive.
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
- Confirm the derived installation command is discoverable, collision-safe, and console-only.
- Run PHP formatting checks on generated providers.
- Run the production frontend build.
- Clear cached configuration and compiled views.
- Exercise the storefront with browser console and failed-request capture.

Re-run discovery after every Bagisto upgrade, then compare the current Shop baseline before refreshing a fork.
