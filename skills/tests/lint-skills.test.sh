#!/usr/bin/env bash
#
# Proves every lint rule fires. A linter that only ever prints "clean" has not
# been shown to catch anything.
#
# Each case builds a throwaway repository containing one deliberately broken
# skill, runs the real linter against it, and asserts the expected rule code is
# reported.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LINTER="$ROOT/bin/lint-skills.sh"

passed=0
failed=0

# Build a scratch repo holding one skill, then run the linter over it.
run_case() {
    local case_name="$1" expected="$2" skill_name="$3" skill_body="$4" extra_file="${5:-}"

    local workspace
    workspace="$(mktemp -d)"

    mkdir -p "$workspace/bin" "$workspace/skills/$skill_name"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    printf '%s' "$skill_body" > "$workspace/skills/$skill_name/SKILL.md"

    if [ -n "$extra_file" ]; then
        printf 'placeholder\n' > "$workspace/skills/$skill_name/$extra_file"
    fi

    local output
    output="$(bash "$workspace/bin/lint-skills.sh" 2>&1)"

    if printf '%s' "$output" | grep -q "$expected"; then
        printf '  ok    %-24s reports %s\n' "$case_name" "$expected"
        passed=$((passed + 1))
    else
        printf '  FAIL  %-24s expected %s, got:\n%s\n' "$case_name" "$expected" "$output"
        failed=$((failed + 1))
    fi

    rm -rf "$workspace"
}

valid_frontmatter() {
    printf -- '---\nname: %s\ndescription: Use when testing the linter. Trigger phrases include "test".\n---\n\n# Test\n' "$1"
}

run_case 'no frontmatter'  FRONTMATTER_MISSING  bagisto-good-skill \
    '# Just a heading, no frontmatter
'

run_case 'name mismatch'   NAME_MISMATCH        bagisto-good-skill \
    '---
name: some-other-name
description: Use when testing. Trigger phrases include "test".
---
'

run_case 'no description'  DESCRIPTION_MISSING  bagisto-good-skill \
    '---
name: bagisto-good-skill
---
'

run_case 'bad description' DESCRIPTION_PREFIX   bagisto-good-skill \
    '---
name: bagisto-good-skill
description: Activates when doing things. Trigger phrases include "test".
---
'

run_case 'no triggers'     DESCRIPTION_TRIGGERS bagisto-good-skill \
    '---
name: bagisto-good-skill
description: Use when doing things, with no trigger sentence at all.
---
'

run_case 'bad requires'    REQUIRES_UNRESOLVED  bagisto-good-skill \
    '---
name: bagisto-good-skill
description: Use when testing. Trigger phrases include "test".
requires: a-skill-that-does-not-exist
---
'

run_case 'missing prefix'  NAME_PREFIX          some-random-skill \
    '---
name: some-random-skill
description: Use when testing. Trigger phrases include "test".
---
'

run_case 'dangling link'   LINK_DANGLING        bagisto-good-skill \
    '---
name: bagisto-good-skill
description: Use when testing. Trigger phrases include "test".
---

See [missing.md](missing.md).
'

# An oversized SKILL.md: frontmatter plus enough body to pass 150 lines.
oversized="$(valid_frontmatter bagisto-good-skill)"
for _ in $(seq 1 160); do
    oversized+='padding
'
done
run_case 'oversized skill' SIZE_SKILL bagisto-good-skill "$oversized"

# A valid skill must lint clean, or every case above proves nothing.
run_case_clean() {
    local workspace
    workspace="$(mktemp -d)"

    mkdir -p "$workspace/bin" "$workspace/skills/bagisto-good-skill"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    valid_frontmatter bagisto-good-skill > "$workspace/skills/bagisto-good-skill/SKILL.md"

    if bash "$workspace/bin/lint-skills.sh" > /dev/null 2>&1; then
        printf '  ok    %-24s passes\n' 'valid skill'
        passed=$((passed + 1))
    else
        printf '  FAIL  %-24s a valid skill was rejected:\n%s\n' 'valid skill' \
            "$(bash "$workspace/bin/lint-skills.sh" 2>&1)"
        failed=$((failed + 1))
    fi

    rm -rf "$workspace"
}

run_case_clean

# The size cap is waivable, and waiving it must not make the linter mistake the
# SKILL.md for one of its own reference files.
run_case_allowlisted() {
    local workspace
    workspace="$(mktemp -d)"

    mkdir -p "$workspace/bin" "$workspace/skills/bagisto-good-skill"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    printf 'bagisto-good-skill\n' > "$workspace/skills/.lint-allow"

    {
        valid_frontmatter bagisto-good-skill
        for _ in $(seq 1 200); do printf 'padding\n'; done
    } > "$workspace/skills/bagisto-good-skill/SKILL.md"

    local output
    output="$(bash "$workspace/bin/lint-skills.sh" 2>&1)"

    if [ -z "$(printf '%s' "$output" | grep -E 'SIZE_SKILL|SIZE_REFERENCE')" ]; then
        printf '  ok    %-24s waived, and not linted as its own reference\n' 'allowlisted skill'
        passed=$((passed + 1))
    else
        printf '  FAIL  %-24s got:\n%s\n' 'allowlisted skill' "$output"
        failed=$((failed + 1))
    fi

    rm -rf "$workspace"
}

run_case_allowlisted

# A grouping folder holds skills that must be linted too — they were silently
# exempt until the linter learned to descend.
run_case_nested() {
    local workspace
    workspace="$(mktemp -d)"

    mkdir -p "$workspace/bin" "$workspace/skills/group/nested-skill"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    printf -- '---\nname: wrong-name\ndescription: Activates when nested. \n---\n' \
        > "$workspace/skills/group/nested-skill/SKILL.md"

    local output
    output="$(bash "$workspace/bin/lint-skills.sh" 2>&1)"

    if printf '%s' "$output" | grep -q NAME_MISMATCH; then
        printf '  ok    %-24s a nested skill is linted\n' 'nested skill'
        passed=$((passed + 1))
    else
        printf '  FAIL  %-24s nested skill escaped the linter:\n%s\n' 'nested skill' "$output"
        failed=$((failed + 1))
    fi

    rm -rf "$workspace"
}

run_case_nested

printf '\n%s passed, %s failed\n' "$passed" "$failed"

[ "$failed" -eq 0 ]
