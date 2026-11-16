# CHANGELOG entries

`CHANGELOG.md` opens with `## Unreleased`, then one section per release:

```markdown
## Unreleased

- Entry.

## **v2.4.9 (5th of August 2026)** - *Release*

- Entry.
```

Entries are `-` prefixed with a blank line between them, and are **prose written
for the person upgrading**: the user-visible effect, in full sentences. Not a
commit subject, not a diff summary.

> Fixed the mega search leaving you on an empty tab when another tab had
> results, which read as nothing being found. It now opens the first tab that
> matched.

**Every entry is at most two lines — clear and to the point.** This is a hard
ceiling, and it applies to every shape:

| Shape | When |
|---|---|
| `- <prose>` | A change with no reported issue |
| `- #11500 [feature] - <prose>` | A new feature for a reported issue |
| `- #11420 [enhancement] - <prose>` | An improvement to existing behaviour for a reported issue |
| `- #11432 [fixed] - <prose>` | A fix for a reported issue |

**Entries in a section run in four groups**, top to bottom:

1. Entries with no issue number.
2. `[feature]` entries, by issue number, highest first.
3. `[enhancement]` entries, by issue number, highest first.
4. `[fixed]` entries, by issue number, highest first.

A new entry goes where its group and number place it, not simply at the top
or the bottom of the section. Re-check the order after merging a release line
in, since entries from both sides land side by side.

```markdown
## Unreleased

- Reworked admin notifications into a feed any package can add to.

- #11500 [feature] - The storefront can be limited to some countries.

- #11343 [feature] - Admin notifications now report system problems.

- #11575 [fixed] - An order for a product without managed stock can be shipped.

- #11574 [fixed] - Editor content keeps its formatting on the storefront.
```

State the user-visible effect and stop. The cause, the internal mechanism and
the history are **not** CHANGELOG material — they belong in the commit message
or the pull request, which is where anyone investigating the change will look.
If an entry does not fit in two lines, it is carrying explanation that should
move there.

```markdown
- Fixed the admin product listing repeating a product once for every channel it is carried by.
```

```markdown
- Fixed the admin product listing repeating a product once for every channel it is carried by, so a
  store with three channels listed it three times. The PostgreSQL work had widened the grouping from
  the product to every selected column, which made the channel part of the group; it now picks one
  row per product.        ← the cause belongs in the commit message, not here
```

Add the entry under `## Unreleased`. Do not invent a version heading or a date —
releases are cut separately.
