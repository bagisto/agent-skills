---
name: bagisto-coding-standards
description: Use when writing, changing or reviewing any Bagisto PHP or Blade — the conventions this codebase holds to, covering Laravel idiom, code style, comments and docblocks, database access, Blade, security and localization. Trigger phrases include "standards", "conventions", "code style", "docblock", "comments", "repository pattern", "blade", "component", "binding", "event", "migration", "security", "XSS", "authorization", "escaping", "is this safe", "best practice".
license: MIT
---

# Coding Standards

The canonical rules for all Bagisto code, in one place, so a change to a
DataGrid, a payment class or a theme is held to the same bar as a change to a
package.

**Pint decides the mechanical questions.** Run `vendor/bin/pint` and trust it for
spacing, import order, trailing commas and the rest. What follows is what Pint
cannot see — and what a reviewer will otherwise send back.

## Reference files

| File | Load when |
|---|---|
| [code-style.md](code-style.md) | Writing any PHP — multi-clause conditions, class member order |
| [comments.md](comments.md) | Any comment or docblock, in any language |
| [laravel.md](laravel.md) | Framework idiom — events, migrations, config, helpers, validation, queues |
| [data-access.md](data-access.md) | Reading or writing the database — the repository rule and its one exception |
| [security.md](security.md) | Output, input, uploads, SQL, secrets, payments |
| [security-authorization.md](security-authorization.md) | Routes, permissions, guards, one user's access to another's data |
| [blade.md](blade.md) | Any `.blade.php` — namespaces, `:` versus `::`, components, page skeleton |
| [blade-formatting.md](blade-formatting.md) | Indentation, attribute layout, `@props` alignment, recipes |
| [localization.md](localization.md) | Any user-facing string, or a `Resources/lang/` change |

The PHP rules apply inside an `@php` block too, which Pint cannot reach.

## The rules in one screen

- **Every method and property carries a docblock**, whatever its visibility. The
  description is a capitalised sentence ending in a full stop. Type information
  belongs in the signature; add `@param`/`@return` only for what a native type
  cannot express.
- **Class members run constants → properties → constructor → public →
  protected → private**, each visibility one contiguous block. A helper called
  by a public method still lives in the protected block at the bottom.
- **A condition with more than one clause goes multiline**, the boolean operator
  leading each line. Single-clause conditions stay inline. The rule keys off the
  number of clauses, not the line length.
- **No comments inside method bodies**, object literals or markup — not even a
  one-line "why". A non-obvious reason belongs in the method's docblock or the
  commit message. If a line needs prose to be understood, extract a named
  method instead. See [comments.md](comments.md).
- **A class docblock defines what the class is.** It is not the history of what
  it replaced or why the previous approach was wrong.
- **All database access goes through a repository.** No `DB::` and no model
  queries in controllers, listeners, jobs or services. The single sanctioned
  exception is a DataGrid's `prepareQueryBuilder()`.
- **Events are dot-delimited strings**, not classes — `catalog.product.update.after`
  — and fire in `before`/`after` pairs. See [laravel.md](laravel.md).
- **`:` binds a PHP value, `::` passes a literal `:` through to Vue**, and `::`
  only works on a Blade component tag. Getting this wrong fails silently. See
  [blade.md](blade.md).
- **Authorize on the server and escape at the point of interpolation.** Hiding a
  control is presentation; the route and the controller decide what is allowed,
  and a value is safe in element text yet dangerous inside an attribute. See
  [security.md](security.md).
- **Scope every storefront query to its owner.** An id from the request never
  selects a row on its own — that is the easiest real vulnerability to introduce
  here. See [security-authorization.md](security-authorization.md).
- **Every user-facing string goes through `trans()`**, with the key added to all
  22 locales and verified by `php artisan bagisto:translations:check`.
- **Fix what you touch.** A pre-existing violation in a file you edit is yours —
  scan the whole class's member order and docblocks, not just your own lines.

## Where the code and these files disagree

The checkout wins. Follow the surrounding code, say so in your summary, and
raise the drift — these files are a snapshot, not the source of truth.

That is different from a file that is simply wrong: a missing docblock in an
untouched class is debt, not a convention. Match the *rule*, not the worst
example of it.

## Related

- **`bagisto-code-review`** — applying all of this to someone else's change.
- **`bagisto-package-development`** — the structure these rules are written inside.
