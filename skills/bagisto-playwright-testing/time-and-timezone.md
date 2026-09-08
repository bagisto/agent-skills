# Time, timezone and booking availability

## Contents

- [The timezone contract](#the-timezone-contract)
- [When to read this file](#when-to-read-this-file)
- [How Bagisto decides a slot is available](#how-bagisto-decides-a-slot-is-available)
- [The two failures this produced](#the-two-failures-this-produced)
- [Rules for writing a time-dependent test](#rules-for-writing-a-time-dependent-test)
- [Diagnosing a clock-related failure](#diagnosing-a-clock-related-failure)

## The timezone contract

Three clocks are in play, and all three must agree:

| Clock | Set by |
|---|---|
| The application | `APP_TIMEZONE` — `Asia/Kolkata` in `.env.example`, copied verbatim by CI |
| Node (the test process) | `process.env.TZ = env.timezone` at the top of each `playwright.config.ts` |
| The browser | `use: { timezoneId: env.timezone }` in each `playwright.config.ts` |

`env.timezone` comes from the shared `readEnv()`, which reads `APP_TIMEZONE` and
falls back to `UTC`. All three suites set both lines; keep it that way if you
touch a config.

The failure this prevents: a CI runner is UTC, Laravel is `Asia/Kolkata`, and
between 18:30 and 24:00 UTC the two disagree about what day it is. A test that
computes "today" in Node then asks the application for that date gets an empty
availability response and fails — only in CI, and only during part of the day.

## When to read this file

Before touching, and before diagnosing a failure in, any test that involves:

current date · current time · "today" · "tomorrow" · booking slots · rental
slots · availability windows · weekly availability · same-slot-all-days ·
calendars and date pickers · expiry · anything computing a date in the spec.

For these, timezone and clock position are the **first** hypothesis, not the
last. Do not add a wait, relax an assertion or raise a timeout in response to one
of these failures.

## How Bagisto decides a slot is available

Two rules in `packages/Webkul/BookingProduct/src/Helpers/` govern almost every
booking test, and they interact:

**1. A slot is only offered while its start is still in the future.**
`Booking.php:638` filters the generated list with:

```php
if ($qty && Carbon::now() <= $from) {
```

(`Booking.php:568` applies the same test to the `default` type.) The instant
`now` passes a slot's start, that slot disappears from the list.

**2. The checkout page re-derives the same list.** `isSlotExpired()` —
`RentalSlot.php:70`, and `Booking.php:229` for the other types — calls
`getSlotsByDate()` again and requires the cart item's stored `from`/`to` to still
be present. If they are not, `Cart::hasError()` is true and
`OnepageController.php:49` redirects the customer back to `/checkout/cart`.

So a slot that was valid when it went into the cart can be rejected at checkout,
seconds later, with no user error message — just a redirect.

**3. The date picker's disabled dates are a render-time snapshot.**
`getDisabledDates()` (`Booking.php:309`, surfaced at `:298`) greys out *today*
only when today's slot list is already empty **at the moment the product page was
rendered**. A page rendered one second before a slot's start shows today as
selectable; the same page a second later does not.

## The two failures this produced

Both were initially reported as flaky. Neither was.

**Timezone skew.** Booking tests using `availableEveryWeek` + `sameSlotAllDays`
failed across six Shop shards. The run happened at 18:50–19:28 UTC, which is
00:20–00:58 next-day in `Asia/Kolkata`, so the browser and the application
disagreed about the date. Evidence: `/booking-slots/6?date=<node-today>` returned
an empty list while the application's own "today" returned a full one. Fixed by
pinning `TZ` and `timezoneId` — not by touching a test.

**A slot that expired mid-test.** One MariaDB shard failed while MySQL and
PostgreSQL passed. The trace showed the selected slot was `10:20 AM - 11:20 AM`;
the server log showed add-to-cart succeeding at 10:19:59 app-time and
`GET /checkout/onepage` returning 302 at 10:20:03. The test had selected the
earliest offered slot, which began four seconds later, and rule 2 above rejected
it at checkout. The window in which this can happen is roughly the last minute
before a hard-coded slot time — which is why it looked random and why the other
drivers, running a minute apart, passed.

The fix was in the test's date selection, not in a wait: pick a bookable date
**after today**, so the chosen slot cannot start during the test. The intent of
the test — book an available slot and check out — is unchanged, and no assertion
was touched.

## Rules for writing a time-dependent test

- **Never book the soonest thing on offer.** The first enabled date and the first
  slot in the dropdown are the two most likely to expire while the test runs.
  Choose one with deterministic headroom.
- **Prefer a date that is not today** when the business rule does not require
  today. `BookingProductCheckout.selectFirstAvailableDate()` skips today
  deliberately, using a calendar-scoped locator that excludes `.today`.
- **Do not solve slot expiry with a delay.** A `waitForTimeout` makes the race
  more likely, not less, and hides it on faster machines.
- **Do not compute a date in the spec and assume the server agrees** unless the
  timezone contract above is intact. If you must, derive it from the same zone.
- **A fixture with a hard-coded wall-clock time carries a daily failure window.**
  If a fixture writes a slot at `10:20`, every test using it is fragile for the
  minute before 10:20 application-time. Prefer a window with headroom, or select
  a later date.
- **Keep the assertion.** If a test asserts the booked hour, changing the date
  keeps that assertion true; weakening it to "any hour" does not.

## Diagnosing a clock-related failure

1. Establish the application's clock: `APP_TIMEZONE`, and the wall-clock time of
   the run in that zone. CI timestamps are UTC.
2. Establish Node's and the browser's zone from the config.
3. From the trace, read the exact slot or date string the test chose, and the
   request that fetched it (`/booking-slots/<id>?date=…`).
4. Compare that date against the application's "today" at that moment.
5. Compare the slot's start against the timestamps of add-to-cart and checkout in
   the server log.
6. Only once those four line up should you look for a different cause.

[troubleshooting.md](troubleshooting.md) has the general CI-artifact workflow and
the caveat about server-log timestamps recording completion rather than start.
