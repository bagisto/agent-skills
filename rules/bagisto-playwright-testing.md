# Playwright End-to-End Testing

- CRITICAL: ALWAYS use the bagisto-playwright-testing skill for anything under `tests/e2e-pw/`.
- Three independent suites, one per package: `packages/Webkul/{Admin,Shop,Installer}/tests/e2e-pw/`. Run every command from the package directory, never the repo root.
- **[2.5]** Use the package scripts: `npm run install:browsers`, `npm run test:e2e`, and `npm run test:e2e -- <flags>` for `-g`, `--shard=i/n` or a spec path. `test:e2e:headed`, `:ui`, `:debug`, `:report` mirror the Playwright flags.
- **[2.4]** No package scripts exist; invoke Playwright directly — `npx playwright install --with-deps chromium` and `npx playwright test --config=tests/e2e-pw/playwright.config.ts`. Check `package.json` before assuming which form the checkout supports.
- **[2.5]** All configuration is read and validated once in `utils/env.ts` — base URL from `APP_URL` falling back to `BASE_URL`, plus `BAGISTO_ADMIN_EMAIL`, `BAGISTO_ADMIN_PASSWORD` and `HEADED`. Never read `process.env` from a config, spec, page object or fixture, and never hardcode a host.
- **[2.4]** `playwright.config.ts` loads the app `.env` itself and reads `APP_URL` only; `BASE_URL` is set by CI and ignored. To retarget a run, change `APP_URL`.
- **[2.5]** All paths live in `utils/paths.ts`, which locates the application by searching upward for `artisan` instead of counting `../`. Never hardcode a parent-walk and never import a path from `playwright.config.ts`.
- The suite shares one database and never rolls back. Assert on the record you created, never a global count or list position, and never rely on a hardcoded fixture value the run itself consumes — that spec passes once and fails on every rerun.
- `workers: 1`, `retries: 0`, `fullyParallel: false`, and CI shards Admin and Shop 10 ways; a spec may not depend on another spec having run.
- Admin auth is cached to `.state/admin-auth.json` by the `adminPage` fixture — never log in by hand in a spec, and keep `.state` gitignored.
- Specs name the intent; page objects own every locator. Scope a locator to the row first — the same action markup repeats per row and an unscoped one fails strict mode.
- Locators are private getters or private methods; a spec never holds a selector. Give the page object the assertion (`expectGrandTotal(amount)`) rather than exposing the locator. A public locator is only for a sibling page object that composes it.
- Member order in a page object: fields and constructor, then getters, then private locator methods, then private helpers, then public actions.
- No comments anywhere under `tests/e2e-pw/` — no `//`, no `/* */`, no docblock, in specs or page objects. If a step needs prose, rename the method so the name carries it.
- Generate test data inside `beforeEach`, never at module scope: one module-scope `Date.now()` gives every test in the file the same SKU or name, and `sku`/`url_key` are unique-validated, so the file passes only while cleanup never misses. Hold the value as a thunk (`value: () => generatedSku`) if a module-scope table needs it.
- Teardown must not leak: delete the record in a `finally` so an earlier failed step cannot strand it, and tolerate the case where the test never created the row. Positional cleanup (`.first()`, `.nth(2)`) targets whatever sits in that row, not what this test made.
- Spec filenames are lower-kebab (`buy-x-get-y-free.spec.ts`, not `buyXgetYfree.spec.ts`). Describe blocks and test titles are lower case throughout — including `rma`, `gdpr`, `sku`, `url` — single-spaced, with ` -> ` spaced on both sides.
- A file that declares a class is named exactly for that class — `CatalogAclPage.ts`, not `catalog.ts`; `ACLManagement.ts`, not `index.ts`; `TinymcePage.ts`, not `tinymce.ts`. Rename the file when the class name is good and the class when it is not, and follow the casing a sibling already set (`RmaCreatePage` beside `RmaManagePage`). Modules with no class stay lower-kebab (`utils/faker.ts`, `*.types.ts`).
