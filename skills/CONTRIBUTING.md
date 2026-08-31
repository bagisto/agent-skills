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
| `name` | Required. Must equal the directory name, begin `bagisto-`, and be lowercase letters, numbers and hyphens | `NAME_MISSING`, `NAME_MISMATCH`, `NAME_FORMAT`, `NAME_PREFIX` |
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

## 7. Two Bagisto lines, one skill

2.4 and 2.5 are maintained together and their stacks differ — Laravel 12 vs 13,
Tailwind 3 vs 4, Pest 3 vs 5, MySQL-only vs PostgreSQL too. Most of what a skill
says holds for both; only a minority diverges.

### `AGENTS.md` is generated — edit `rules/`, not the file

The guidelines blob is assembled from fragments, the way Laravel Boost composes
`laravel/core` with `laravel/v12`:

```
rules/
├── bagisto/core.md    # every line
├── bagisto/v2.4.md    # 2.4 only
├── bagisto/v2.5.md    # 2.5 only
└── …                  # one file per `=== <name> rules ===` section
```

```bash
bin/build-agents.sh                  # newest line
bin/build-agents.sh --version 2.4
bin/build-agents.sh --app ../bagisto # detect from Core::BAGISTO_VERSION
bin/build-agents.sh --check          # CI: fails if AGENTS.md drifted
```

A fragment named `<package>/v<version>` is version-specific; exactly one is
selected per build. Everything else is always included. **Never hand-edit
`AGENTS.md`** — CI runs `--check` and will fail.

A version-invariant fact belongs in `bagisto/core.md`. Put a fact in a version
fragment only when the other line genuinely does something else, and say what
that something else is.

Do not fork a skill per version. Write the shared rule once and mark only the
delta, inline, with a bold **2.4** / **2.5** label so it is greppable:

> **2.5** exposes `npm run test:e2e`. **2.4** has no such script — invoke
> `npx playwright test --config=…` directly.

Three rules for these:

1. **State which line a version-specific fact belongs to.** An unmarked fact is
   a claim about both, and will be read as one.
2. **Never let a fact silently change line.** When a rule becomes true only on
   2.5, mark it and say what 2.4 does instead — deleting the old behaviour
   strands anyone on the maintained release.
3. **Prefer a fact the checkout can answer** over a version label. "Read the
   version from `composer.json`" survives a release; "Laravel v12" does not.

## 8. A skill should name the failure it prevents

Before adding one, be able to say what an agent gets wrong without it. If the
answer is "nothing specific", it is documentation, not a skill.

The strongest content is what cannot be inferred from the code in the time
available: that on 2.4 `BASE_URL` is ignored because the Playwright config reads
`APP_URL`, that a DataGrid cell renders through `v-html`, that
`Bus::batch(...)->allowFailures()` lets an import reach `completed` with failed
batches.

## 9. Naming

Directory and `name` match, lowercase and hyphenated, named for the **domain**
rather than the activity — `bagisto-datagrid-development`, not `how-to-build-grids`.

**Every skill begins `bagisto-`.** These skills are installed into an agent
directory that may already hold another project's — the UnoPim set, for one,
which prefixes `unopim-`. Without a prefix, `coding-standards` from two projects
collide, and the agent has no way to tell which it loaded. `NAME_PREFIX` enforces
this.

The one exception is a **grouping folder** such as `api-platform-development`,
which has no `SKILL.md` of its own. It is not a skill, so the rule does not apply
to it — but every skill inside it does have to carry the prefix, and the linter
checks them individually.

## 10. Before the pull request

- [ ] `bin/lint-skills.sh` is clean.
- [ ] `bash skills/tests/lint-skills.test.sh` passes.
- [ ] A split is proved lossless (§4).
- [ ] Every version-specific fact carries a **2.4** / **2.5** label (§7).
- [ ] `bin/build-agents.sh --check` passes; `AGENTS.md` was not hand-edited (§7).
- [ ] New or changed descriptions are synced into `README.md` and `AGENTS.md`.
- [ ] Claims were checked against the codebase, not recalled.
