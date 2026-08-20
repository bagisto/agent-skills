# Security

Bagisto is a storefront handling money, addresses and customer accounts, with an
admin panel behind role-based permissions. Most of its defences are already in
place — this skill is about knowing **which ones**, so a change neither
re-invents them nor steps outside them.

Authorization — routes, permissions, guards, and one user's access to another's
data — is in [security-authorization.md](security-authorization.md).

## When this skill is obligatory

Load it when the diff touches any of these. Nothing else needs it.

| Surface | Trigger |
|---|---|
| Authorization | a new route, an ACL entry, `bouncer()`, a guard, a `where('customer_id', …)` |
| Rendered output | a DataGrid closure, `{!! !!}`, `v-html`, an email or PDF template |
| Input | a new request parameter, a FormRequest, a filter or sort argument |
| Uploads | a `mimes:` rule, a stored path, anything served back |
| SQL | `DB::raw`, `whereRaw`, `selectRaw`, `orderByRaw` |
| Secrets | a config key, an API credential, anything logged |
| Payments | a callback, a webhook, an order state transition |

## What Bagisto already does for you

Knowing these prevents both false findings and misplaced effort:

- **Admin ACL fails closed for custom roles.** `Bouncer` middleware refuses any
  route that is neither in `acl.php` nor in `UNRESTRICTED_ROUTES`. A route
  without an ACL entry is not silently public — it 401s for every custom role.
  See [security-authorization.md](security-authorization.md) for the one case that is not true.
- **DataGrid values are tag-stripped.** `sanitizeRow()` runs `strip_tags()` over
  every string before closures run, and filter options render through `v-text`.
  Quotes survive, which is the part that still needs care.
- **Purify strips Blade as well as HTML.** The purifier helper removes `{{ }}`,
  `{!! !!}`, `@if`/`@foreach`… and `<?php`, so stored content cannot become a
  template injection.
- **Eloquent parameterises**, and `$fillable` guards mass assignment on every
  core model.
- **CSRF is on for the whole `web` group**, with one deliberate exclusion:
  `stripe/*`.

## The rules

- **Never weaken an existing defence to make a feature work.** Adding a route to
  `UNRESTRICTED_ROUTES`, a path to the CSRF exclusions, `svg` to a `mimes:` list,
  or `$guarded = []` to a model each need a stated reason and a reviewer.
- **Authorize on the server, every time.** Hiding a button, omitting a menu entry
  or gating a DataGrid action changes what is *shown*. The route and the
  controller decide what is *allowed*.
- **Scope every query to its owner.** A storefront read of orders, addresses,
  downloads or reviews filters on the authenticated customer — never on an id
  from the request alone.
- **Escape at the point of interpolation**, not at the point of storage. The
  same value is safe in element text and dangerous inside an attribute.
- **Validate in a FormRequest**, so the rules are one object a reviewer can read,
  rather than scattered through a controller.
- **Never log or return a secret** — API keys, tokens, card data, password
  hashes. An exception message that reaches the browser is a disclosure.
- **Treat a webhook as anonymous and hostile** until its signature verifies.

## Reporting

Say what an attacker controls, the path it takes to the sink, and what they get.
A finding without those three is a guess, and should say so.

> `RMAStatus::color` is free text saved by an admin. `StatusDataGrid` interpolates
> it into `style="background: …"` without escaping. `strip_tags()` leaves quotes,
> so `red" onmouseover="alert(1)` closes the attribute and runs script in the
> browser of any admin who opens the grid.

## The surfaces

## Contents

