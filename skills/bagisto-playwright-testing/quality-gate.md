# Final quality gate

Run this before calling any E2E work done. It is a checklist, not a formality —
most of these lines name a defect that is present in the suite today.

Mark an item N/A when the scenario genuinely does not apply, and be able to say
why. "N/A" is a legitimate answer; skipping the question is not.

## Prove it runs

Three runs, in this order. Each catches a different defect:

```bash
npm run typecheck                                    # first — a type error is cheaper than a run
npm run test:e2e -- <path/to/spec.ts> -g "<title>"   # alone — catches order dependence
npm run test:e2e -- <path/to/spec.ts>                # whole file — catches shared data
npm run test:e2e -- <path/to/spec.ts>                # again, same database — catches self-consuming data
```

The third is the one people skip and the one that matters most here: a test that
passes on a clean database and fails on the second run has hardcoded a value, or
left a record it needs absent, or asserted a count.

For a regression test, add the falsification run: break the behaviour by hand,
confirm the test fails for the expected reason, restore the fix, confirm it
passes.

## Investigation

- [ ] Application implementation inspected — routes, controller, model, DataGrid.
- [ ] Validation and business rules inspected, including rules the UI never shows.
- [ ] Exact UI strings taken from the lang file, not from memory.
- [ ] Impact surface mapped, and the source of truth for the change identified.
- [ ] Existing related specs inspected, and what each actually proves is known.
- [ ] Existing page objects inspected.
- [ ] Existing fixtures, utils and helpers inspected.
- [ ] User workflows identified — entry point, observable outcome, failure modes.
- [ ] Prerequisites identified: which configuration and data must exist.

## Coverage design

- [ ] Each scenario written as state A → action → state B.
- [ ] Refused / invalid transitions considered, not only the ones that succeed.
- [ ] Positive scenarios considered.
- [ ] Negative scenarios considered.
- [ ] Validation considered.
- [ ] Boundary and edge cases considered where applicable.
- [ ] ACL / permission behaviour considered where applicable.
- [ ] Persistence-after-reload considered where applicable.
- [ ] Side effects considered; the requirement-bearing ones are asserted.
- [ ] Regression behaviour considered where applicable.
- [ ] Admin-vs-Shop responsibility decided: the test sits where its outcome is
      visible, and covers both sides when both change.
- [ ] E2E vs Pest decided per scenario, and backend-only logic left to Pest.
- [ ] Duplicate coverage checked — no second test proving an existing guarantee.
- [ ] Same-behaviour-different-input cases parameterised rather than copied.
- [ ] No test exists only to satisfy a category on the matrix.
- [ ] The stop condition is met — no low-value test added to raise the count.

## Implementation

- [ ] Existing infrastructure reused; anything new is justified by a failed search.
- [ ] Page-object abstraction is at the domain level — no whole-scenario methods,
      no click-by-click micro-methods.
- [ ] The spec contains no selector; the page object owns every locator.
- [ ] Locators are stable and scoped to the row, form or container they belong to.
- [ ] No positional selector identifies a business entity; `.first()` is not used
      to silence strict mode.
- [ ] No `waitForTimeout` and no named delay constant. No open-coded
      `networkidle` — `BasePage.waitForBackgroundRequestsToSettle()` is the only
      sanctioned use, and only for the Laravel flash case it exists for.
- [ ] Every wait names the application state transition it waits for.
- [ ] Any locator that depends on a third-party widget was verified against the
      version **that package** resolves, not a sibling suite's.
- [ ] A test that depends on the clock was checked against the timezone contract,
      and does not book the soonest available date or slot.
- [ ] Test data is generated in `beforeEach`, unique where the database requires
      it, deterministic where the value is the thing under test.
- [ ] The test creates the data it uses, and uses the data it creates.
- [ ] Prerequisite state is established by the test, not assumed from another
      spec, another suite, the seeder, or file order.
- [ ] Configuration is *set* idempotently, never toggled blind.
- [ ] Any global setting the test changes is read first and restored, in a
      `finally`.
- [ ] No `describe.serial` or numeric filename prefix added to encode ordering.
- [ ] Cleanup targets only test-owned records, by name, and one failing step does
      not skip the next.
- [ ] No API or database bypass of the behaviour under test.
- [ ] No comments anywhere under `tests/e2e-pw/`.
- [ ] Naming follows the suite — lower-kebab files, `<Feature>Page.ts` matching
      its class, lower-case describe and test titles.
- [ ] Test titles state the behavioural guarantee.

## Verification

- [ ] Assertions prove the actual requirement, not that a request succeeded.
- [ ] A success message is never the only assertion.
- [ ] If the feature were deleted, every new test would go red.
- [ ] Negative tests verify the absence of the unintended side effect.
- [ ] No assertion depends on a global count or a list position.
- [ ] No assertion depends on implementation detail that a redesign would change.
- [ ] Every failure seen during the work was classified before anything changed,
      and no assertion was weakened to get green.
- [ ] No failure was called flaky without trace, log and timestamp evidence.
- [ ] Any fix for an intermittent failure has either a red baseline or an
      argument from the code that the failing condition is now impossible — and
      the summary says which.
- [ ] Each new test has been made to fail on purpose, and failed for the right
      reason.
- [ ] Regression tests have been validated against the regression itself.
- [ ] The spec passes alone, in its file, and on a second run against the same
      database.

## Then hand off

**REQUIRED SUB-SKILL:** Use `bagisto-change-verification` before calling the
change done — it owns the repository-wide gates. If the change touched
application code as well as tests, `bagisto-coding-standards` and
`bagisto-code-review` apply to that half.

State plainly in your summary:

- which tests were added, and the guarantee each one carries;
- which were strengthened rather than added, and what they were missing;
- anything you decided belongs in Pest instead, and why;
- any scenario you could not cover through the browser;
- for a regression test, that you saw it fail against the bug.
