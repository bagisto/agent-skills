## Workflow

### 1. Discover the target

Resolve `<skill-dir>` from this `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/inspect_theme_environment.py \
  --project-root <project-root> \
  --theme-code <existing-theme-code> \
  --json
```

Omit `--theme-code` only when no theme exists yet or the task intentionally inventories every configured theme.

Inspect the reported:

- Bagisto/Shop source and version;
- repository instructions and protected paths;
- configured themes, fallback, paths, namespaces, and Vite registry;
- Shop Composer/frontend dependencies, scripts, Vite/Tailwind/PostCSS files, entry points, components, routes, tests, and locales;
- existing theme package, published path, symlink, manifest, and override scope.

Stop if the script cannot safely parse the architecture. Inspect the files directly; do not guess. Read [official-sources.md](references/official-sources.md) when documentation or versions matter.

### 2. Define the outcome and mode

For a new visual system or substantial redesign:

1. Read [design-quality.md](references/design-quality.md), [commerce-design-direction.md](references/commerce-design-direction.md), and [bagisto-ui-ux-foundations.md](references/bagisto-ui-ux-foundations.md). Read [bagisto-ui-ux-interactions.md](references/bagisto-ui-ux-interactions.md) when motion or interactive presentation is in scope. These are design resources; use the architecture and implementation references only after approving the visual direction.
2. Collect the brand promise, industry, audience, price position, catalog character, tone, content constraints, and anti-goals. Choose provisional `variance`/`motion`/`density` dials.
3. Run the bundled, self-contained `bagisto-ui-ux` generator. It reads this skill's original Bagisto commerce design knowledge, inspects the checkout, selects accessible candidates, derives page-level design exceptions and Laravel/Vue/Tailwind guidance, and emits a candidate report without network access or persistence:

   ```bash
   python3 <skill-dir>/scripts/generate_bagisto_ui_ux.py \
     --project-root <project-root> \
     --project-name <display-name> \
     --industry <industry> \
     --audience <audience> \
     --tone <tone-keywords> \
     --catalog <catalog-character> \
     --price-position <price-position> \
     --variance <1-10> \
     --motion <1-10> \
     --density <1-10> \
     --json
   ```

4. Review the selected archetype, supporting influence, palette, typography strategy, signatures, tokens, page blueprints, page dials, interaction policy, alternatives, and stack guidance. Resolve every `bagisto_review` finding. Treat all output as unapproved candidates; approve actual font, icon, image, and motion assets separately.
5. Synthesize one brand-specific archetype, composition, merchandising hierarchy, semantic token system, and page-level exceptions. Complete the relevant fields from `assets/theme-brief.template.md` in approved task notes or a brief file. Record the `bagisto-ui-ux` query plus accepted, adapted, and rejected recommendations. Do not create a project documentation file unless the user or repository policy permits it.
6. When a brief file is created, validate it before styling:

   ```bash
   python3 <skill-dir>/scripts/validate_theme_brief.py \
     --brief <theme-brief.md> \
     --strict
   ```

If the bundled knowledge file or generator fails validation, stop and repair this skill or use an explicitly documented manual design direction. Do not silently call another skill, use network recommendations, or fabricate generator results.

When the user asks for teaching, handoff, or step-by-step help—or identifies as a beginner—read [developer-guidance.md](references/developer-guidance.md) and use its guided delivery mode. Keep the same technical gates for every experience level; change the explanation and implementation granularity, not the quality bar.

Read [architecture.md](references/architecture.md), then choose:

- `overlay`: a small view-only change that intentionally reuses the base asset bundle and visual system;
- `package`: the default for a distinct production theme—sparse views plus a theme-owned installed Shop asset runtime;
- `full-fork`: an explicit complete Shop snapshot with recorded upgrade responsibility.

Use a Composer-discovered package when distribution across applications is required. Use the checkout's local PSR-4/provider convention only for an application-local package. Do not combine both registration strategies.

Inventory target channels, enabled locales/currencies/product types/extensions, merchant-managed content, supported browsers, accessibility target, performance budgets, required journeys, theme license, and asset provenance before implementation.

### 3. Plan and scaffold without collisions

Run the scaffolder without `--apply` first:

```bash
python3 <skill-dir>/scripts/scaffold_theme.py \
  --project-root <project-root> \
  --theme-code <theme-code> \
  --display-name <display-name> \
  --mode package \
  --registration local \
  --vendor <php-vendor> \
  --package <php-package> \
  --override <shop-relative-blade-path>
```

Review every identity and integration snippet plus every `planned_actions` source, destination, state, and checksum. Run again with `--apply` only when the plan matches the requested mode. The script creates new files, accepts byte-identical reruns, and rejects conflicts; it does not edit host configuration or activate a channel.

Use `--registration composer --bagisto-constraint <supported-range> --theme-license <spdx-expression> --theme-license-file <project-relative-license-file>` only for a distributable package with an explicitly tested Bagisto range and an approved theme license. The scaffold retains the discovered Bagisto notice separately. Never Composer-install and locally register the same provider.

For an existing theme, do not scaffold. Inspect it, then compare the actual source tree (not a merely configured publish destination):

```bash
python3 <skill-dir>/scripts/diff_theme_overrides.py \
  --project-root <project-root> \
  --theme-path <theme-package-or-views-path> \
  --expected-theme-code <theme-code> \
  --fail-on baseline-drift
```

