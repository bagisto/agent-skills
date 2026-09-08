# Troubleshooting a Playwright failure

## Contents

- [Triage before touching the test](#triage-before-touching-the-test)
- [Strict mode violations](#strict-mode-violations)
- [Clicks that never land](#clicks-that-never-land)
- [Locators that match nothing](#locators-that-match-nothing)
- [Failures caused by leftover data](#failures-caused-by-leftover-data)
- ["Flaky" is a conclusion, not a starting hypothesis](#flaky-is-a-conclusion-not-a-starting-hypothesis)
- [A flash message that never appeared](#a-flash-message-that-never-appeared)
- [Debugging from a CI artifact](#debugging-from-a-ci-artifact)
- [Where configuration comes from](#where-configuration-comes-from)
- [Environment faults mistaken for bugs](#environment-faults-mistaken-for-bugs)
- [A test that passes when it should not](#a-test-that-passes-when-it-should-not)

## Triage before touching the test

Every failure writes a directory under `tests/e2e-pw/test-results/<test-name>/`
containing `error-context.md` (the error plus a page snapshot), a full-page
screenshot, a video, and `trace.zip`.

```bash
awk '/# Error details/,/# Page snapshot/' test-results/<dir>/error-context.md
npx playwright show-trace test-results/<dir>/trace.zip
```

The error text names the cause far more often than the stack does. Read it, then
classify the failure before changing anything — the fix is different for each,
and guessing wastes a run:

| Class | Tell | Fix belongs in |
|---|---|---|
| **Application bug** | The screenshot shows the app doing the wrong thing | The application — the test is working |
| **Wrong expectation** | The app is right and the test's claim about it was never true | The assertion, after re-reading the code |
| **Locator** | Strict-mode violation, or a locator matching nothing while the element is on screen | [locators.md](locators.md) |
| **Synchronisation** | It passes headed, or passes on a rerun | [locators.md](locators.md) |
| **Test data** | A count, an index, "already been taken", or a record the test did not create | [test-data.md](test-data.md) |
| **Cleanup** | The first run passes and the second does not | [test-data.md](test-data.md) |
| **Global state** | A spec that passed alone fails after another spec ran | [admin-and-shop.md](admin-and-shop.md) |
| **Auth / session** | Redirected to `admin/login`, or a customer action performed as a guest | Below |
| **Clock / timezone** | A date, slot, availability or expiry assertion; fails only in CI, or only at some times of day | [time-and-timezone.md](time-and-timezone.md) |
| **Flash message lost** | A redirect landed on the right page but the success or error message is absent | Below |
| **Stale build** | The component being targeted does not exist in the DOM at all | `npm run build` |
| **Environment** | Every test fails, or fails at navigation | Below |

### Never edit a test just to make it pass

The point of the classification is this decision:

- **If the application is wrong, the test is doing its job.** Leave it red, report
  it, and fix the application — or, if that is out of scope, say plainly that the
  test is exposing a real defect. Weakening an assertion to get green deletes the
  only thing that noticed.
- **If the test is wrong, fix the test** — and fix the cause, not the symptom.
  Relaxing an assertion, adding `.first()`, or raising a timeout are symptom fixes
  that convert a failing test into a test that cannot fail.

Before changing an assertion, be able to say which of the two it is. "The test
was too strict" is a conclusion that needs evidence from the application code,
not a convenient explanation for a red run.

The other expensive mistake is deciding "it's flaky" and adding a wait. That is a
diagnosis of last resort, not first.

## Strict mode violations

`resolved to N elements` means the locator is not scoped, not that Playwright is
being strict for no reason. In an admin list every row carries the same markup,
so a page-level locator matches every row.

```ts
await page.getByText("Delete", { exact: true }).click();

const row = this.sectionRow(name);
await row.locator("button.icon-dots").click();
await row.getByText("Delete", { exact: true }).click();
```

Do not silence it with `.first()` — that trades an error for a test that asserts
about an arbitrary element.

Two other sources of the same error:

- **A container that also matches.** A row selector like `div.border-b` also
  matches the drawer header showing the same record's name. Prefer a selector
  unique to the list (`div[data-draggable]`).
- **The debug bar.** With `APP_DEBUG=true` and Laravel Debugbar enabled, the
  flash message is rendered a second time inside a `sf-dump` panel, so
  `getByText("… successfully")` resolves to two elements locally and one in CI.
  Set `DEBUGBAR_ENABLED=false` while running E2E locally.

## Clicks that never land

`element intercepts pointer events` names the element on top. In Bagisto that is
almost always an open drawer, modal or overlay.

Creating a record often opens its edit drawer immediately, which then covers the
list. Close it before acting on the list behind it:

```ts
await this.closeDrawerButton.click();
await expect(this.publishActiveButton).toBeHidden();
```

Sortable lists are driven by pointer events, so `dragTo` is unreliable. Take the
handle and move it:

```ts
const handle = this.sectionRows.nth(from).locator("span.section-handle");
const target = await this.sectionRows.nth(to).boundingBox();

await handle.hover();
await this.page.mouse.down();
await this.page.mouse.move(target.x + target.width / 2, target.y + target.height / 2, { steps: 12 });
await this.page.mouse.up();
```

A stray click near a drag handle can start a real drag and reorder the list. If a
spec's later assertions drift for no visible reason, suspect this.

## Locators that match nothing

- **Icon-font glyphs pollute the accessible name.** A tile rendered as an icon
  span plus a label span does not answer to
  `getByRole("button", { name: "Static Content" })`. Target the label:
  `locator("span").filter({ hasText: /^Static Content$/ })`.
- **Schema-driven fields have no `name` attribute.** Address them through the
  label above the control — see [locators.md](locators.md).
- **The element is behind a `v-if` that has not resolved.** Wait for a stable
  anchor (`await this.createForm.waitFor()`), not a fixed timeout.
- **The string is not the string.** Assertions match translated text; check the
  lang file rather than the UI you remember.
- **The bundle is stale.** After any frontend change run `npm run build` in the
  package, or the browser loads the previous JS and the component you are
  targeting does not exist yet.

## Failures caused by leftover data

The E2E suites share one database and **do not roll back**. Every record a run
creates is still there for the next run.

Symptoms: an assertion on a count (`Failed asserting that 42 is identical to 2`),
on "the first row", on a total that grew between two runs of the same command, or
a 422 with "The sku has already been taken".

Fixes, in order of preference:

1. Assert on the uniquely-named record you created, never on a count or an index.
2. If a spec must leave the app in a particular state, put the state back.
3. When cleaning dev data by hand, **delete by explicit id only.** A predicate
   like `name LIKE '% Copy'` will eventually match something a person created.

The design rules that prevent this are in [test-data.md](test-data.md).

## "Flaky" is a conclusion, not a starting hypothesis

None of the following is evidence that a test is flaky:

- only one shard failed;
- only one database driver failed while the others passed;
- it passes locally;
- it passes on a re-run;
- the failure is rare.

Every one of those is also what a **deterministic** failure looks like when it
depends on a narrow condition — the position of the clock, a slot boundary, a
request still in flight, data another spec left. Two failures in this repository
presented exactly that way and both had precise, reproducible causes: see
[time-and-timezone.md](time-and-timezone.md).

Classify with evidence, in this order:

1. **Read the trace.** `npx playwright show-trace <dir>/trace.zip`, or read the
   network entries directly — they carry `startedDateTime` and a duration per
   request, which is the only reliable way to see two requests overlapping.
2. **Read the server log** for the same window. Note the caveat below.
3. **Establish the exact application state** at the moment of failure: what the
   request returned, what the page rendered, what the database would have held.
4. **Name the condition** under which the failure is certain — a clock position,
   an ordering of two writes, a missing prerequisite.
5. **Reproduce it under that condition** where you can; where you cannot, say so
   rather than implying you did.
6. **Only then** classify it, and fix the cause.

> **Server logs record completion, not start.** An nginx access log line is
> written when the response finishes, so two requests logged a second apart may
> have overlapped substantially. A failure was misdiagnosed here for exactly this
> reason: the log showed a draft write at `:34` and a publish at `:35`, implying
> they were sequential, while the trace showed the publish starting 421 ms
> *inside* the draft's flight window. When ordering matters, take it from the
> trace.

Once the cause is a genuine synchronisation gap, fix it by naming the transition:

1. Reproduce — `npm run test:e2e -- -g "<title>" --repeat-each=5`.
2. Watch it fail — `--headed`, or step the trace to the moment before the action.
3. Name the transition you needed and did not wait for — the table in
   [locators.md](locators.md) lists the usual ones.
4. Assert that transition, then act.
5. Confirm with another `--repeat-each` loop.

`retries: 0` is deliberate: a retry that turns a red run green hides exactly the
defect you need to see. Do not add retries to settle a failure.

If a test fails because it depends on data or state another test left, the fix is
ownership, not timing.

### A green run is not proof that your fix worked

If you never saw the test fail, a passing run afterwards tells you nothing — it
may simply not reproduce on your machine. Before claiming a fix:

- get a red baseline (revert the fix, run it, watch it fail), **or**
- show from the trace or the code that the failing condition is now impossible.

If you have neither, say which one you are missing rather than reporting the fix
as verified.

## A flash message that never appeared

Laravel ages flash data on every request that **saves the session**:
`Store::save()` calls `ageFlashData()`, so a value flashed by one request
survives roughly one subsequent session-saving request and is then dropped.

That matters here because Bagisto's shop API routes are registered inside the
`web` middleware group (`ShopServiceProvider` groups `Routes/api.php` with
`['web', 'shop', …]`), so every `/api/products`, `/api/categories` and similar
call starts and saves the session.

The failure shape: a form POST redirects back with `session()->flash('error', …)`,
but background XHRs from the *previous* page — still executing server-side even
after the browser aborted them, which the access log shows as `499` — save the
session in between and consume the flash. The page renders correctly but without
the message, and the response is byte-for-byte the size of the message-less page.

The fix is to let those requests settle before the state-changing submit, not to
sleep:

```ts
await this.visit("customer/login");
await this.waitForBackgroundRequestsToSettle();
```

`BasePage.waitForBackgroundRequestsToSettle()` is the sanctioned place for this —
see the note on `networkidle` in [locators.md](locators.md). Settle the page you
are about to navigate *away* from as well, so its requests are never aborted
mid-flight.

## Debugging from a CI artifact

Each `playwright_tests` job uploads one artifact named
`<Project>-results-<db>-shard-<n>-<run_id>-<run_number>`, containing:

```
packages/Webkul/<Project>/tests/e2e-pw/playwright-report   # the HTML report + report.json
packages/Webkul/<Project>/tests/e2e-pw/test-results        # per-failure dir: error-context.md, screenshots, video, trace.zip
storage/logs/laravel.log                                   # application errors
server-logs/                                               # nginx access + error, php-fpm
```

Retention is one day, so download before it expires. The workflow:

1. **Identify the failing test** from the report — file, line, full title.
2. **Read `error-context.md`** for the error and the page snapshot at failure.
3. **Open the trace** and find the request that matters. The `.network` entries
   give `startedDateTime` and duration per request; use these, not the access
   log, whenever ordering or overlap is the question.
4. **Correlate with `server-logs/nginx-access.log`** for status codes and sizes.
   A redirect that should not have happened, or two renders of the same URL with
   different byte counts, are both strong signals.
5. **Check `storage/logs/laravel.log`** for an exception behind a 500.
6. **Convert CI timestamps to the application timezone** before reasoning about
   anything time-dependent — CI logs UTC, the app runs `APP_TIMEZONE`.
7. **Reproduce locally**, under the environment difference if you can identify
   one (a `TZ`, a database driver, a time of day).
8. **Apply the smallest correct fix**, re-run the affected spec, then the spec
   file, and confirm nothing was weakened.

A CI-only failure is usually reproducible locally once the differing condition is
named. If it is not, the condition is the finding — say which one you could not
reproduce rather than calling the test flaky.

## Where configuration comes from

`utils/env.ts` in each package loads the application `.env` through `dotenv` and
delegates to the shared `readEnv()` in `tests/e2e-pw/helpers/env.ts`, which reads
and validates every value once:

| Field | Source | Default |
|---|---|---|
| `baseUrl` | `APP_URL`, falling back to `BASE_URL` | none — throws with a directed message |
| `adminEmail` | `BAGISTO_ADMIN_EMAIL` | `admin@example.com` |
| `adminPassword` | `BAGISTO_ADMIN_PASSWORD` | `admin123` |
| `timezone` | `APP_TIMEZONE` | `UTC` |
| `headed` | `HEADED` (`1`/`true`/`yes`/`on`) | `false` |

Set no URL and it fails immediately rather than navigating to `"undefined/"`.
Never read `process.env` from a config, spec, page object or fixture — and note
that `timezone` is consumed twice in each config, as `process.env.TZ` and as
`use.timezoneId` ([time-and-timezone.md](time-and-timezone.md)).

`utils/paths.ts` wraps the shared `createE2ePaths()` and owns every path,
including `DATA_PATH`, `ADMIN_AUTH_STATE_PATH` and `ensureStateDir()`. It finds
the application by searching upward for `artisan` rather than counting `../`, and
prefers a suite-local `tests/e2e-pw/.env` when one exists — so the folder keeps
working if it moves. Never hardcode a parent-walk, and never import a path from
`playwright.config.ts`.

CI sets `BASE_URL=http://localhost` for the Admin and Shop jobs; the installer
job rewrites `APP_URL` in `.env` instead.

## Environment faults mistaken for bugs

- **`APP_URL` is the base URL.** If every test 404s or hits the wrong host, check
  it first — including that it points at the app you actually rebuilt.
- **The app must be running and seeded.** CI runs `bagisto:install`, seeds the
  product table and runs `indexer:index --mode=full` before the first spec.
- **The Installer suite is the exception — it needs an *uninstalled* app.** It
  drives the guided web installer, so run it after `php artisan key:generate`
  and *before* `bagisto:install`; against an installed app the spec skips. The
  database it installs into comes from the `INSTALLER_DB_*` environment
  variables, defaulting to MySQL on `127.0.0.1:3306`. Its two specs are tagged
  `@en` and `@ar`, so select one with `--grep "@en"`.
- **Browsers must be installed where the tests run** — `npm run install:browsers`
  in the package. In a containerised workspace, decide deliberately whether the
  run happens on the host or in the container, and install the browsers there.
- **The admin auth cache can go stale.** `.state/admin-auth.json` is reused
  across runs; if every admin spec starts on the login screen after credentials
  changed, delete it and let the fixture log in again.
- **A whole suite timing out** usually means the app is down or the base URL is
  wrong, not that the timeouts are too short. Shop's 240 s per test and 2 h
  global cap are already generous; raising them hides the real fault.
- **CI runs Admin and Shop across 10 shards each, against MySQL, MariaDB and
  PostgreSQL, gated by an installer job.** A shard splits by file, and every job
  runs `workers: 1` with `fullyParallel: false` — so when you are debugging,
  assume sequential execution and do not reach for parallelism as an explanation.
  A CI-only failure is usually reproducible locally by running that spec file
  once the differing condition is named; if it is not, look for a dependency on
  another file's state, a database-driver difference, or the clock — in that
  order.

## A test that passes when it should not

The most expensive failure mode is a test that never guarded anything.

Two ways a test is born dead in this codebase:

- **The seeded data does not reproduce the bug.** A reorder test cannot detect a
  gapped-`sort_order` bug when the seeder writes a contiguous `1..N`, so it
  passes with and without the fix. If the condition cannot be created through
  the UI, cover it in Pest, where the fixture can be set up directly — and say
  so in the test name rather than implying a guarantee the test does not give.
- **The assertion is weaker than the claim.** Asserting that a badge cleared
  does not prove the value reverted; asserting a toast does not prove a save.

The remedy is the falsification step: break the behaviour by hand, confirm the
test fails for the expected reason, restore it, confirm it passes. See
[assertions.md](assertions.md) and [test-design.md](test-design.md).
