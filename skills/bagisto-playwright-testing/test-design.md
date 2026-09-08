# Designing the coverage

## Contents

- [Model the state transition first](#model-the-state-transition-first)
- [The scenario matrix](#the-scenario-matrix)
- [The coverage matrix](#the-coverage-matrix)
- [Collapsing the matrix](#collapsing-the-matrix)
- [Side effects](#side-effects)
- [Parameterising a behaviour](#parameterising-a-behaviour)
- [E2E or Pest](#e2e-or-pest)
- [Regression tests](#regression-tests)
- [When to stop](#when-to-stop)
- [Before you implement](#before-you-implement)

## Model the state transition first

A test is not "does the button work". It is a claim that an action moves the
system from one observable state to another. Write each candidate as:

```
STATE A  →  ACTION  →  STATE B
```

```
guest checkout disabled  → enable it        → a guest can reach payment
section draft            → publish          → change is live and the marker clears
product out of stock     → set inventory    → product is buyable on the storefront
empty cart               → add product      → cart shows the product and a subtotal
cart with items          → place order      → order exists and appears in order history
order cancelled          → attempt to ship  → refused, status unchanged
```

Three things fall out of writing it this way, and all three are things weak tests
miss:

- **State A is the setup**, and it is the test's responsibility to establish it.
  Not the seeder's, and not a previous spec's — see
  [admin-and-shop.md](admin-and-shop.md).
- **State B is the assertion**, and it is a state, not an event. "A toast
  appeared" is the event; "the product is buyable" is the state.
- **The refused transitions are scenarios too.** For every transition that should
  work, ask which neighbouring one should be blocked, and whether the block is
  worth proving. A cancelled order that can still be shipped is a real bug that
  no happy-path test will ever catch.

For a transition whose whole point is that it persists, State B has to be
re-read after a reload — see [assertions.md](assertions.md).

## The scenario matrix

For each workflow from [investigation.md](investigation.md), walk this list and
write down which entries are *genuinely different behaviour* in this feature.
The list is a prompt for thinking. It is not a quota, and an entry that does not
apply gets no test.

| Category | Ask |
|---|---|
| Happy path | What is the user actually trying to do? |
| Alternative valid flows | Is there a second legitimate route to the same outcome that runs different code? |
| Required-field validation | Which fields does the request refuse to accept as empty? |
| Invalid input | What does the application reject, and how does it say so? |
| Boundary values | Where are the numeric, length or date limits? |
| Empty values | Does `''` become `null`, a default, or an error? |
| Duplicate values | Which fields are unique, and what does the second attempt show? |
| Cancel | Does backing out leave nothing behind? |
| Edit / update | Does the changed value persist and display? |
| Delete | Is the record gone from the place the user would look? |
| State transitions | Which moves are allowed, and which are refused? |
| Persistence after reload | Does the value survive a fresh page load, or only the optimistic UI? |
| Permission / ACL | What does a role without this permission see and reach? |
| Visibility | What appears or disappears depending on type, channel, locale or config? |
| Error states | What does the user see when the server refuses? |
| Empty states | What does the screen say with no records? |
| Business rules | The rule you found in the repository or `AbstractType` that no field shows |
| Combinations | Which pairs interact — a rule plus a product type, a config plus a channel? |
| Time dependence | Does the outcome depend on the clock — availability, a slot, an expiry, "today"? If so, [time-and-timezone.md](time-and-timezone.md) before you design the data |
| Regression | What broke before, and how would it look if it broke again? |

## The coverage matrix

For a feature with more than one actor or more than one precondition, the
category list is not enough — the interesting bugs live in the combination. Lay
the candidates out in a row per scenario:

| Actor | Permission | Initial state | Input | Action | Business rule | Expected outcome | Side effect | Persists | Final state |
|---|---|---|---|---|---|---|---|---|---|
| guest | — | guest checkout on | valid address | place order | guests may order | confirmation shown | order created | yes | order visible by number |
| guest | — | guest checkout off | — | reach checkout | guests must sign in | sign-in required | none | n/a | still a guest |
| admin | `catalog.products` | product exists | duplicate sku | save | sku is unique | field error shown | none | n/a | still one product |
| admin | no `catalog.products` | product exists | — | open product edit | route is gated | refused | none | n/a | product unchanged |

**Do not build the Cartesian product.** Four actors × five states × six inputs is
120 rows and perhaps six real behaviours. Fill in only the rows that differ in
the *Business rule* or *Expected outcome* column, and among those prioritise:

1. high business risk — money, orders, stock, access;
2. permission boundaries, where the failure is a security one;
3. state transitions that are refused, not just the ones that succeed;
4. anything a known regression touched;
5. customer-visible impact over admin-internal detail;
6. genuine edge cases, once the above are covered.

Rows that share every column except *Input* are one parameterised test. Rows
whose *Expected outcome* is identical are one test.

## Collapsing the matrix

Then cut it down. The goal is **meaningful behavioural coverage**, never
maximum test count.

- **Same behaviour, different data → one parameterised test.** Eight coupon
  operators exercising one code path is a table, not eight specs.
- **Same assertion, different entry point → one test**, unless the two paths run
  different validation or defaults. Verify that in the controller before
  deciding.
- **Different behaviour → separate tests**, even when the setup is identical. A
  duplicate SKU rejection and a missing-price rejection are two guarantees; a
  test that only proves "some error appeared" proves neither.
- **A scenario the UI cannot reach is not an E2E scenario.** If the state cannot
  be produced through the browser, the test belongs in Pest, where the fixture
  can be built directly.
- **Cost matters.** A Shop checkout spec runs for minutes. Fold an extra
  assertion into an existing flow rather than paying for a second checkout to
  assert one more field — as long as the folded assertion still names its own
  guarantee and its failure is unambiguous.

The output is a short list: *these N tests, each proving this one thing.* If two
entries would fail for the same reason, they are one entry.

## Side effects

An action in Bagisto rarely changes one thing. Before settling the assertions,
list what else moves — then assert the ones that are part of the requirement,
business-critical, customer-visible or historically fragile, and let the rest go.

| Action | Also changes |
|---|---|
| Create a product | The product grid, its status and visibility, category association, inventory, whether it is buyable on the storefront |
| Change a configuration value | The admin screen, the storefront, and every later spec in the run |
| Place an order | Cart emptied, inventory decremented, order grid, order status, customer order history, invoice state |
| Delete a record | The grid, anything referencing it, and any storefront listing that included it |
| Publish a theme section | The staged-change marker, and the storefront home page |

The decision rule: **assert a side effect when its absence would mean the feature
is broken for a user.** An order that is placed but leaves the cart full is
broken; an order that does not update an internal counter probably is not — and
if it is, that counter is a Pest test.

Mechanically asserting every side effect makes the test slow, brittle, and vague
about what it guarantees. Asserting none of them is how "the toast appeared" tests
happen.

## Parameterising a behaviour

The suite already has the form —
`Shop/tests/e2e-pw/tests/promotion/cart-rules/product-attributes/sku.spec.ts`:

```ts
const cases = [
    { operator: "==", type: "fixed", value: () => generatedSku },
    { operator: "!=", type: "fixed", value: () => "sku-123" },
];

test.describe("cart rules", () => {
    for (const { operator, type, value } of cases) {
        test(`should apply coupon when sku condition is -> ${operator} (${type})`, async ({ adminPage }) => {
            await createRuleAndVerifyCoupon({ page: adminPage, operator, value: value(), couponType: type });
        });
    }
});
```

That spec now takes `adminPage` and generates its data in `beforeEach`, so the
whole shape is safe to copy.

Three rules for this form:

- **Each case gets its own `test()`**, so a single failing operator names itself
  in the report. Never loop assertions inside one test.
- **Values that depend on per-test data are thunks.** The table is built at
  import time, when `generatedSku` is still `undefined`; `value: () => sku` and
  `value()` at the call site is why it works. See [test-data.md](test-data.md).
- **The title must vary by case** and describe the behaviour, not the index.

Parameterise only where the *behaviour* is one thing. Two rows that fail for
different reasons want two tests.

## E2E or Pest

Playwright is expensive, serial, and runs against a database that never rolls
back. Spend it where the browser is the point.

| Use Playwright when | Use Pest when |
|---|---|
| The user workflow across screens is the thing being guaranteed | The behaviour is a calculation, a query or a service method |
| Frontend validation, a Vue component's state, or a drawer's behaviour matters | Server-side validation rules are the whole point and the UI just forwards them |
| Navigation, redirects, visibility or ACL as *experienced* matter | The precondition cannot be produced through the UI |
| The rendered, user-visible outcome is the requirement | You need many input permutations cheaply |
| The bug being guarded was a frontend or integration bug | The bug was in a repository, model, or type class |

Some behaviour deserves both, at different depths: Pest proves every branch of a
discount calculation; one Playwright test proves the discounted total reaches
the checkout screen. That is a good split. Twelve Playwright tests over the same
calculation is not.

**Do not force backend-only logic through a browser.** An import that validates
rows, an indexer that rebuilds a flat table, a price rule that resolves across
channels — these are Pest tests. If you find yourself driving the UI purely as a
way to reach a service method, stop and write the Pest test instead. The
`bagisto-pest-testing` skill covers that side.

When a scenario is real but cannot be proven in the browser, say so where it
will be read — in the Pest test's name, or in your summary — rather than
shipping a Playwright test whose name implies a guarantee it does not give.

## Regression tests

A regression test that cannot detect the regression is worse than no test: it
occupies the slot where a real guard would have gone.

Design it against the bug, not against the fix:

1. **Name the observable symptom.** Not "the controller now passes the channel"
   but "the price shown on the product page was the default channel's".
2. **Reproduce the precondition through the UI.** If the bug only appears with a
   gapped `sort_order`, and the UI cannot create a gap, the Playwright test
   cannot see the bug — cover it in Pest.
3. **Assert the symptom**, not a proxy for it. A cleared badge is not a reverted
   value.
4. **Falsify it.** Put the bug back in the working tree by hand — invert the
   fixed line, restore the old condition — run the spec, and confirm it fails
   *for the reason you expect*, not because a locator went missing. Then restore
   the fix by editing it back and confirm the spec passes.

Step 4 is not optional and it is not satisfied by the test being green. A test
that has never been red has never been tested.

Two ways a regression test is born dead in this codebase:

- **The seeded data does not reproduce the bug.** The seeder writes values that
  do not hit the broken path, so the test passes with and without the fix.
- **The assertion is weaker than the claim.** It proves that a request
  succeeded, when the bug was in what the request stored.

## When to stop

Adding tests has diminishing returns, and past a point it has negative returns —
every extra spec is maintenance, run time, and another chance to leave data
behind. Stop when all of these are true:

- the important workflows are covered end to end;
- the meaningful positive scenarios are covered;
- the validation and refusal behaviour that matters is covered;
- the business rules you found in the code are covered or consciously deferred
  to Pest;
- the important state transitions, including refused ones, are covered;
- permission behaviour is covered where the feature is gated;
- known regressions have a test that has been shown to catch them;
- duplicate coverage has been reviewed and folded in;
- every test is independent, owns its data, and restores global state;
- locators are stable and scoped, synchronisation is deterministic;
- assertions prove the requirement;
- the suite passes against the real application, twice.

The next test after that point should be justified by a specific risk you can
name, not by the shape of a checklist. **Forty near-identical specs is not better
coverage than four** — `Shop/tests/promotion/` is what that looks like once it
has happened.

## Before you implement

You should now have, written down:

- the tests you are going to add, one line each, naming the guarantee;
- for each, whether it is E2E or Pest, and why;
- which existing test you are strengthening rather than duplicating;
- the data each test creates, and what cleans it up;
- for a regression test, how you will make it fail.

That list is what you implement. Go to [authoring.md](authoring.md).
