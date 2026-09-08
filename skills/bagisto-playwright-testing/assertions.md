# Assertions

## Contents

- [The question to ask](#the-question-to-ask)
- [Weak assertions](#weak-assertions)
- [What to assert, by outcome](#what-to-assert-by-outcome)
- [Negative tests assert two things](#negative-tests-assert-two-things)
- [Persistence](#persistence)
- [Counts](#counts)
- [Do not assert implementation detail](#do-not-assert-implementation-detail)
- [Prove the test can fail](#prove-the-test-can-fail)

## The question to ask

For every `expect` you write: **what requirement does this prove, and would it
fail if that requirement broke?**

If the honest answer is "it proves the request did not error", the assertion is
not carrying the test. Something else has to.

Run the question against the test as a whole: *if the feature were deleted from
the application, would this test go red?*

| Testing | Not enough | Proves it |
|---|---|---|
| Product creation | the form submitted | the product exists in the grid with the entered sku, price and status |
| Deletion | a success toast | a search for the record returns nothing |
| Validation | an error message appeared | the error names the field, **and** the record was not created |
| Permission | the menu entry is hidden | the gated route itself refuses the request |
| Configuration | "Configuration saved successfully" | the setting reads back changed, and the behaviour it controls changed |
| A discount rule | the coupon field accepted input | the grand total the customer sees is the discounted one |

The left column is not forbidden — it is what a test asserts *in addition*. It
just cannot be the whole test.

## Weak assertions

These are not wrong in themselves — they are wrong when they are the *only*
thing a test asserts:

| Assertion | What it actually proves | Why it is not enough |
|---|---|---|
| the page loaded | routing works | says nothing about the feature |
| a button is visible | the template rendered | the button may do nothing |
| a success toast appeared | the request completed and the app flashed a message | the value may not have been stored, or stored wrong |
| the URL changed | a redirect happened | the same redirect happens on many outcomes |
| `getByText(x).first()` is visible | *something* on the page says `x` | may be the drawer, the debug bar, or another record |

The pattern to watch for is the lone flash-message assertion: a configuration
test that fills fields and asserts only "Configuration saved successfully" would
still pass if the form silently dropped every field.

The fix is not to delete the toast assertion. It is to pair it with a read-back,
which is what the configuration specs now do — `checkout.spec.ts` applies a
change and then calls `expectSettings(changed)`, which reopens the screen and
compares every value:

```ts
await expect(this.page.getByText("Configuration saved successfully")).toBeVisible();

await this.open();
await expect(this.productsPerPageInput).toHaveValue("24");
```

## What to assert, by outcome

| The test claims | Assert |
|---|---|
| **Creation** | The named record appears where the user would look, carrying the data that was entered |
| **Validation** | The specific error message is shown against the field, **and** the record was not created |
| **Update** | The new value is displayed, and still displayed after a reload |
| **Deletion** | The record is gone from the list — `toHaveCount(0)` on the row locator — and a search for it finds nothing |
| **Cancel** | Nothing was created, and the screen returned where it should |
| **Permission** | The user is refused: the denial the app actually shows, plus the absence of the control or menu entry |
| **Visibility** | The element is absent for the condition that should hide it, and present for the one that should show it |
| **State transition** | The new state is displayed, and the transitions that should be refused are refused |
| **Empty state** | The empty-state text, not merely a row count of zero |
| **Business rule** | The number, total, status or availability the rule is supposed to produce |

For a discount rule, the assertion is the grand total the customer sees — not
that a coupon field accepted input. `RuleApplyPage.expectGrandTotal(expected)`
is the right shape: compute what the rule should produce, then assert the
screen shows it.

## Negative tests assert two things

A negative test that only checks for an error message has proved half of what it
claims. The other half is that nothing happened.

```ts
test("should reject a product whose sku already exists", async ({ adminPage }) => {
    const productPage = new ProductCreatePage(adminPage);
    const sku = `SKU-${uniqueStamp()}`;

    await productPage.createProduct({ type: "simple", sku, ...rest });
    await productPage.attemptCreateProduct({ type: "simple", sku, ...rest });

    await productPage.expectFieldError("sku", "The sku has already been taken.");
    await productPage.expectSkuOccursOnce(sku);
});
```

The second assertion is the one that catches a controller that shows an error
and saves anyway, or one that saves a partial record before validating.

Where "nothing happened" is meaningful, assert it:

- a rejected create leaves the grid count for that name at zero;
- a cancelled edit leaves the old value;
- a refused state transition leaves the old status;
- a denied action leaves no audit entry the user can see.

Get the exact message text from the lang file rather than from memory — see
[investigation.md](investigation.md).

## Persistence

An optimistic UI update is not persistence. When the claim is that something was
stored, reload and assert again:

```ts
await this.open();
await expect(this.field("Title")).toHaveValue(title);
```

Apply it to every update, every configuration change, and every state transition
whose whole point is that it survives. The appearance-section specs do this by
reopening the section after publishing and re-reading the field, rather than
trusting the editor's own state.

## Counts

- **Never assert a global count.** `meta.total`, "3 sections", "the grid has 12
  rows" — all break the moment another spec adds a record, and they were never
  proving anything about your record anyway.
- **A scoped count is fine and often the strongest assertion available.**
  `expect(this.row(name)).toHaveCount(0)` after a delete, or `toHaveCount(1)`
  after a create, is precise and immune to leftover data.
- **Search first, then count.** Filtering the grid by a unique value and
  asserting one row is the reliable form of "exactly one of these exists".

## Do not assert implementation detail

A test should survive a reasonable redesign while still proving the requirement.
Avoid asserting on:

- Vue component internals or wrapper structure;
- CSS classes as a proxy for state, where a user-visible signal exists (assert
  the disabled control cannot be used, not that it carries `.opacity-50`);
- DOM nesting;
- database columns, in place of what the screen shows;
- internal method or event names.

The exception is where the class *is* the only signal the application gives —
`span.line-through` for a switched-off section, `span.icon-dot` for an unsaved
change. Then keep it in a named private locator (`unsavedMarker(name)`,
`switchedOffName(name)`) so the assertion in the test still reads as behaviour.

## Prove the test can fail

Before calling a test done, make it fail on purpose. Both moves below are
*temporary* edits you undo immediately — the opposite of weakening an assertion
to get a red run green, which [troubleshooting.md](troubleshooting.md) rules out.
The cheapest version costs a minute:

- temporarily change the expected value in the assertion, run, and confirm the
  failure message names the right thing — then put it back;
- for a regression test, put the bug back in the working tree by hand, run, and
  confirm it fails *for the reason you expect* — then edit the fix back and
  confirm it passes.

A test that has never been red is an untested test. This is the step that
catches assertions scoped to the wrong element, assertions that match seeded
data, and assertions that were already true before the action ran.
