# Writing for a developer

## Who is reading

A developer with the Bagisto source open, building something on top of it. They
are not reading for pleasure — they arrived from a search, they want the shape
of the solution and a sample they can adapt, and they will leave as soon as they
have it.

- **Lead with the shape, then the detail.** Say what the thing is and where it
  lives before explaining how to configure it.
- **Cite real paths.** `packages/Webkul/Product/src/Repositories/ProductRepository.php`,
  not "the product repository". The reader wants to open it.
- **Prefer showing to describing.** A twelve-line class says more than three
  paragraphs about the class.
- **Say what will bite them.** The ordering constraint, the cache that must be
  cleared, the provider that must be registered twice. That is the content they
  cannot get from reading the source in the time they have.
- **Never describe the admin UI.** Click paths and button labels are the other
  audience's page — see [user-guide.md](user-guide.md).

## Page shape

```md
# Repositories

Repositories are the only sanctioned way to read and write data in Bagisto…

## Creating a repository

<what it is, then the sample, then the registration step>

## Using it

<the call sites>

## Things to watch

<the constraints>
```

One H1, matching the sidebar entry. `##` for the major moves, `###` beneath.
A page that needs four levels of heading is two pages.

## Code samples

This is where a developer page earns or loses its keep.

**Copy from the checkout.** Open the real file, take the real code, and say
where it came from. A bolded `**File:**` line immediately above the fence is the
clearest form, and the one the newer pages use:

**File:** `packages/Webkul/RMA/src/Providers/ModuleServiceProvider.php`

```php
<?php

namespace Webkul\RMA\Providers;

use Konekt\Concord\BaseModuleServiceProvider;

class ModuleServiceProvider extends BaseModuleServiceProvider
{
    protected $models = [
        \Webkul\RMA\Models\ReturnRequest::class,
    ];
}
```

**Fence every block with its language** — `php`, `bash`, `json`, `blade`, `ts`,
`env`. An unfenced block loses highlighting and, in a long page of them, becomes
unreadable.

**Samples follow `bagisto-coding-standards`.** A published sample is copied
verbatim into real projects, so a missing docblock or a `DB::table()` call in a
controller propagates. Specifically:

- A docblock on every method and property, whatever the visibility.
- No comments inside method bodies. If a line needs prose, the *page* explains
  it — that is what the page is for.
- Data access through a repository.
- Namespaces and class names exactly as they are in the source.

**Elide with `// ...`, and only in the middle.** Never elide the parts that make
the sample work — the namespace, the imports, the class declaration. A reader
who cannot see which `use` statements are needed will guess wrong.

**Do not invent APIs.** If the method you want does not exist, the page cannot
say it does. Document what is there, or say plainly that the extension point is
missing.

## Verify before you write

The most expensive defect in a developer page is a confident sentence about
behaviour the code does not have. Before writing a claim, check it:

```bash
# Does the class still exist, and is that still its namespace?
grep -rn "class SectionRepository" packages/Webkul/

# Is that really the event name?
grep -rn "Event::dispatch('section" packages/Webkul/Theme/src/

# Is that config key real?
grep -rn "'key' => 'catalog.products" packages/Webkul/*/src/Config/system.php

# Is that route name and URI real?
php artisan route:list --path=<area>
```

Read the package's `Config/`, `Routes/`, migrations and `Providers/` directly.
Every route, artisan command, config key, class name, method signature, table
column and file path on the page has to come from one of those, read **this
session** — not from recall.

Bagisto's events are **dot-delimited strings**, not event classes, so a page
that shows `Event::listen(ProductUpdated::class, …)` is wrong in a way that
looks plausible. Check the string.

When a page and the checkout disagree, the checkout wins — update the page and
say so in the commit.

## Versions

Behaviour changes between releases, and a page that quietly documents only the
newest one strands everybody else. Name the release when it matters: "from 2.4,
theme customizations are sections". Check whether the site still carries
per-version page trees before assuming a versioned path exists.

## Tables for reference material

Configuration keys, event names, endpoints and route lists read far better as a
table than as prose:

```md
| Event | Fired when |
|---|---|
| `section.create.after` | A section has been created |
| `section.update.after` | A section has been saved |
```

Keep the columns narrow enough to read without horizontal scrolling, and give
every row the same shape — a table where half the cells are sentences and half
are fragments is harder to scan than a list.

## Callouts

VitePress containers are established house style on the developer side — it uses
several hundred of them. Match the existing usage:

::: warning
Removing a provider from `bootstrap/providers.php` half-loads the package.
:::

| Container | For |
|---|---|
| `::: tip` | A shortcut, a better way, a helpful aside |
| `::: info` | Context the reader needs but will not be hurt by missing |
| `::: warning` | Something that will break if ignored |
| `::: danger` | Something that destroys data or exposes the store |
| `::: details` | A long aside — collapsed by default |

Pick by consequence, not by emphasis. Promoting an `info` to a `warning` to make
it noticed is how a page ends up with five warnings and no signal. Do not stack
two containers back to back, and do not open a section with one — the reader
needs the ordinary sentence first to know what is being warned about.

## Style

- Second person, present tense. "You register the provider", not "the provider
  should be registered".
- Sentence case in headings.
- Backticks for anything typed: class names, methods, paths, commands, keys.
- Bold for emphasis in prose, never for code — that is what backticks are for.
- Wrap prose at a readable width; do not reflow paragraphs you did not change.
- No "simply", "just", "obviously".
