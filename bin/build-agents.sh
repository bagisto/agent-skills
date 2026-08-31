#!/usr/bin/env bash
#
# Assemble AGENTS.md from the fragments in rules/, for one Bagisto line.
#
# Run from the repository root:
#     bin/build-agents.sh                     # defaults to the newest line
#     bin/build-agents.sh --version 2.4
#     bin/build-agents.sh --app ../../../..   # detect from a Bagisto checkout
#     bin/build-agents.sh --check             # verify AGENTS.md is in sync
#
# A fragment named `<package>/v<version>` is version-specific and only the one
# matching the target line is included. Everything else is always included, in
# the order listed in ORDER below.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RULES_DIR="$ROOT/rules"
TARGET="$ROOT/AGENTS.md"

ORDER=(
    bagisto/core
    bagisto/VERSION
    boost
    php
    tests
    laravel/core
    laravel/LARAVEL
    boost/core
    pint/core
    pest/core
    bagisto-playwright-testing
    bagisto-payment-method-development
    bagisto-shipping-method-development
    bagisto-coding-standards
    bagisto-package-development
    bagisto-product-type-development
    api-platform-development
)

version=""
app=""
check=0

while [ $# -gt 0 ]; do
    case "$1" in
        --version) version="$2"; shift 2 ;;
        --app)     app="$2";     shift 2 ;;
        --check)   check=1;      shift ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

detect_version() {
    local core_php
    core_php="$1/packages/Webkul/Core/src/Core.php"

    if [ ! -f "$core_php" ]; then
        echo "no Bagisto checkout at $1 (expected packages/Webkul/Core/src/Core.php)" >&2
        exit 1
    fi

    sed -n "s/.*BAGISTO_VERSION = '\([0-9]\+\.[0-9]\+\).*/\1/p" "$core_php" | head -1
}

if [ -n "$app" ]; then
    version="$(detect_version "$app")"
fi

if [ -z "$version" ]; then
    version="$(ls "$RULES_DIR/bagisto" | sed -n 's/^v\([0-9.]*\)\.md$/\1/p' | sort -V | tail -1)"
fi

if [ ! -f "$RULES_DIR/bagisto/v$version.md" ]; then
    echo "no fragment for Bagisto $version — expected rules/bagisto/v$version.md" >&2
    echo "known lines: $(ls "$RULES_DIR/bagisto" | sed -n 's/^v\([0-9.]*\)\.md$/\1/p' | tr '\n' ' ')" >&2
    exit 1
fi

# The Laravel major each Bagisto line ships on. Read from the checkout when one
# was given, so the fragment can never disagree with composer.json.
laravel_major() {
    if [ -n "$app" ] && [ -f "$app/composer.json" ]; then
        local from_composer
        from_composer="$(sed -n 's/.*"laravel\/framework"[^0-9]*\([0-9]\{1,\}\).*/\1/p' "$app/composer.json" | head -1)"

        if [ -n "$from_composer" ]; then
            echo "$from_composer"
            return
        fi
    fi

    case "$1" in
        2.4) echo 12 ;;
        2.5) echo 13 ;;
        *)   echo "" ;;
    esac
}

laravel="$(laravel_major "$version")"

if [ -z "$laravel" ] || [ ! -f "$RULES_DIR/laravel/v$laravel.md" ]; then
    echo "no Laravel fragment for Bagisto $version — expected rules/laravel/v$laravel.md" >&2
    echo "add the fragment, or extend laravel_major() in $(basename "${BASH_SOURCE[0]}")" >&2
    exit 1
fi

build() {
    echo "<bagisto-guidelines>"

    for name in "${ORDER[@]}"; do
        name="${name/VERSION/v$version}"
        name="${name/LARAVEL/v$laravel}"

        local path="$RULES_DIR/$name.md"

        if [ ! -f "$path" ]; then
            echo "missing fragment: rules/$name.md" >&2
            exit 1
        fi

        echo "=== $name rules ==="
        echo
        cat "$path"
        echo
    done

    echo "</bagisto-guidelines>"
}

if [ "$check" -eq 1 ]; then
    if diff -q <(build) "$TARGET" > /dev/null 2>&1; then
        echo "AGENTS.md is in sync with rules/ for Bagisto $version"
        exit 0
    fi

    echo "AGENTS.md is out of sync with rules/ for Bagisto $version." >&2
    echo "Edit the fragment in rules/, then run: bin/build-agents.sh --version $version" >&2
    diff <(build) "$TARGET" | head -40 >&2
    exit 1
fi

build > "$TARGET"

echo "AGENTS.md built for Bagisto $version from ${#ORDER[@]} fragments"
