#!/usr/bin/env bash
#
# The authoring standard, enforced.
#
# Run from the repository root:
#     bin/lint-skills.sh
#
# Exits non-zero on the first standard a skill fails, naming the skill, the rule
# and the fix. Every rule here is mechanical — anything needing judgment belongs
# in skills/CONTRIBUTING.md instead.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT/skills"
ALLOW_FILE="$SKILLS_DIR/.lint-allow"

SKILL_MAX_LINES=150
REFERENCE_MAX_LINES=500
DESCRIPTION_MAX_CHARS=1024

failures=0

fail() {
    printf '%s: %s: %s\n' "$1" "$2" "$3" >&2
    failures=$((failures + 1))
}

# Read one key from a SKILL.md's YAML frontmatter block.
frontmatter() {
    awk -v key="$2" '
        NR == 1 && $0 != "---" { exit }
        NR == 1 { next }
        $0 == "---" { exit }
        index($0, key ":") == 1 {
            sub("^" key ":[ ]*", "")
            print
            exit
        }
    ' "$1"
}

is_allowlisted() {
    [ -f "$ALLOW_FILE" ] && grep -qxF "$1" "$ALLOW_FILE"
}

for skill_dir in "$SKILLS_DIR"/*/; do
    name="$(basename "$skill_dir")"
    skill_md="${skill_dir}SKILL.md"

    # The suite that tests this linter is not itself a skill.
    [ "$name" = "tests" ] && continue

    # A folder of nested skills (api-platform-development) carries no SKILL.md of
    # its own; lint the children instead.
    if [ ! -f "$skill_md" ]; then
        if compgen -G "$skill_dir*/SKILL.md" > /dev/null; then
            continue
        fi

        fail "skills/$name" SKILL_MISSING "a skill directory must contain a SKILL.md"
        continue
    fi

    rel="skills/$name/SKILL.md"

    if [ "$(head -n 1 "$skill_md")" != "---" ]; then
        fail "$rel" FRONTMATTER_MISSING "file must open with a --- delimited YAML block"
        continue
    fi

    declared_name="$(frontmatter "$skill_md" name)"
    description="$(frontmatter "$skill_md" description)"
    requires="$(frontmatter "$skill_md" requires)"

    case "$declared_name" in
        '')   fail "$rel" NAME_MISSING "frontmatter needs a name field" ;;
        "$name") ;;
        *)    fail "$rel" NAME_MISMATCH "name '$declared_name' must equal directory '$name'" ;;
    esac

    if ! printf '%s' "$declared_name" | grep -qE '^[a-z0-9-]+$'; then
        fail "$rel" NAME_FORMAT "name must be lowercase letters, numbers and hyphens only"
    fi

    if [ -z "$description" ]; then
        fail "$rel" DESCRIPTION_MISSING "frontmatter needs a description field"
    else
        case "$description" in
            'Use when'*) ;;
            *) fail "$rel" DESCRIPTION_PREFIX "description must begin with 'Use when' so the trigger is the first thing read" ;;
        esac

        case "$description" in
            *'Trigger phrases include'*) ;;
            *) fail "$rel" DESCRIPTION_TRIGGERS "description must end with a 'Trigger phrases include \"…\"' sentence" ;;
        esac

        if [ "${#description}" -ge "$DESCRIPTION_MAX_CHARS" ]; then
            fail "$rel" DESCRIPTION_LENGTH "description is ${#description} chars; keep it under $DESCRIPTION_MAX_CHARS"
        fi
    fi

    if [ -n "$requires" ]; then
        while IFS= read -r dependency; do
            [ -z "$dependency" ] && continue

            if [ ! -d "$SKILLS_DIR/$dependency" ]; then
                fail "$rel" REQUIRES_UNRESOLVED "requires '$dependency', which is not a skill directory"
            fi
        done < <(printf '%s\n' "$requires" | tr ',' '\n' | tr -d '[:blank:]')
    fi

    lines="$(wc -l < "$skill_md" | tr -d '[:space:]')"

    if [ "$lines" -gt "$SKILL_MAX_LINES" ] && ! is_allowlisted "$name"; then
        fail "$rel" SIZE_SKILL "$lines lines; a SKILL.md must be $SKILL_MAX_LINES or fewer — move depth into a reference file, or allowlist in skills/.lint-allow"
    fi

    for reference in "$skill_dir"*.md; do
        [ "$reference" = "$skill_md" ] && continue
        [ -e "$reference" ] || continue

        reference_lines="$(wc -l < "$reference" | tr -d '[:space:]')"

        if [ "$reference_lines" -gt "$REFERENCE_MAX_LINES" ]; then
            fail "skills/$name/$(basename "$reference")" SIZE_REFERENCE \
                "$reference_lines lines; a reference file must be $REFERENCE_MAX_LINES or fewer — split it"
        fi
    done
done

# Every relative markdown link must resolve, so a split never leaves a dead pointer.
while IFS= read -r markdown; do
    directory="$(dirname "$markdown")"

    while IFS= read -r target; do
        [ -z "$target" ] && continue

        if [ ! -e "$directory/$target" ]; then
            fail "${markdown#"$ROOT"/}" LINK_DANGLING "links to '$target', which does not exist"
        fi
    done < <(grep -oE '\]\([^):]+\.md\)' "$markdown" 2>/dev/null | tr -d '](' | tr -d ')' || true)
done < <(find "$SKILLS_DIR" -name '*.md')

if [ "$failures" -gt 0 ]; then
    printf '\n%s skill lint failure(s)\n' "$failures" >&2
    exit 1
fi

printf 'skills lint clean\n'
