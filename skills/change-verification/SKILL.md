---
name: change-verification
description: Use when a Bagisto change is about to be called done, or when asked to run the verification gates — code style, tests, end-to-end tests and translation completeness. Trigger phrases include "verify", "is this done", "run the gates", "pint", "pest", "playwright", "translations check", "ready to commit".
license: MIT
---

# Change Verification

The completion gate for Bagisto. A change is not done until every gate its diff
reaches has passed and been reported. These four gates are the five test
workflows in `.github/workflows/` — E2E runs as two, Admin and Shop — so a
change that clears them locally is a change that clears the pipeline.

## The four gates

| # | Gate | Command | Applies when |
|---|---|---|---|
| 1 | Style | `vendor/bin/pint --test` | any `.php` changed |
| 2 | Tests | `vendor/bin/pest` | any `.php` changed |
| 3 | E2E | `npx playwright test --config=tests/e2e-pw/playwright.config.ts` | any view, JS, CSS or route changed |
| 4 | Translations | `php artisan bagisto:translations:check` | any `Resources/lang/**` changed |

Run them in that order — style is seconds, E2E is minutes, and a Pint failure
makes the rest moot.

### 1. Style

```bash
vendor/bin/pint          # fix
vendor/bin/pint --test   # then confirm: CI runs this form
```

Pint does not format `.blade.php`. Blade style is applied by hand — see the
`coding-standards` skill.

### 2. Tests

```bash
vendor/bin/pest                                        # everything
vendor/bin/pest packages/Webkul/Admin/tests/Feature    # one directory
vendor/bin/pest --testsuite="Admin Feature Test"       # one suite
```

Suites live in `phpunit.xml`, one per package that has tests. A package with no
`tests/` directory has no suite; adding a `<testsuite>` for a path that does not
exist makes PHPUnit error.

### 3. End-to-end

Admin and Shop are separate Playwright projects, each run from its own package
directory. See the `playwright-testing` skill before writing or debugging one.

```bash
cd packages/Webkul/Admin   # or packages/Webkul/Shop
npx playwright test --config=tests/e2e-pw/playwright.config.ts
```

CI runs each project across **10 shards**. Locally, run the spec files your
change touches rather than the whole suite.

### 4. Translations

```bash
php artisan bagisto:translations:check
```

A key must exist in all 22 locales under `Resources/lang/`. One missing locale
fails the workflow.

## The security checkpoint

Not a gate — there is no command that returns "secure". It is a question the
diff has to answer before the work is called done:

> Does this change touch authorization, rendered output, user input, uploads,
> raw SQL, secrets or payments?

If yes, load **`coding-standards`** and work its checklist for the surfaces the
diff actually touches. If no, say so — "no authorization, output or input
surfaces touched" — the same way a skipped Playwright run is stated rather than
left silent.

The gates above cannot answer this. Pint has no opinion on an unscoped query,
and a test suite passes just as happily with an IDOR in it.

## Establish the baseline before you blame your change

Bagisto's suites do not start green on every checkout. Some tests assert
absolute counts (`meta.total`) that a seeded install does not satisfy, and the
suites share one database with no rollback between runs, so counts drift.

**Never report a failure count as a regression without comparing.** Revert your
change, run the same command, and diff the failing test **names** — not the
counts, which move on their own:

```bash
vendor/bin/pest <path> 2>&1 | grep -E "^  ⨯" | sed 's/ *[0-9.]*s *$//' | sort > /tmp/with.txt
# revert the change, re-run into /tmp/without.txt
comm -23 /tmp/with.txt /tmp/without.txt   # empty means you introduced nothing
```

An empty diff is the evidence that the gate passed. A count that went 3 → 4 is
not evidence of anything.

## Rules

- **A gate you did not run is a gate that failed.** Report each one explicitly,
  including the ones the diff did not reach: "no view or JS changes — Playwright
  skipped" is a result; silence is not.
- **Fix the cause, never the check.** Do not delete or skip a test, loosen an
  assertion, or add a Pint exclusion to reach green.
- **A pre-existing failure you did not cause is still reported**, with the
  evidence that it pre-dates the change.
- **Prove a fix by breaking it.** When a change fixes a bug, revert the fix and
  watch the new test fail. A test that passes both ways guards nothing — it is
  the most common way a regression test is born dead.
- **Rebuild assets after any frontend change**, then re-run the E2E gate:
  `cd packages/Webkul/<Admin|Shop> && npm run build`.
- **Do not commit or stage** as part of verification unless asked.

## Common mistakes

- **Reporting counts instead of names.** Two runs of the same suite can differ
  without any code change; only the name diff is meaningful.
- **Running Pint over the whole repo and reporting someone else's debt.** Scope
  it: `vendor/bin/pint --test <changed paths>`.
- **Claiming the translation gate passed after editing only `en`.** The checker
  compares all 22 locales; editing one and running nothing is the usual path to
  a red pipeline.
- **Skipping E2E because "it is only a Blade change".** Views are exactly what
  the E2E gate covers.