- [Rendered output](#rendered-output)
- [Stored content](#stored-content)
- [Uploads](#uploads)
- [SQL](#sql)
- [Mass assignment](#mass-assignment)
- [Secrets](#secrets)
- [Payments and webhooks](#payments-and-webhooks)
- [CSRF](#csrf)

## Rendered output

Blade escapes `{{ }}` and does not escape `{!! !!}`. The places that bypass
escaping deliberately are where to look.

**DataGrid cells** render with `v-html`, so a column value reaches the DOM as
HTML. Two defences are already in place — `sanitizeRow()` runs `strip_tags()`
over every string before closures run, and filter options render through
`v-text` — so injecting an element does not work.

What survives `strip_tags()` is **quotes**, and that is the live risk:

```php
// Vulnerable — the value lands inside an attribute
'closure' => fn ($row) => '<p style="background: '.$row->color.';">…</p>',

// Safe
'closure' => fn ($row) => '<p style="background: '.e($row->color).';">…</p>',
```

`strip_tags('red" onmouseover="alert(1)')` returns the string unchanged, and the
result renders as `<p style="background: red" onmouseover="alert(1);">`.

So: **escape anything a closure interpolates, and treat an attribute as the
dangerous position.** A closure returning only `trans()` output or an integer id
needs nothing. The same reasoning applies to any `{!! !!}` and to a `v-html` in
a Vue component.

Remember who the victim is. A product name is set by an admin or a seller and
rendered in the **customer's** account; an uploaded file name is set by one
operator and rendered to **other admins**. "Only an admin can set it" is not a
reason to skip escaping when someone else reads it.

## Stored content

CMS pages, theme `static_content` sections and anything else accepting markup go
through Purify. The helper also strips Blade:

```php
'/\{\{.*?\}\}/', '/\{!!.*?!!\}/',
'/@(php|if|else|endif|foreach|…)/', '/<\?php.*?\?>/s'
```

That second part matters: without it, stored content rendered through a Blade
path could become **template injection**, which is code execution rather than
XSS. Any new path storing operator-supplied markup must go through the same
helper — see `SectionRepository::sanitizeOptions()` for the pattern, which
sanitises on both the draft and the publish path.

Purify strips `id` attributes by default, which is a functional surprise rather
than a security one, but it is why CSS keyed on an id stops matching.

## Uploads

Every upload needs an explicit `mimes:` allowlist and a `max:`:

```php
'file' => 'required|mimes:bmp,jpeg,jpg,png,webp,mp4,webm,ogg|max:51200',
'logo_path.*' => 'mimes:bmp,jpeg,jpg,png,webp',
```

Checks worth making:

- **Is there an allowlist at all?** A missing `mimes:` accepts anything.
- **Does it admit an active type?** `html`, `svg`, `php`, `xhtml`. Several
  system-config uploads (logo, favicon) do accept **`svg`**, which can carry
  script and is served from the store's own origin. That is a pre-existing
  accepted risk for admin-only branding — do not copy it into a new upload, and
  never into one a customer or seller can reach.
- **Is the stored name derived from user input?** Prefer a generated name.
- **Where does it land?** Anything under `public/` is served directly.
- **Is it echoed back?** A file name rendered in a grid or a page is
  user-controlled text — see [Rendered output](#rendered-output).

## SQL

Eloquent and the query builder parameterise. The exceptions are the raw
fragments, and the rule is simple: **an interpolated request value in a raw
fragment is an injection.**

```php
// Never
->whereRaw("name LIKE '%".request('q')."%'")
->orderByRaw("$column $direction")

// Bindings, and an allowlist for identifiers
->whereRaw('name LIKE ?', ['%'.request('q').'%'])
```

Column and direction are **identifiers**, which cannot be bound — validate them
against a known list instead. A DataGrid's sort arrives from the browser.

## Mass assignment

Core models declare `$fillable`. A change to `$guarded = []`, or adding a
sensitive column to `$fillable`, lets a crafted request set it — `is_user_defined`
on an attribute, `customer_group_id`, a role id, a price. Fill trusted fields
explicitly rather than widening the list.

## Secrets

- API keys and credentials live in config, read from the environment — never
  committed, never defaulted to a real value.
- Do not log them, return them in an API response, or include them in an
  exception the browser sees. An import once answered with the storage path of
  the uploaded file; the same reflex applies to keys.
- A password hash, a token or a 2FA secret must not be selected into a DataGrid
  or an API resource.

## Payments and webhooks

A webhook is an **anonymous request from the internet** that claims to be a
gateway. Treat it as hostile until verified:

- **Verify the signature** before acting — `RazorpayPayment::verifySignature()`,
  PayGlocal's `Crypto` token check.
- **Never trust an amount, a currency or a status from the request.** Confirm
  with the gateway, or against the order already stored.
- **Be idempotent.** A gateway retries; placing an order twice is a real bug.
- **Do not leak state.** A callback that reveals whether an order id exists is an
  enumeration oracle.

The redirect a customer returns through is not proof of payment — it is a URL
they can retype.

## CSRF

On for the whole `web` group, with one deliberate exclusion in `bootstrap/app.php`:

```php
$middleware->validateCsrfTokens(except: ['stripe/*']);
```

That is a gateway callback, which cannot carry a session token and is
authenticated by signature instead. **Adding to this list needs the same
justification**: the endpoint must authenticate the caller some other way. An
exclusion added to make a form or an AJAX call work is a vulnerability.
