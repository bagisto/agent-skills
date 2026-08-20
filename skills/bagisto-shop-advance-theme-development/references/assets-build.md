# Asset and build contract

Read this reference when a task adds CSS, JavaScript, images, fonts, Vue behavior, Vite configuration, or deployment assets.

## Derive the toolchain

Read the installed Shop package before generating files:

- `package.json` for package manager scripts and dependency versions;
- `vite.config.*` for Vue/plugins, public root, hot file, build directory, entry points, chunking, preload, and asset URL behavior;
- `tailwind.config.*` for content globs, screens, tokens, safelist, and plugins;
- `postcss.config.*` for module format and plugins;
- the JavaScript entry reported from the installed Vite `input` contract for runtime plugins and global contracts.

Copy and minimally patch that contract. Never use versions embedded in documentation or this skill.

## Keep path invariants aligned

Make these values agree:

- active theme Vite block in `config/themes.php`;
- Vite `hotFile`;
- Vite `publicDirectory`;
- Vite `buildDirectory`;
- entry-point paths;
- package asset prefix;
- optional named registry in `config/bagisto-vite.php`;
- manifest location used during validation.

Compute relative paths from the actual package directory. Do not assume a fixed `../../../` depth.

## Preserve the storefront runtime

Treat the installed Shop asset tree as a coupled runtime. Do not copy `app.js` while removing dependencies or plugins it imports. Preserve installed Vue initialization, validation, emitter, Axios, calendar, debounce, and Shop plugins unless a deliberate replacement covers every consumer.

For a sparse package, copy/derive the complete asset runtime even though views remain sparse. Bagisto view fallback does not merge Vite manifests or JavaScript applications.

## Configure Tailwind safely

Scan:

- every theme source type present in the installed content globs, including Blade, JavaScript, TypeScript, or Vue;
- published theme views, if used;
- inherited Shop sources for sparse themes;
- any CMS/component sources that emit utility classes.

Preserve installed screens, safelist, plugins, and compatibility tokens before adding the theme design system. Do not delete a token merely because the first redesigned page does not use it; inherited views may still depend on it.

Prefer semantic theme roles layered on the installed compatibility tokens. Keep product, validation, status, focus, and destructive-action colors accessible and consistent.

## Handle assets deliberately

- Use responsive images and explicit dimensions to prevent layout shift.
- Eager-load only genuine LCP imagery; lazy-load below-the-fold media.
- Prefer modern formats where the target stack supports them.
- Self-host fonts when licensing and deployment allow it; subset weights and preload sparingly.
- Keep icon fonts/SVG references needed by inherited components.
- Avoid external render-blocking font or script dependencies without a measured reason.

## Build sequence

1. Finish Vite/Tailwind/PostCSS configuration.
2. Respect the repository's lockfile and package-manager policy.
3. Install dependencies only with user authorization when network or lockfile mutation is involved.
4. Run the installed build script from the theme package.
5. Confirm the manifest contains every expected CSS/JavaScript entry.
6. Check output paths and asset URLs for 404s.
7. Ensure a development hot marker cannot control production rendering.
8. Deploy package code and its matching manifest/assets atomically.

Do not activate a channel between source changes and a successful production build.

## Development server

Discover host, port, HTTPS, container, and public URL from the environment. Do not pick a port unconditionally. Verify the generated hot file and remove or exclude it from production deployment.

## Asset validation failures

When compilation fails:

1. Compare the theme package files to the installed Shop baseline.
2. Resolve missing imports against both dependencies and devDependencies.
3. Check ESM/CommonJS file extensions against `package.json` module type.
4. Verify Vue plugin registration and entry points.
5. Inspect Tailwind content paths from the package working directory.
6. Inspect Vite's manifest rather than assuming output filenames.
7. Re-run the skill validator before browser testing.
