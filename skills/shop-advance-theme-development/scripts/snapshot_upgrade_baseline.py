#!/usr/bin/env python3
"""Create an accepted Shop-source hash baseline for an existing Bagisto theme."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from diff_theme_overrides import (
    ComparisonError,
    absolute_from,
    build_source_files,
    collect_files,
    digest_hex,
    load_baseline,
    locate_views_path,
    resource_package_root,
    require_shop_package,
    installed_bagisto_version,
    shop_assets_root,
    theme_source_matches_config,
)
from inspect_theme_environment import (
    ConfigParseError,
    PackageDiscoveryError,
    discover_root,
    discovered_view_root,
    find_package,
    parse_php_config,
)


THEME_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class SnapshotError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or write a no-overwrite upgrade baseline for an existing theme. "
            "The snapshot accepts the currently installed Shop sources; review and test first."
        )
    )
    parser.add_argument("--project-root", default=".", type=Path, help="Bagisto project root")
    parser.add_argument("--theme-code", required=True, help="configured theme identity")
    parser.add_argument("--theme-path", required=True, type=Path, help="theme package, root, or views directory")
    parser.add_argument(
        "--scaffold-mode",
        required=True,
        choices=("overlay", "package", "full-fork"),
        help="maintenance mode recorded in the baseline",
    )
    parser.add_argument("--upstream-views", type=Path, help="optional installed Shop package or views path")
    parser.add_argument("--output", type=Path, help="output file; defaults beside the theme source root")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the planned baseline; replacement additionally requires --refresh",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="explicitly replace a valid same-theme baseline after reviewed upgrade reconciliation",
    )
    parser.add_argument(
        "--acknowledge-reviewed",
        action="store_true",
        help="confirm current overrides and installed Shop changes were reviewed and tested",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the complete baseline JSON")
    return parser.parse_args()


def safe_output(root: Path, path: Path) -> Path:
    path = path.absolute()
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError as error:
        raise SnapshotError(f"output must stay inside the project root: {path}") from error
    current = path
    while current != root:
        if current.is_symlink():
            raise SnapshotError(f"refusing to write through symlink: {current}")
        current = current.parent
    return path


def lexical_output_path(value: Path, root: Path) -> Path:
    expanded = value.expanduser()
    return (expanded if expanded.is_absolute() else root / expanded).absolute()


def default_output_root(theme_input: Path, theme_views: Path) -> Path:
    package_root = resource_package_root(theme_views)
    if package_root:
        return package_root
    if theme_views.name == "views":
        return theme_views.parent
    if theme_input.is_dir():
        return theme_input
    raise SnapshotError("could not derive a baseline location; pass --output")


def tracked_hashes(theme_root: Path | None, upstream_root: Path | None) -> dict[str, str]:
    if theme_root is None or upstream_root is None or not theme_root.is_dir() or not upstream_root.is_dir():
        return {}
    result: dict[str, str] = {}
    for relative, theme_file in collect_files(theme_root).items():
        upstream_file = upstream_root / relative
        if theme_file.is_symlink() or upstream_file.is_symlink() or not upstream_file.is_file():
            continue
        result[relative] = digest_hex(upstream_file)
    return result


def complete_hashes(files: dict[str, Path]) -> dict[str, str]:
    return {relative: digest_hex(path) for relative, path in sorted(files.items())}


def build_source_hashes(theme_root: Path | None, shop_root: Path | None) -> dict[str, str]:
    if theme_root is None or shop_root is None:
        return {}
    result: dict[str, str] = {}
    for relative, shop_file in sorted(build_source_files(shop_root).items()):
        theme_file = theme_root / relative
        if theme_file.is_file() and not theme_file.is_symlink() and shop_file.is_file() and not shop_file.is_symlink():
            result[relative] = digest_hex(shop_file)
    return result


def snapshot_document(
    root: Path,
    theme_code: str,
    mode: str,
    theme_views: Path,
    upstream_views: Path,
    package_assets_directory: str,
) -> dict[str, Any]:
    theme_package = resource_package_root(theme_views)
    shop_package = require_shop_package(upstream_views)
    theme_assets = theme_package / package_assets_directory if theme_package else None
    shop_assets = shop_assets_root(shop_package)
    bagisto_release = installed_bagisto_version(shop_package)
    if not bagisto_release:
        raise SnapshotError(
            "cannot accept a baseline because the installed Bagisto version is unavailable"
        )
    try:
        shop_source = str(shop_package.relative_to(root)) if shop_package else None
    except ValueError:
        shop_source = None
    return {
        "schema_version": 1,
        "theme_code": theme_code,
        "scaffold_mode": mode,
        "shop": {
            "composer_name": "bagisto/laravel-shop",
            "bagisto_version": bagisto_release,
            "assets_directory": shop_assets.relative_to(shop_package).as_posix(),
            "source_path": shop_source,
        },
        "theme": {
            "package_assets_directory": package_assets_directory,
        },
        "views": tracked_hashes(theme_views, upstream_views),
        "assets": tracked_hashes(theme_assets, shop_assets),
        "build_sources": build_source_hashes(theme_package, shop_package),
        "shop_inventory": {
            "views": complete_hashes(collect_files(upstream_views)),
            "assets": complete_hashes(collect_files(shop_assets)),
            "build_sources": complete_hashes(build_source_files(shop_package)),
        },
    }


def required_ownership_gaps(document: dict[str, Any]) -> dict[str, list[str]]:
    required = {
        "overlay": (),
        "package": ("assets", "build_sources"),
        "full-fork": ("views", "assets", "build_sources"),
    }[document["scaffold_mode"]]
    return {
        section: sorted(set(document["shop_inventory"][section]) - set(document[section]))
        for section in required
        if set(document["shop_inventory"][section]) - set(document[section])
    }


def main() -> int:
    args = parse_args()
    try:
        if not THEME_CODE_RE.fullmatch(args.theme_code):
            raise SnapshotError("--theme-code must match [a-z][a-z0-9-]*")
        if args.apply and not args.acknowledge_reviewed:
            raise SnapshotError("--apply requires --acknowledge-reviewed")
        root = discover_root(args.project_root, search_parents=True)
        if root is None:
            raise SnapshotError(f"no Bagisto project root found from {args.project_root}")
        try:
            configured = parse_php_config(root / "config/themes.php").get("shop", {})
        except ConfigParseError as error:
            raise SnapshotError(f"could not parse config/themes.php safely: {error}") from error
        if not isinstance(configured, dict) or args.theme_code not in configured:
            raise SnapshotError(f"shop theme is not configured: {args.theme_code}")
        theme_input = absolute_from(args.theme_path, root)
        theme_views = locate_views_path(args.theme_path, root, "theme path")
        try:
            theme_views.relative_to(root)
        except ValueError as error:
            raise SnapshotError("theme source must stay inside the project root") from error
        theme_config = configured[args.theme_code]
        if not isinstance(theme_config, dict) or not theme_source_matches_config(
            root,
            args.theme_code,
            theme_views,
        ):
            raise SnapshotError(
                f"theme source does not match configured theme {args.theme_code!r}: {theme_views}"
            )
        vite_config = theme_config.get("vite")
        package_assets_directory = (
            vite_config.get("package_assets_directory")
            if isinstance(vite_config, dict)
            else None
        )
        package_assets_path = Path(str(package_assets_directory))
        if (
            not isinstance(package_assets_directory, str)
            or package_assets_path.is_absolute()
            or not package_assets_path.parts
            or ".." in package_assets_path.parts
        ):
            raise SnapshotError("configured package_assets_directory is missing or unsafe")
        detected_theme_package = resource_package_root(theme_views)
        if args.scaffold_mode == "overlay" and detected_theme_package is not None:
            raise SnapshotError("overlay mode requires a resource view tree, not a package-shaped source")
        if args.scaffold_mode != "overlay" and detected_theme_package is None:
            raise SnapshotError(
                f"{args.scaffold_mode} mode requires a package-shaped theme source"
            )
        shop = find_package(root, "bagisto/laravel-shop")
        if shop is None:
            raise SnapshotError("installed bagisto/laravel-shop package was not found")
        installed_views = discovered_view_root(shop[0])
        if installed_views is None:
            raise SnapshotError("installed Shop package has no unique discovered Blade view root")
        require_shop_package(installed_views)
        shop_assets_root(shop[0])
        if args.upstream_views:
            upstream_views = locate_views_path(args.upstream_views, root, "upstream path")
            if upstream_views.resolve() != installed_views.resolve():
                raise SnapshotError("--upstream-views must resolve to the installed bagisto/laravel-shop source")
        else:
            upstream_views = installed_views

        document = snapshot_document(
            root,
            args.theme_code,
            args.scaffold_mode,
            theme_views,
            upstream_views,
            package_assets_directory,
        )
        ownership_gaps = required_ownership_gaps(document)
        if ownership_gaps:
            details = "; ".join(
                f"{section}: {', '.join(paths[:5])}"
                + (f" (+{len(paths) - 5} more)" if len(paths) > 5 else "")
                for section, paths in ownership_gaps.items()
            )
            raise SnapshotError(
                f"theme source is incomplete for scaffold mode {args.scaffold_mode!r}: {details}"
            )
        base = default_output_root(theme_input, theme_views)
        output = safe_output(
            root,
            lexical_output_path(args.output, root)
            if args.output
            else base / ".bagisto-theme-baseline.json",
        )
        content = json.dumps(document, indent=2, sort_keys=True) + "\n"
        state = "create"
        if output.exists():
            if output.is_symlink() or not output.is_file():
                state = "conflict"
            elif output.read_text(encoding="utf-8") == content:
                state = "unchanged"
            else:
                state = "conflict"
        if state == "conflict":
            if not args.refresh:
                raise SnapshotError(f"refusing to replace existing baseline without --refresh: {output}")
            try:
                current = load_baseline(output)
            except ComparisonError as error:
                raise SnapshotError(f"refusing to refresh invalid baseline: {error}") from error
            if (
                current.get("theme_code") != args.theme_code
                or current["shop"].get("composer_name") != "bagisto/laravel-shop"
            ):
                raise SnapshotError(
                    "refusing to refresh a baseline with another schema, theme, or Shop identity"
                )
            state = "refresh"
        if args.apply and state in {"create", "refresh"}:
            output.parent.mkdir(parents=True, exist_ok=True)
            safe_output(root, output)
            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=output.parent,
                    prefix=".bagisto-theme-baseline.",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                    temporary = Path(handle.name)
                os.replace(temporary, output)
                temporary = None
            finally:
                if temporary and temporary.exists():
                    temporary.unlink()

        payload = {
            "output": str(output),
            "state": state,
            "applied": args.apply,
            "counts": {
                "theme_owned": {
                    key: len(document[key]) for key in ("views", "assets", "build_sources")
                },
                "shop_inventory": {
                    key: len(document["shop_inventory"][key])
                    for key in ("views", "assets", "build_sources")
                },
            },
            "baseline": document if args.as_json else None,
        }
        if args.as_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Baseline: {output}")
            print(f"State: {state}; {'applied' if args.apply else 'dry-run'}")
            print(
                "Theme-owned sources: "
                f"{len(document['views'])} views, "
                f"{len(document['assets'])} assets, "
                f"{len(document['build_sources'])} build sources"
            )
            print(
                "Shop inventory: "
                f"{len(document['shop_inventory']['views'])} views, "
                f"{len(document['shop_inventory']['assets'])} assets, "
                f"{len(document['shop_inventory']['build_sources'])} build sources"
            )
            print("Accept this snapshot only after override review and all applicable tests pass.")
        return 0
    except (
        SnapshotError,
        ComparisonError,
        PackageDiscoveryError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        if args.as_json:
            print(json.dumps({"schema_version": 1, "error": str(error)}, indent=2))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
