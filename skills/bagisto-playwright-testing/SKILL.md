---
name: bagisto-playwright-testing
description: Use when writing, changing or debugging a Bagisto end-to-end test — deciding what to cover, Playwright specs, page objects, locators, assertions, ACL role coverage, fixtures, test data, admin-versus-storefront coverage, a regression test, or a failing E2E run. Trigger phrases include "playwright", "e2e", "end to end", "spec.ts", "page object", "browser test", "add tests for", "flaky test", "regression test", "shard".
---

# Playwright Testing

## Do not write the spec first

"Add Playwright tests for X" is not an instruction to start typing a spec. It is
an instruction to find out what X actually does, what already covers it, and
which of its behaviours a browser can prove that a Pest test cannot.

A test written before that investigation is usually a duplicate, a test of the
wrong layer, or a test that passes whether or not the feature works. All three
cost more than they return: someone maintains them, and nobody can trust them.

Work the pipeline:

```
UNDERSTAND FEATURE → INSPECT APPLICATION CODE → INSPECT VALIDATION AND BUSINESS RULES
  ↓
MAP IMPACT SURFACE → INSPECT EXISTING TESTS, PAGE OBJECTS, FIXTURES AND DATA HELPERS
  ↓
IDENTIFY WORKFLOWS AND STATE TRANSITIONS → BUILD COVERAGE MATRIX → DECIDE E2E VS PEST
  ↓
DESIGN TEST DATA AND PREREQUISITE STATE → DESIGN LOCATORS → IMPLEMENT
  ↓
RUN → CLASSIFY FAILURES → STABILISE → VERIFY ASSERTIONS → VERIFY REGRESSION BEHAVIOUR
  ↓
RUN FINAL QUALITY GATE
```

| Phase | Read | Produces |
|---|---|---|
| Investigate | [investigation.md](investigation.md) | The feature, its rules, its impact surface, and what already covers it |
| Design | [test-design.md](test-design.md), [admin-and-shop.md](admin-and-shop.md) | State transitions, a coverage matrix, an E2E-vs-Pest call per scenario |
| Implement | [authoring.md](authoring.md), [test-data.md](test-data.md), [locators.md](locators.md), [assertions.md](assertions.md) | A spec and its page object |
| Time-dependent work | [time-and-timezone.md](time-and-timezone.md) | Booking, rental, slot, availability and "today" coverage that holds in CI |
| Prove | [troubleshooting.md](troubleshooting.md) | A run that passes for the right reason, twice |
| Gate | [quality-gate.md](quality-gate.md) | A completed checklist |

**Scale the process to the change.** A one-line locator fix needs the
investigation step (why did the locator break?) and the proof step (does it still
fail when the feature does?), not a coverage matrix. A new feature area needs all
of it. What never gets skipped: reading the application code, and proving the
test can fail.

## How to think about this work

- **Maximise meaningful behavioural coverage, not test count.** Ten tests that
  differ only in input value are one test with a data table.
- **A passing test is not evidence of a good test.** Ask separately whether it
  *could* have failed — if the feature were deleted, would this go red?
- **Do not copy an existing test without deciding what it proves.** These suites
  contain tests that assert only that a toast appeared.
- **A business prerequisite is not an execution dependency.** Establish the state
  you need; never rely on another spec having run.
- **Do not add a wait without naming the thing you are waiting for.**
- **Classify a failure before changing anything.** If the application is wrong,
  the red test is doing its job — never edit an assertion to get green.
- **Choose a locator because it is stable and uniquely identifies the intended
  element**, never because it is short or made strict mode quiet.
- **Search before you build.** A new fixture, helper or page object is the last
  resort, after reuse, extension and refactoring.
- **A regression test is not finished until it has failed against the bug.**
- **Prefer the strongest behavioural verification with the least machinery**, and
  stop when the risks are covered — [test-design.md](test-design.md) says when.

## Architecture

Three independent Playwright projects, one per package, plus a small root-level
layer of **dependency-free** helpers all three import through `@shared/*`.

```
tests/e2e-pw/helpers/       # shared, dependency-free — imported as @shared/*
├── env.ts                  # readEnv() → baseUrl, adminEmail, adminPassword, timezone, headed
├── faker.ts                # uniqueStamp, generateName, generateEmail, generateSlug, …
├── paths.ts                # createE2ePaths(e2eRootPath)
├── prices.ts               # formatPrice
└── regex.ts                # escapeRegExp

packages/Webkul/{Admin,Shop,Installer}/tests/e2e-pw/
├── playwright.config.ts    # testDir ./tests, workers 1, retries 0, chromium
├── setup.ts                # adminPage / shopPage fixtures (Installer has neither)
├── tsconfig.json           # strict; @pages/* @utils/* @data/* @shared/*
├── pages/                  # BasePage.ts + page objects (admin/ and shop/)
├── tests/                  # *.spec.ts — Admin by menu, Shop by customer journey
├── utils/                  # package-local helpers, and the wrappers over @shared/*
└── data/                   # fixture files for uploads
```

