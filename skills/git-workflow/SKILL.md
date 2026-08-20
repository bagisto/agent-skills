---
name: git-workflow
description: Use when branching, committing, writing a CHANGELOG entry or opening a pull request against a Bagisto repository. Trigger phrases include "branch", "commit", "commit message", "PR", "pull request", "changelog", "merge", "conventional commits", "release notes".
license: MIT
---

# Git Workflow

The conventions this repository actually follows, read from its history rather
than from a generic Git guide.

## Branches

`<author>/<topic>` or `<author>/<type>/<topic>`, lowercase and hyphenated:

```
devansh-webkul/themes-improvements
kartikeywebkul9260/v2.4_file_attribute_required_validation
Vansh-Sharmaa/fix/duplicate-product-customizable-options
```

Branch from the release line you are targeting — `2.4` for 2.4 work, `master`
for the next major — and open the pull request against that same branch. Never
commit directly to `2.4` or `master`.

## Commits

Conventional Commits, lowercase subject, imperative or descriptive. Across the
last 200 commits: `fix:` 66, `feat:` 21, `chore:` 9, `chore(deps):` 5,
`test:` 3, `refactor(shop):` 1, `docs:` 1.

```
fix: grouped themes into two parts my theme and buy themes
feat: playwight testcases updated and draft issue fixed
test: playwright testcases added
chore: changelog and version updated
```

A scope is optional and used sparingly — `refactor(shop):`, `chore(deps):`.

Write a body only when the subject cannot carry the reason — 12 of the last 100
non-merge commits have one. The body explains **why**, not what the diff shows —
and it is the right home for anything you were tempted to write as a comment in
the code, since this codebase does not take comments inside method bodies.

**Never add AI or tool attribution.** No `Co-Authored-By` for an assistant, no
"Generated with", no robot emoji. There are none in this repository's history
and none should appear.

## CHANGELOG

`CHANGELOG.md` opens with `## Unreleased`, then one section per release:

```markdown
## Unreleased

- Entry.

## **v2.4.9 (5th of August 2026)** - *Release*

- Entry.
```

Entries are `-` prefixed with a blank line between them, and are **prose written
for the person upgrading**: the user-visible effect first, the cause second, in
full sentences. Not a commit subject, not a diff summary.

> Fixed the mega search leaving you on an empty tab when another tab had
> results, which read as nothing being found. It now opens the first tab that
> matched.

Two shapes, and the length rule differs between them:

| Shape | When | Length |
|---|---|---|
| `- <prose>` | A feature or a change with no reported issue | As long as it needs, one paragraph |
| `- #11432 [fixed] - <prose>` | A fix for a reported issue | **At most two lines** |

An issue-numbered entry is a terse record against a ticket that carries the
detail, so keep it to two lines. A plain entry may run longer when the change
genuinely needs explaining, but one paragraph is the ceiling.

Add the entry under `## Unreleased`. Do not invent a version heading or a date —
releases are cut separately.

## Pull requests

Merged with GitHub's default subject, which is what the history shows:

```
Merge pull request #11426 from devansh-webkul/themes-improvements
```

The description states what changed and why, and names anything a reviewer
cannot see in the diff — a config default, a migration, a follow-up left out.
Run the verification gates before opening it, and say in the description which
ran and which were skipped.

## Rules

- **Do not commit, push, or open a PR unless asked.** Leave the work in the
  tree and say what is ready.
- **Never `--force` onto a shared branch**, and never rewrite published history.
- **Never commit `.env`, credentials, `vendor/`, `node_modules/`, or build
  output under `public/themes/*/build/`.**
- **One logical change per commit.** A fix and an unrelated refactor are two
  commits, so either can be reverted alone.
- **Do not add or remove a Composer or npm dependency without approval**, and
  never commit a lockfile change you did not intend.
- **Run the gates first.** A commit that fails Pint or the tests is a commit
  that fails CI.

**REQUIRED SUB-SKILL:** Use change-verification before calling any change done.
