#!/usr/bin/env python3
"""Validate completed Bagisto theme ownership and journey evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CORE_JOURNEYS = {
    "home",
    "navigation",
    "search",
    "category",
    "filters-sort",
    "product-simple",
    "cart",
    "checkout-guest",
    "checkout-customer",
    "authentication",
    "customer-account",
    "wishlist",
    "compare",
    "review",
    "cms-404",
    "locale-currency",
    "runtime-integrity",
    "responsive",
    "accessibility",
}

OWNER_TYPES = {
    "theme_customization",
    "channel",
    "configuration",
    "cms_page",
    "category",
    "product",
    "locale",
    "extension",
    "derived_commerce",
    "code_structure",
}

SURFACE_KINDS = {"structure", "editorial", "catalog", "commerce", "configuration", "extension"}
ADMIN_CONTROLLED_KINDS = {"editorial", "catalog", "configuration", "extension"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Ownership manifest JSON")
    parser.add_argument(
        "--inventory",
        help="JSON output from inspect_bagisto_test_surface.py; requires every discovered core/product journey",
    )
    parser.add_argument(
        "--strict-admin-control",
        action="store_true",
        help="Require editorial/catalog/configuration/extension surfaces to be merchant editable",
    )
    parser.add_argument(
        "--require-journey",
        action="append",
        default=[],
        help="Additional installed/enabled journey ID; repeat as needed",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    return parser.parse_args()


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_surface(surface: Any, index: int, strict: bool) -> list[str]:
    prefix = f"surfaces[{index}]"
    errors: list[str] = []
    if not isinstance(surface, dict):
        return [f"{prefix} must be an object"]

    for key in ("id", "route", "selector"):
        if not non_empty(surface.get(key)):
            errors.append(f"{prefix}.{key} must be a non-empty string")

    kind = surface.get("kind")
    if kind not in SURFACE_KINDS:
        errors.append(f"{prefix}.kind must be one of {sorted(SURFACE_KINDS)}")

    merchant_editable = surface.get("merchant_editable")
    if not isinstance(merchant_editable, bool):
        errors.append(f"{prefix}.merchant_editable must be boolean")

    owner = surface.get("owner")
    owner_type = owner.get("type") if isinstance(owner, dict) else None
    if owner_type not in OWNER_TYPES:
        errors.append(f"{prefix}.owner.type must be one of {sorted(OWNER_TYPES)}")

    if owner_type == "code_structure" and kind != "structure":
        errors.append(f"{prefix} uses code_structure for a non-structural surface")
    if merchant_editable and owner_type in {"code_structure", "derived_commerce"}:
        errors.append(f"{prefix} is merchant editable but has non-editor owner {owner_type}")
    if strict and kind in ADMIN_CONTROLLED_KINDS and merchant_editable is not True:
        errors.append(f"{prefix} must be merchant editable in strict mode")

    evidence = surface.get("evidence")
    if not isinstance(evidence, dict):
        errors.append(f"{prefix}.evidence must be an object")
        return errors

    if not non_empty(evidence.get("source_binding")):
        errors.append(f"{prefix}.evidence.source_binding must identify the source path/contract")
    if evidence.get("result") != "pass":
        errors.append(f"{prefix}.evidence.result must be pass")

    if merchant_editable:
        if not non_empty(evidence.get("spec")) or not non_empty(evidence.get("test")):
            errors.append(f"{prefix} must identify its Playwright spec and test title")
        propagation = evidence.get("propagation")
        if not isinstance(propagation, dict):
            errors.append(f"{prefix}.evidence.propagation must be an object")
        else:
            for key in ("save", "storefront", "restore"):
                if propagation.get(key) is not True:
                    errors.append(f"{prefix}.evidence.propagation.{key} must be true")
            scopes = owner.get("scope", []) if isinstance(owner, dict) else []
            if any(scope in {"channel", "locale", "theme"} for scope in scopes):
                if propagation.get("scope_isolation") is not True:
                    errors.append(f"{prefix}.evidence.propagation.scope_isolation must be true")

    return errors


def validate_journey(journey: Any, index: int) -> list[str]:
    prefix = f"journeys[{index}]"
    errors: list[str] = []
    if not isinstance(journey, dict):
        return [f"{prefix} must be an object"]

    if not non_empty(journey.get("id")):
        errors.append(f"{prefix}.id must be a non-empty string")
    applicable = journey.get("applicable")
    if not isinstance(applicable, bool):
        errors.append(f"{prefix}.applicable must be boolean")
        return errors

    if applicable:
        if journey.get("result") != "pass":
            errors.append(f"{prefix}.result must be pass for an applicable journey")
        if not non_empty(journey.get("spec")) or not non_empty(journey.get("test")):
            errors.append(f"{prefix} must identify its Playwright spec and test title")
    else:
        if not non_empty(journey.get("reason")):
            errors.append(f"{prefix}.reason must explain why the journey is unavailable")
        if not non_empty(journey.get("applicability_evidence")):
            errors.append(f"{prefix}.applicability_evidence must prove the feature is unavailable or disabled")

    return errors


def validate_manifest(data: Any, strict: bool, required_journeys: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["manifest root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    for key in ("theme_code", "environment"):
        if not non_empty(data.get(key)):
            errors.append(f"{key} must be a non-empty string")

    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("surfaces must be a non-empty array")
        surfaces = []
    surface_ids: list[str] = []
    for index, surface in enumerate(surfaces):
        errors.extend(validate_surface(surface, index, strict))
        if isinstance(surface, dict) and non_empty(surface.get("id")):
            surface_ids.append(surface["id"])
    duplicates = sorted({item for item in surface_ids if surface_ids.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate surface IDs: {', '.join(duplicates)}")

    journeys = data.get("journeys")
    if not isinstance(journeys, list) or not journeys:
        errors.append("journeys must be a non-empty array")
        journeys = []
    journey_ids: list[str] = []
    for index, journey in enumerate(journeys):
        errors.extend(validate_journey(journey, index))
        if isinstance(journey, dict) and non_empty(journey.get("id")):
            journey_ids.append(journey["id"])
    duplicate_journeys = sorted({item for item in journey_ids if journey_ids.count(item) > 1})
    if duplicate_journeys:
        errors.append(f"duplicate journey IDs: {', '.join(duplicate_journeys)}")

    missing = sorted(required_journeys - set(journey_ids))
    if missing:
        errors.append(f"missing required journey rows: {', '.join(missing)}")

    cleanup = data.get("cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("result") != "pass":
        errors.append("cleanup.result must be pass")
    if not isinstance(cleanup, dict) or not non_empty(cleanup.get("evidence")):
        errors.append("cleanup.evidence must identify restoration/reset evidence")

    return errors


def required_journeys_from_inventory(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("required_journeys") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError("inventory.required_journeys must be an array")

    result: set[str] = set()
    for index, row in enumerate(rows):
        journey_id = row.get("id") if isinstance(row, dict) else None
        if not non_empty(journey_id):
            raise ValueError(f"inventory.required_journeys[{index}].id must be a non-empty string")
        result.add(journey_id)
    return result


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"manifest does not exist: {manifest_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"invalid JSON: {error}", file=sys.stderr)
        return 2

    required = CORE_JOURNEYS | set(args.require_journey)
    if args.inventory:
        try:
            required |= required_journeys_from_inventory(Path(args.inventory).resolve())
        except FileNotFoundError:
            print(f"inventory does not exist: {Path(args.inventory).resolve()}", file=sys.stderr)
            return 2
        except (json.JSONDecodeError, ValueError) as error:
            print(f"invalid inventory: {error}", file=sys.stderr)
            return 2
    errors = validate_manifest(data, args.strict_admin_control, required)
    result = {
        "valid": not errors,
        "manifest": str(manifest_path),
        "required_journeys": sorted(required),
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("Ownership manifest is valid and all required evidence rows pass.")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
