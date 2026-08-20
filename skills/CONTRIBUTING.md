# Authoring standard

The rules a skill in this repository must meet. `bin/lint-skills.sh` enforces
every mechanical one; the rest is judgment, and this file is where it lives.

Run before opening a pull request:

```bash
bin/lint-skills.sh
bash skills/tests/lint-skills.test.sh
```

## 1. The dividing line: judgment versus mechanics

| | Example | Enforced by |
|---|---|---|
| Judgment | when a closure belongs in a DataGrid column, whether a reorder test can guard a gapped-`sort_order` bug | the skill's prose |
| Mechanics | a `SKILL.md` over 150 lines, a description not starting `Use when`, a dangling link | `bin/lint-skills.sh` |

If a rule can be decided by a regex, it belongs in the linter, where it is an
exit code. A paragraph can be rationalised past; an exit code cannot.

## 2. Frontmatter contract

Every `SKILL.md` opens on line 1 with a `---` delimited YAML block:

```yaml
---
name: bagisto-datagrid-development
description: Use when building or changing a Bagisto admin listing page — … Trigger phrases include "datagrid", "admin listing", "mass action".
requires: bagisto-coding-standards
license: MIT
---
```

| Field | Rule | Lint code |
|---|---|---|
| `name` | Required. Must equal the directory name, lowercase letters, numbers and hyphens | `NAME_MISSING`, `NAME_MISMATCH`, `NAME_FORMAT` |
| `description` | Required. Must begin `Use when` and end with a `Trigger phrases include "…"` sentence. Under 1024 chars | `DESCRIPTION_*` |
| `requires` | Optional. Skills this one is **incomplete without** — see below | `REQUIRES_UNRESOLVED` |
| `license` | Optional | — |

The description is the only part an agent reads before deciding whether to load
the skill. `Use when` puts the trigger first; the trigger-phrase sentence
catches the wording a user actually types.

### What `requires` means

`requires` declares that a skill **cannot be applied correctly on its own** —
`bagisto-datagrid-development` without `bagisto-coding-standards` produces a grid that fails
review — wrong docblocks, an unescaped closure, a query outside a repository.

It is not a reading list. In particular, **do not list `bagisto-change-verification`**:
every skill ends with a `REQUIRED SUB-SKILL` line pointing at it, and a
dependency true of every skill carries no information.

List direct dependencies only — the chain is transitive.

> **Note:** nothing resolves this chain automatically yet. It is validated by
> `bin/lint-skills.sh` and read by whoever loads the skill. If an installer is
> added (as the UnoPim repo has), it becomes the input to dependency
> resolution — which is why the names must stay accurate.

## 3. Size

| File | Limit | Lint code |
|---|---|---|
| `SKILL.md` | 150 lines | `SIZE_SKILL` |
| Any other `*.md` in the skill directory | 500 lines | `SIZE_REFERENCE` |

A `SKILL.md` is a **router**, not a manual: what the thing is, the rules that
are never negotiable, and a table pointing at reference files. Depth goes in the
references, which load only when the task reaches them.

The cap exists because a `SKILL.md` loads in full every time the skill
activates. This repository's skills were once 5,604 lines of always-loaded text
across ten skills; the same material plus everything added since is now
1,572 lines of router across 20 skills, with 14,866 lines of reference in
101 files loaded only when a task reaches them.

If a skill genuinely cannot be split — it is one long rule table — add its
directory name to `skills/.lint-allow`, one per line, with a comment saying why.

## 4. Splitting an oversized skill

Split by **relocating, never rewriting**. Then prove it:

- Every heading in the original must still exist, in the router or a reference.
- The concatenated references must be whitespace-identical to the part of the
  original they replaced.

Rewriting while splitting makes both checks impossible and quietly loses
content. Rewrite afterwards, as a separate change, if it needs it.

## 5. Links

Reference links are relative and must resolve — `LINK_DANGLING` fails the build
otherwise. Link a skill's references from its `SKILL.md` table, so nothing is
reachable only by knowing the filename.

## 6. Cite the codebase, and prefer it

Every rule should name a real file in the Bagisto checkout as the pattern to
copy. When a reference file and the code disagree, **the code wins** — follow
the checkout and fix the skill. These documents are a snapshot, not the source
of truth.

Verify claims before writing them. A skill that confidently states something the
code does not do is worse than no skill, because it is believed.

## 7. A skill should name the failure it prevents

Before adding one, be able to say what an agent gets wrong without it. If the
answer is "nothing specific", it is documentation, not a skill.

The strongest content is what cannot be inferred from the code in the time
available: that `BASE_URL` is ignored because the Playwright config reads
`APP_URL`, that a DataGrid cell renders through `v-html`, that
`Bus::batch(...)->allowFailures()` lets an import reach `completed` with failed
batches.

## 8. Naming

Directory and `name` match, lowercase and hyphenated, named for the **domain**
rather than the activity — `bagisto-datagrid-development`, not `how-to-build-grids`.

## 9. Before the pull request

- [ ] `bin/lint-skills.sh` is clean.
- [ ] `bash skills/tests/lint-skills.test.sh` passes.
- [ ] A split is proved lossless (§4).
- [ ] New or changed descriptions are synced into `README.md` and `AGENTS.md`.
- [ ] Claims were checked against the codebase, not recalled.
