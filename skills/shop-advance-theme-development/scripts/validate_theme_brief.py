#!/usr/bin/env python3
"""Validate a completed Bagisto storefront theme brief without dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REQUIRED_HEADINGS = {
    "delivery context",
    "identity",
    "creative direction",
    "semantic token contract",
    "commerce priorities",
    "page composition",
    "content and administration",
    "licensing and provenance",
    "quality budgets",
    "acceptance evidence",
}

CRITICAL_FIELDS = {
    "theme code",
    "display name",
    "brand promise",
    "primary audience",
    "concept in one sentence",
    "primary style archetype",
    "visual variance (1-10) and reason",
    "motion intensity (1-10) and reason",
    "information density (1-10) and reason",
    "primary conversion journey",
    "cms/theme-customization strategy",
    "accessibility target",
    "core web vitals/performance budgets",
}

RECOMMENDED_FIELDS = {
    "accepted recommendations and reasons",
    "bagisto ui/ux findings and resolutions",
    "explicit anti-goals",
    "composition language",
    "merchandising hierarchy",
    "typography roles",
    "color roles and contrast targets",
    "candidate archetype, supporting influence, palette, typography, signatures, and effects",
    "installed tailwind compatibility tokens that must remain",
    "required loading, empty, disabled, selected, error, success, and out-of-stock states",
    "content ownership map",
    "localization and rtl requirements",
    "font/icon/media redistribution evidence",
    "supported browsers and viewports",
    "required test journeys",
    "rejected recommendations and reasons",
    "merchant editability and empty-state evidence",
    "bagisto ui/ux engine identity and query or explicit manual fallback reason",
    "ux, icon, laravel, vue, and tailwind guidance adopted",
}

DIAL_FIELDS = {
    "visual variance (1-10) and reason",
    "motion intensity (1-10) and reason",
    "information density (1-10) and reason",
}

THEME_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
FIELD_RE = re.compile(r"^\s*-\s+([^:]+):\s*(.*)$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
PLACEHOLDER_RE = re.compile(
    r"\{\{[^{}]+\}\}|<[a-z0-9-]+(?:\|[a-z0-9-]+)+>",
    re.IGNORECASE,
)
EMPTY_VALUES = {"", "-", "tbd", "todo", "n/a?", "unknown", "not decided"}


@dataclass(frozen=True)
class Finding:
    level: str
    check: str
    message: str
    field: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a completed Bagisto storefront theme brief without changing files."
    )
    parser.add_argument("--brief", required=True, type=Path, help="completed Markdown theme brief")
    parser.add_argument("--strict", action="store_true", help="return nonzero when warnings remain")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("`")).casefold()


def useful(value: str) -> bool:
    normalized = normalize(value)
    return normalized not in EMPTY_VALUES and not PLACEHOLDER_RE.search(value)


def parse_brief(source: str) -> tuple[set[str], dict[str, str], list[str]]:
    headings: set[str] = set()
    fields: dict[str, str] = {}
    duplicates: list[str] = []

    for line in source.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            headings.add(normalize(heading.group(1)))
            continue

        field = FIELD_RE.match(line)
        if not field:
            continue

        name = normalize(field.group(1))
        value = field.group(2).strip()
        if name in fields:
            duplicates.append(name)
        else:
            fields[name] = value

    return headings, fields, duplicates


def dial_value(value: str) -> int | None:
    match = re.match(r"^\s*`?(10|[1-9])`?(?:\s|[—–:-]|$)", value)
    return int(match.group(1)) if match else None


def validate(source: str) -> list[Finding]:
    headings, fields, duplicates = parse_brief(source)
    findings: list[Finding] = []

    for heading in sorted(REQUIRED_HEADINGS - headings):
        findings.append(Finding("fail", "heading.required", f"missing required section: {heading}"))

    for field in duplicates:
        findings.append(Finding("warn", "field.duplicate", "field appears more than once", field))

    for field in sorted(CRITICAL_FIELDS):
        if field not in fields:
            findings.append(Finding("fail", "field.required", "critical field is missing", field))
        elif not useful(fields[field]):
            findings.append(Finding("fail", "field.incomplete", "critical field is empty or unresolved", field))

    for field in sorted(RECOMMENDED_FIELDS):
        if field not in fields:
            findings.append(Finding("warn", "field.recommended", "recommended field is missing", field))
        elif not useful(fields[field]):
            findings.append(Finding("warn", "field.incomplete", "recommended field is empty or unresolved", field))

    for field in sorted(DIAL_FIELDS):
        value = fields.get(field, "")
        if useful(value) and dial_value(value) is None:
            findings.append(Finding("fail", "dial.range", "include an integer from 1 through 10", field))

    theme_code = fields.get("theme code", "").strip().strip("`")
    if useful(theme_code) and not THEME_CODE_RE.fullmatch(theme_code):
        findings.append(
            Finding(
                "fail",
                "identity.theme-code",
                "use a lowercase theme code beginning with a letter and containing only letters, digits, or hyphens",
                "theme code",
            )
        )

    if PLACEHOLDER_RE.search(source):
        findings.append(Finding("warn", "brief.placeholders", "unresolved template placeholders remain"))

    return findings


def result_document(path: Path, findings: list[Finding]) -> dict[str, object]:
    counts = {
        "fail": sum(item.level == "fail" for item in findings),
        "warn": sum(item.level == "warn" for item in findings),
    }
    return {
        "schema_version": 1,
        "brief": str(path.resolve()),
        "summary": counts,
        "findings": [asdict(item) for item in findings],
    }


def print_human(document: dict[str, object]) -> None:
    summary = document["summary"]
    assert isinstance(summary, dict)
    print(f"Theme brief: {document['brief']}")
    print(f"Summary: {summary['fail']} failure(s), {summary['warn']} warning(s)")

    findings = document["findings"]
    assert isinstance(findings, list)
    for raw in findings:
        assert isinstance(raw, dict)
        location = f" [{raw['field']}]" if raw.get("field") else ""
        print(f"- {str(raw['level']).upper()} {raw['check']}{location}: {raw['message']}")

    if not findings:
        print("Theme brief is complete.")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        path = args.brief.resolve(strict=True)
        if not path.is_file():
            raise ValueError("brief must be an existing file")
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        if args.as_json:
            print(json.dumps({"error": str(error)}, indent=2))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2

    findings = validate(source)
    document = result_document(path, findings)

    if args.as_json:
        print(json.dumps(document, indent=2))
    else:
        print_human(document)

    has_failures = any(item.level == "fail" for item in findings)
    has_warnings = any(item.level == "warn" for item in findings)
    return 1 if has_failures or (args.strict and has_warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