The diff auto-discovers `.bagisto-theme-baseline.json` at the exact theme source root and distinguishes theme edits from installed Shop changes across views, assets, and the discovered build-contract graph. Its complete Shop view/asset/build-contract inventory catches added and removed upstream files; its theme-owned hashes catch newly added, removed, and concurrently changed overrides. This baseline does not inventory Shop PHP, controllers, providers, or runtime data contracts; the recorded Bagisto release and regression tests gate those. Use `--theme-code <theme-code>` only when its configured `views_path` exists and is the authoritative override tree.

If an existing theme has no baseline, treat the nonzero result as “not yet auditable.” Review its current upstream diff; do not accept current hashes merely to silence the gate.

### 4. Integrate using installed conventions

Merge only the required theme entry and one chosen package-registration strategy. Preserve all current configuration. Keep active-theme Vite settings synchronized with Vite output; add a named Vite registry only for explicit namespaced asset calls or an installed requirement.

Do not register models/Concord for a view-and-asset-only theme. Do not activate the theme yet.

Read [assets-build.md](references/assets-build.md) before changing build files or dependencies. Respect the target lockfile and package-manager policy; obtain approval for installs/network or dependency changes.

### 5. Implement from the installed contracts

Use Blade Tracer only in development and restore its previous state. Copy the exact Shop-relative view before overriding it.

- Read [blade-vue-events.md](references/blade-vue-events.md) for layouts, components, inline Vue, script timing, and render events.
- Read [cms-channels-data.md](references/cms-channels-data.md) for home/footer/services content, channels, CMS, logos, favicon, and theme-customization records.
- When the request is for a new merchant-editable homepage section in **Admin → Settings → Themes**, decide whether an installed type is sufficient before adding a custom one. For a new type or editor, read [admin-theme-customization-components.md](references/admin-theme-customization-components.md) and complete `assets/theme-customization-component.contract.template.md`. Keep the extension package-scoped; never modify the installed Admin or Theme package just to add a component.
- Read [commerce-contracts.md](references/commerce-contracts.md) before changing catalog, product, cart, checkout, account, payment, shipping, or extension-sensitive views.
- Read [localization-seo-media.md](references/localization-seo-media.md) for translations, RTL, metadata, semantics, images, icons, and fonts.
- Apply the approved semantic tokens and page compositions from the theme brief. Preserve installed Tailwind compatibility tokens for inherited views; do not scatter raw colors, arbitrary spacing, one-off shadows, or unrelated motion through Blade templates.

Implement the smallest coherent override set. Keep merchant content editable, keep the server authoritative for commerce state, and preserve meaningful server-rendered output before Vue enhancement.

### 6. Build and validate

Run the repository-approved formatter, translation checker, affected PHP tests, and theme build. Then run:

```bash
python3 <skill-dir>/scripts/validate_theme.py \
  --project-root <project-root> \
  --theme-code <theme-code> \
  --package-dir <package-dir>
```

Resolve failures; explain warnings. Re-run `validate_theme_brief.py` when the approved direction changes. Read [testing-deployment.md](references/testing-deployment.md) and run its applicable storefront matrix with console, page-error, failed-request, mobile, RTL, accessibility, and performance evidence. Adapt `assets/storefront-smoke.template.spec.ts` only when the checkout lacks equivalent coverage.

For every new/redesigned theme, every activation/release decision, or any request to prove dynamic/admin-controlled content or complete storefront functionality, read and follow the embedded [bagisto-theme-testing skill](references/bagisto-theme-testing/SKILL.md). Use its folder resources to:

1. inventory the installed Shop/Admin Playwright coverage and conditional product/extension surface;
2. map every visible storefront block to its Bagisto owner;
3. prove admin save → scoped storefront propagation → restoration in an isolated environment;
4. exercise every applicable commerce journey and explicitly account for exclusions;
5. validate the completed ownership manifest before claiming readiness.

Static Blade inspection and screenshots are discovery/visual evidence only; they do not prove merchant control or commerce correctness.

For new scaffolds, keep the generated `.bagisto-theme-baseline.json`; it records theme-owned Shop sources plus the complete Shop view/asset/discovered-build-contract inventory without embedding an absolute host path. After an existing theme has been reconciled and every applicable test passes, preview the complete path/hash document with `--json`, review it, then repeat with the apply flags:

```bash
python3 <skill-dir>/scripts/snapshot_upgrade_baseline.py \
  --project-root <project-root> \
  --theme-code <theme-code> \
  --theme-path <theme-package-or-views-path> \
  --scaffold-mode <overlay-or-package-or-full-fork> \
  --json
```

Then replace `--json` with `--apply --acknowledge-reviewed`.

Use `assets/override-baseline.template.json` only when an external process must create the same schema. Re-run the override diff after upgrades, and refresh accepted hashes only after validation passes.
For a later reconciled upgrade, preview with `--refresh --json`, then apply with `--refresh --apply --acknowledge-reviewed`; refresh atomically replaces only a valid baseline bound to the same theme and Shop identity.

### 7. Activate and hand off

After every required gate passes:

1. Confirm theme-customization content exists or has an approved empty/fallback strategy.
2. Record the current theme and rollback action for the intended channel.
3. Select the new theme only on that channel.
4. Clear/rebuild relevant caches and reload long-running processes when needed.
5. Run production smoke tests and roll back source/assets/channel selection together on failure.

Report changed files, discovered baseline, scaffold mode, integration strategy, license/notice and asset-provenance decisions, build/manifest results, tests and browsers/locales/product types/extensions covered, accessibility/performance evidence, activation state, rollback, override diff, and every skipped check with risk.

## Definition of done

Do not claim completion until the theme is brand-specific, visually coherent, responsive, merchant-usable, upgrade-auditable, and proven across the requested commerce journey. A completed brief, successful home-page render, or asset build alone is insufficient.
