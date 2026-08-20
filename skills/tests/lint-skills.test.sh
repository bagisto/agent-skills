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

run_case 'no frontmatter'  FRONTMATTER_MISSING  good-skill \
    '# Just a heading, no frontmatter
'

run_case 'name mismatch'   NAME_MISMATCH        good-skill \
    '---
name: some-other-name
description: Use when testing. Trigger phrases include "test".
---
'

run_case 'no description'  DESCRIPTION_MISSING  good-skill \
    '---
name: good-skill
---
'

run_case 'bad description' DESCRIPTION_PREFIX   good-skill \
    '---
name: good-skill
description: Activates when doing things. Trigger phrases include "test".
---
'

run_case 'no triggers'     DESCRIPTION_TRIGGERS good-skill \
    '---
name: good-skill
description: Use when doing things, with no trigger sentence at all.
---
'

run_case 'bad requires'    REQUIRES_UNRESOLVED  good-skill \
    '---
name: good-skill
description: Use when testing. Trigger phrases include "test".
requires: a-skill-that-does-not-exist
---
'

run_case 'dangling link'   LINK_DANGLING        good-skill \
    '---
name: good-skill
description: Use when testing. Trigger phrases include "test".
---

See [missing.md](missing.md).
'

# An oversized SKILL.md: frontmatter plus enough body to pass 150 lines.
oversized="$(valid_frontmatter good-skill)"
for _ in $(seq 1 160); do
    oversized+='padding
'
done
run_case 'oversized skill' SIZE_SKILL good-skill "$oversized"

# A valid skill must lint clean, or every case above proves nothing.
run_case_clean() {
    local workspace
    workspace="$(mktemp -d)"

    mkdir -p "$workspace/bin" "$workspace/skills/good-skill"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    valid_frontmatter good-skill > "$workspace/skills/good-skill/SKILL.md"

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

    mkdir -p "$workspace/bin" "$workspace/skills/good-skill"
    cp "$LINTER" "$workspace/bin/lint-skills.sh"
    printf 'good-skill\n' > "$workspace/skills/.lint-allow"

    {
        valid_frontmatter good-skill
        for _ in $(seq 1 200); do printf 'padding\n'; done
    } > "$workspace/skills/good-skill/SKILL.md"

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

printf '\n%s passed, %s failed\n' "$passed" "$failed"

[ "$failed" -eq 0 ]
