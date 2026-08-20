#!/usr/bin/env python3
"""Inventory Bagisto theme and Playwright test surfaces without changing the checkout."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


FEATURE_PATTERNS: dict[str, tuple[str, ...]] = {
    "home": ("home",),
    "navigation": ("home", "navigation", "menu"),
    "search": ("search",),
    "category": ("categor",),
    "filters-sort": ("filter", "sort"),
    "product": ("product",),
    "cart": ("cart",),
    "checkout": ("checkout",),
    "authentication": ("auth", "login", "register"),
    "customer-account": ("customer", "address", "order"),
    "wishlist": ("wishlist",),
    "compare": ("compare",),
    "review": ("review",),
    "cms": ("cms",),
    "theme-customization": ("theme", "customization"),
    "locale-currency": ("locale", "currency"),
    "rma": ("rma",),
    "gdpr": ("gdpr",),
}

OPTIONAL_PACKAGE_FEATURES: dict[str, str] = {
    "GDPR": "gdpr",
    "RMA": "rma",
    "SocialLogin": "social-login",
    "SocialShare": "social-share",
}

MUTATION_REVIEW_SIGNALS: dict[str, re.Pattern[str]] = {
    "creates_records": re.compile(r"create(?:Product|Theme|Customer|Category|Order)|beforeAll\s*\(", re.I),
    "deletes_first_record": re.compile(r"deleteFirst|deleteIcons?\.first\s*\(", re.I),
    "hardcoded_first_id": re.compile(r"selectOption\s*\(\s*['\"]1['\"]", re.I),
    "hardcoded_default_theme": re.compile(r"selectOption\s*\(\s*['\"]default['\"]", re.I),
    "writes_auth_state": re.compile(r"storageState|writeFileSync", re.I),
}

SOURCE_SIGNALS: dict[str, re.Pattern[str]] = {
    "theme_customization": re.compile(r"theme[_-]?customization|ThemeCustomization", re.I),
    "channel": re.compile(r"getCurrentChannel|current_channel|channel(?:_id)?", re.I),
    "cms": re.compile(r"cms|CMS", re.I),
    "catalog_binding": re.compile(r"\$(?:product|category|products|categories)\b"),
    "dynamic_loop": re.compile(r"@foreach|v-for\s*=", re.I),
    "localized": re.compile(r"@lang\s*\(|__\s*\(", re.I),
    "route_binding": re.compile(r"route\s*\(|url\s*\(", re.I),
}

RISK_SIGNALS: dict[str, re.Pattern[str]] = {
    "blade_php_block": re.compile(r"@php\b", re.I),
    "fixed_theme_asset": re.compile(r"bagisto_asset\s*\(\s*['\"]", re.I),
    "placeholder_link": re.compile(r"href\s*=\s*['\"]#['\"]", re.I),
    "inline_absolute_url": re.compile(r"https?://", re.I),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, help="Bagisto checkout root")
    parser.add_argument("--theme-code", help="Configured Shop theme code")
    parser.add_argument("--theme-path", help="Explicit theme views/package path")
    parser.add_argument("--json", action="store_true", help="Emit formatted JSON")
    return parser.parse_args()


def run_parent_inspector(project_root: Path, theme_code: str | None) -> dict[str, Any]:
    parent_skill = Path(__file__).resolve().parents[3]
    inspector = parent_skill / "scripts" / "inspect_theme_environment.py"

    if not inspector.is_file():
        raise RuntimeError(f"parent environment inspector not found: {inspector}")

    command = [
        sys.executable,
        str(inspector),
        "--project-root",
        str(project_root),
        "--json",
    ]
    if theme_code:
        command.extend(["--theme-code", theme_code])

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"parent environment inspection failed: {detail}")

    return json.loads(result.stdout)


def discover_playwright_configs(project_root: Path) -> list[Path]:
    ignored = {".git", "vendor", "node_modules", "public", "storage", "build", "dist"}
    configs: list[Path] = []
    for current, directories, files in os.walk(project_root):
        directories[:] = sorted(directory for directory in directories if directory not in ignored)
        for filename in files:
            if filename.startswith("playwright.config."):
                configs.append(Path(current) / filename)
    return sorted(configs)


def nearest_package_root(config: Path, project_root: Path) -> Path:
    for candidate in config.parents:
        if (candidate / "package.json").is_file():
            return candidate
        if candidate == project_root:
            break
    return config.parent


def discover_harnesses(project_root: Path) -> list[dict[str, Any]]:
    harnesses: list[dict[str, Any]] = []
    configs = discover_playwright_configs(project_root)

    for config in configs:
        root = config.parent
        package_root = nearest_package_root(config, project_root)
        specs = sorted(root.rglob("*.spec.*"))
        feature_specs: dict[str, list[str]] = defaultdict(list)
        mutation_candidates: dict[str, list[str]] = defaultdict(list)

        for spec in specs:
            relative = spec.relative_to(project_root).as_posix()
            searchable = relative.lower()
            for feature, patterns in FEATURE_PATTERNS.items():
                if any(pattern in searchable for pattern in patterns):
                    feature_specs[feature].append(relative)
            try:
                content = spec.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = ""
            for signal, pattern in MUTATION_REVIEW_SIGNALS.items():
                if pattern.search(content):
                    mutation_candidates[signal].append(relative)

        harnesses.append(
            {
                "name": package_root.name,
                "root": root.relative_to(project_root).as_posix(),
                "config": config.relative_to(project_root).as_posix(),
                "package_json": (
                    package_root / "package.json"
                ).relative_to(project_root).as_posix()
                if (package_root / "package.json").is_file()
                else None,
                "spec_count": len(specs),
                "feature_specs": dict(sorted(feature_specs.items())),
                "mutation_review_candidates": dict(sorted(mutation_candidates.items())),
            }
        )

    return harnesses


def resolve_theme_path(
    project_root: Path,
    environment: dict[str, Any],
    theme_code: str | None,
    explicit_theme_path: str | None,
) -> Path | None:
    if explicit_theme_path:
        candidate = Path(explicit_theme_path)
        return candidate.resolve() if candidate.is_absolute() else (project_root / candidate).resolve()

    if not theme_code:
        return None

    for theme in environment.get("theme_config", {}).get("themes", []):
        if theme.get("code") != theme_code:
            continue
        view_info = theme.get("views_path") or {}
        resolved = view_info.get("resolved") or view_info.get("absolute")
        if resolved:
            return Path(resolved).resolve()

    return None


def scan_theme(theme_path: Path | None, project_root: Path) -> dict[str, Any]:
    if theme_path is None:
        return {"path": None, "exists": False, "blade_files": 0, "source_signals": {}, "review_candidates": {}}

    exists = theme_path.exists()
    files = sorted(theme_path.rglob("*.blade.php")) if exists else []
    signals: dict[str, list[str]] = defaultdict(list)
    risks: dict[str, list[str]] = defaultdict(list)

    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        try:
            display = path.relative_to(project_root).as_posix()
        except ValueError:
            display = str(path)

        for name, pattern in SOURCE_SIGNALS.items():
            if pattern.search(content):
                signals[name].append(display)
        for name, pattern in RISK_SIGNALS.items():
            if pattern.search(content):
                risks[name].append(display)

    return {
        "path": str(theme_path),
        "exists": exists,
        "blade_files": len(files),
        "source_signals": dict(sorted(signals.items())),
        "review_candidates": dict(sorted(risks.items())),
        "notice": "Signals and candidates require source tracing plus runtime proof; they are not pass/fail findings.",
    }


def discover_registered_product_types(project_root: Path) -> list[str]:
    candidates = [
        project_root / "packages/Webkul/Product/src/Config/product_types.php",
        project_root / "vendor/bagisto/bagisto/packages/Webkul/Product/src/Config/product_types.php",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        keys = re.findall(r"['\"]key['\"]\s*=>\s*['\"]([a-z0-9_-]+)['\"]", content, re.I)
        if keys:
            return sorted(set(keys))
    return []


def discover_checkout_scenarios(project_root: Path) -> list[str]:
    scenarios: set[str] = set()
    for config in discover_playwright_configs(project_root):
        for spec in config.parent.rglob("*-checkout.spec.*"):
            if "checkout" in {part.lower() for part in spec.parts}:
                scenarios.add(spec.name.split("-checkout.spec.", 1)[0])
    return sorted(scenarios)


def discover_optional_features(project_root: Path) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    package_root = project_root / "packages" / "Webkul"
    for package, feature in OPTIONAL_PACKAGE_FEATURES.items():
        if (package_root / package).exists():
            result.append({"package": package, "feature": feature})
    return result


def discover_configured_codes(project_root: Path, filenames: set[str]) -> list[str]:
    ignored = {".git", "node_modules", "public", "storage", "build", "dist"}
    codes: set[str] = set()
    for current, directories, files in os.walk(project_root):
        directories[:] = sorted(directory for directory in directories if directory not in ignored)
        for filename in files:
            if filename not in filenames:
                continue
            path = Path(current) / filename
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            codes.update(re.findall(r"['\"]code['\"]\s*=>\s*['\"]([a-z0-9_-]+)['\"]", content, re.I))
    return sorted(codes)


def build_required_journeys(product_types: list[str]) -> list[dict[str, str]]:
    base = [
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
    ]
    rows = [{"id": item, "basis": "Bagisto core storefront surface"} for item in base]

    for product_type in product_types:
        feature = f"product-{product_type}"
        if feature not in {row["id"] for row in rows}:
            rows.append({"id": feature, "basis": "Registered product type in installed configuration"})

    return rows


def inspect(project_root: Path, theme_code: str | None, theme_path: str | None) -> dict[str, Any]:
    environment = run_parent_inspector(project_root, theme_code)
    harnesses = discover_harnesses(project_root)
    product_types = discover_registered_product_types(project_root)
    checkout_scenarios = discover_checkout_scenarios(project_root)
    optional_features = discover_optional_features(project_root)
    payment_methods = discover_configured_codes(project_root, {"payment-methods.php"})
    shipping_carriers = discover_configured_codes(project_root, {"carriers.php", "shipping-methods.php"})
    resolved_theme_path = resolve_theme_path(project_root, environment, theme_code, theme_path)

    return {
        "schema_version": 1,
        "project": environment.get("project", {}),
        "project_root": str(project_root),
        "theme_code": theme_code,
        "theme": scan_theme(resolved_theme_path, project_root),
        "playwright_harnesses": harnesses,
        "registered_product_types": product_types,
        "checkout_scenarios": checkout_scenarios,
        "conditional_features": [
            {
                **item,
                "applicability": "installed-candidate; verify provider, route, channel/configuration and credentials before requiring a journey",
            }
            for item in optional_features
        ],
        "conditional_payment_methods": [
            {
                "code": code,
                "applicability": "configuration default candidate; verify effective runtime/channel enablement and sandbox safety",
            }
            for code in payment_methods
        ],
        "conditional_shipping_carriers": [
            {
                "code": code,
                "applicability": "configuration default candidate; verify effective runtime/channel enablement and address/cart eligibility",
            }
            for code in shipping_carriers
        ],
        "required_journeys": build_required_journeys(product_types),
        "warnings": [
            *environment.get("warnings", []),
            *([] if harnesses else ["No installed Playwright harness was discovered."]),
            *([] if resolved_theme_path else ["No theme path was selected; pass --theme-code or --theme-path."]),
        ],
    }


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"project root does not exist: {project_root}", file=sys.stderr)
        return 2

    try:
        report = inspect(project_root, args.theme_code, args.theme_path)
    except (RuntimeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Bagisto: {report['project'].get('bagisto_version') or 'unknown'}")
        print(f"Theme: {report['theme_code'] or report['theme']['path'] or 'not selected'}")
        print(f"Playwright harnesses: {len(report['playwright_harnesses'])}")
        print(f"Registered product types: {', '.join(report['registered_product_types']) or 'none'}")
        print(f"Checkout scenarios: {', '.join(report['checkout_scenarios']) or 'none'}")
        print(f"Payment candidates: {', '.join(item['code'] for item in report['conditional_payment_methods']) or 'none'}")
        print(f"Shipping candidates: {', '.join(item['code'] for item in report['conditional_shipping_carriers']) or 'none'}")
        print(f"Core/registered journeys: {len(report['required_journeys'])}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