**Why the shared layer must stay dependency-free.** CI runs `npm install` inside
`packages/Webkul/<project>` only — there is no root `node_modules`, in CI or
locally. Anything under `tests/e2e-pw/helpers/` therefore has to run with no
imports of its own: no `@playwright/test`, no `dotenv`, no third-party package.
Pure TypeScript over `process.env`, strings, numbers and dates.

That constraint, not taste, decides where code goes:

| Put it in | When |
|---|---|
| `tests/e2e-pw/helpers/` | Genuinely useful to more than one suite **and** dependency-free — value generation, string/price formatting, environment parsing, path arithmetic |
| `<package>/tests/e2e-pw/utils/` | It needs a package dependency, or encodes something only that suite knows |
| `<package>/tests/e2e-pw/pages/` | It drives a screen |

`utils/env.ts` is the pattern to copy: shared `readEnv()` does the parsing and
validation, and the package's `utils/env.ts` owns the `dotenv` call — the
dependency stays where the dependency is installed. `utils/faker.ts` does the
same, re-exporting `@shared/faker` and adding package-local generators
(`generateSKU` in Admin, `generateLocation` in Shop). A pure helper with no
package-local variant, such as `escapeRegExp`, is imported straight from
`@shared/regex` by the page objects that need it.

**The suites still share no page objects, fixtures or specs.** Each carries page
objects for whatever screens it must drive, including the other side's — that is
what keeps them independently runnable. Never import across package boundaries.
If both suites need the same *dependency-free* logic it belongs in `@shared/*`;
if it needs Playwright, each suite keeps its own copy.

Per-test timeouts are 60 s in Admin, 240 s in Shop (plus a 2 h global cap) and
300 s in Installer; `expect` waits 30 s in all three. A single long flow raises
its own with `test.setTimeout(...)`; never raise the config. `utils/env.ts` is
the only place `process.env` is read and `utils/paths.ts` owns every path —
never read either directly.

## Running

Run from the package directory, never the repo root — that is where
`node_modules` lives. All three packages expose the same scripts:

```bash
cd packages/Webkul/Admin          # or Shop, or Installer
npm install && npm run install:browsers
npm run test:e2e
npm run test:e2e -- tests/catalog/categories.spec.ts -g "create a category"
npm run typecheck                 # tsc --noEmit over the suite
```

`test:e2e:headed`, `:ui`, `:debug` and `:report` mirror the Playwright flags.
Admin and Shop need a running, installed, seeded app; Installer needs an
*uninstalled* one. [troubleshooting.md](troubleshooting.md) has the environment
contract.

## Non-negotiables

- **The suite shares one database and does not roll back.** An E2E run leaves
  every record it creates. Assertions must survive that: scope to the row you
  created, never to a global count or a list position.
- **A test owns its state.** It creates what it needs, restores any global
  setting it changed, and deletes only what it made. Never operate on "the first
  row" or an arbitrary existing record because it was convenient —
  [test-data.md](test-data.md).
- **Tests are independently runnable, across suites too.** `workers: 1` and file
  order are not permission to depend on another test having run, and a Shop spec
  never assumes an Admin spec configured anything —
  [admin-and-shop.md](admin-and-shop.md).
- **Admin auth is cached** to `.state/admin-auth.json` by the `adminPage` fixture.
  Do not log in by hand in a spec; the Shop promotion specs that call
  `loginAsAdmin(page)` are legacy — see [authoring.md](authoring.md).
- **Rebuild assets before running** after any frontend change, or the browser
  loads the previous bundle and the failure will look like a test bug.
- **No comments anywhere under `tests/e2e-pw/`** — no `//`, no `/* */`, no
  docblock. This is a Bagisto convention, held without exception across all three
  suites today, and it diverges from generic Playwright advice deliberately. Put
  the reason in a method name instead; [authoring.md](authoring.md) shows how.
- **Generate test data inside `beforeEach`, never at module scope.** One
  module-scope `uniqueStamp()` gives every test in the file the same SKU, and the
  file only passes while cleanup never misses.
- **A test that depends on the clock is a timezone question first.** The app runs
  on `APP_TIMEZONE` (`Asia/Kolkata` here) and the configs pin Node and the browser
  to the same zone. Anything involving today, tomorrow, slots, availability or
  expiry is investigated with [time-and-timezone.md](time-and-timezone.md) before
  anything else.
- **"Flaky" is a conclusion, not a starting hypothesis.** One shard failing, one
  database driver failing, or a local pass are not evidence of flakiness. Get the
  trace, the timestamps and the server log first —
  [troubleshooting.md](troubleshooting.md).
- **Filenames are lower-kebab** and **a file that declares a class is named
  exactly for it** — `CatalogAclPage.ts`, not `catalog.ts`. Describe and test
  titles are lower case with single spaces. No numeric ordering prefixes.

The spec names the intent and composes the workflow; the page object owns every
locator and asserts through named `expect…` methods. A spec that contains a CSS
selector belongs in a page object instead — [authoring.md](authoring.md).

**REQUIRED SUB-SKILL:** Use bagisto-change-verification before calling any change done.
