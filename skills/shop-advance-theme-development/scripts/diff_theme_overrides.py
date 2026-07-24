#!/usr/bin/env python3
"""Classify a Bagisto theme's view files against the installed Shop package.

The comparison is byte-for-byte and read-only.  Theme and project names are
always supplied or discovered; none are embedded in the script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from inspect_theme_environment import (
    ConfigParseError,
    EXIT_INVALID,
    EXIT_NOT_FOUND,
    JavaScriptScanError,
    PackageDiscoveryError,
    discover_root,
    discovered_view_root,
    find_package,
    installed_package_records,
    installed_version,
    javascript_module_specifiers,
    literal_vite_input_files,
    literal_vite_assets_root,
    package_is_registered,
    parse_php_config,
    strip_php_comments,
)


EXIT_DIFFERENCES = 1
EXIT_OK = 0


class ComparisonError(ValueError):
    """Raised when a requested view tree cannot be selected safely."""


def absolute_from(path: Path, base: Path) -> Path:
    expanded = path.expanduser()
    return (expanded if expanded.is_absolute() else base / expanded).resolve(strict=False)


def locate_views_path(value: Path, base: Path, label: str) -> Path:
    """Accept either a package root, a theme root, or the views directory itself."""
    path = absolute_from(value, base)
    if not path.exists():
        raise ComparisonError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise ComparisonError(f"{label} is not a directory: {path}")

    candidates = (
        path / "src" / "Resources" / "views",
        path / "Resources" / "views",
        path / "resources" / "views",
        path / "views",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve(strict=False)
    return path


def configured_theme_views(root: Path, code: str) -> Path:
    config_path = root / "config" / "themes.php"
    if not config_path.is_file():
        raise ComparisonError(f"theme config was not found: {config_path}")
    try:
        config = parse_php_config(config_path)
    except ConfigParseError as error:
        raise ComparisonError(f"could not parse config/themes.php safely: {error}") from error

    shop = config.get("shop", {})
    if not isinstance(shop, dict) or code not in shop:
        available = sorted(str(key) for key in shop) if isinstance(shop, dict) else []
        suffix = f" (available: {', '.join(available)})" if available else ""
        raise ComparisonError(f"shop theme {code!r} is not configured{suffix}")
    theme = shop[code]
    if not isinstance(theme, dict) or not isinstance(theme.get("views_path"), str):
        raise ComparisonError(f"shop theme {code!r} has no literal views_path")
    return locate_views_path(Path(theme["views_path"]), root, f"views for theme {code!r}")


def collect_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for directory, directories, filenames in os.walk(root, followlinks=False):
        directories.sort()
        filenames.sort()
        base = Path(directory)
        for filename in filenames:
            path = base / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            files[relative] = path
    return files


def digest(path: Path) -> bytes:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.digest()


def digest_hex(path: Path) -> str:
    return digest(path).hex()


def baseline_path(value: Path | None, theme_views: Path, base: Path) -> Path | None:
    if value is not None:
        candidate = absolute_from(value, base)
        if candidate.is_dir():
            candidate = candidate / ".bagisto-theme-baseline.json"
        if not candidate.is_file():
            raise ComparisonError(f"baseline does not exist: {candidate}")
        return candidate

    package_root = resource_package_root(theme_views)
    candidates = (
        (package_root / ".bagisto-theme-baseline.json",)
        if package_root
        else (
            theme_views / ".bagisto-theme-baseline.json",
            theme_views.parent / ".bagisto-theme-baseline.json",
        )
    )
    matches = [candidate for candidate in candidates if candidate.is_file()]
    if len(matches) > 1:
        raise ComparisonError(
            "multiple auto-discovered baselines exist for this theme source: "
            + ", ".join(str(path) for path in matches)
        )
    return matches[0] if matches else None


def validate_hash_map(values: Any, label: str) -> dict[str, str]:
    if not isinstance(values, dict):
        raise ComparisonError(f"baseline {label} must be an object")
    for relative, checksum in values.items():
        path_value = Path(str(relative))
        if (
            not isinstance(relative, str)
            or path_value.is_absolute()
            or not path_value.parts
            or ".." in path_value.parts
            or any(ord(character) < 32 or ord(character) == 127 for character in relative)
            or not isinstance(checksum, str)
            or not re.fullmatch(r"[0-9a-f]{64}", checksum)
        ):
            raise ComparisonError(f"unsafe or invalid baseline entry in {label}: {relative!r}")
    return values


def load_baseline(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ComparisonError(f"invalid baseline JSON: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ComparisonError("baseline must be an object with schema_version 1")
    if not isinstance(data.get("theme_code"), str) or not re.fullmatch(r"[a-z][a-z0-9-]*", data["theme_code"]):
        raise ComparisonError("baseline theme_code is missing or invalid")
    if data.get("scaffold_mode") not in {"overlay", "package", "full-fork"}:
        raise ComparisonError("baseline scaffold_mode must be overlay, package, or full-fork")
    shop = data.get("shop")
    if not isinstance(shop, dict) or shop.get("composer_name") != "bagisto/laravel-shop":
        raise ComparisonError("baseline shop identity must be bagisto/laravel-shop")
    if shop.get("bagisto_version") is not None and (
        not isinstance(shop["bagisto_version"], str) or not shop["bagisto_version"].strip()
    ):
        raise ComparisonError("baseline shop bagisto_version must be a non-empty string or null")
    assets_directory = shop.get("assets_directory")
    assets_path = Path(str(assets_directory))
    if (
        not isinstance(assets_directory, str)
        or assets_path.is_absolute()
        or not assets_path.parts
        or ".." in assets_path.parts
    ):
        raise ComparisonError("baseline shop assets_directory is missing or unsafe")
    theme = data.get("theme")
    package_assets_directory = theme.get("package_assets_directory") if isinstance(theme, dict) else None
    package_assets_path = Path(str(package_assets_directory))
    if (
        not isinstance(package_assets_directory, str)
        or package_assets_path.is_absolute()
        or not package_assets_path.parts
        or ".." in package_assets_path.parts
    ):
        raise ComparisonError("baseline theme package_assets_directory is missing or unsafe")
    for section in ("views", "assets", "build_sources"):
        validate_hash_map(data.get(section), section)
    inventory = data.get("shop_inventory")
    if not isinstance(inventory, dict):
        raise ComparisonError("baseline shop_inventory must be an object")
    for section in ("views", "assets", "build_sources"):
        inventory_entries = validate_hash_map(inventory.get(section), f"shop_inventory/{section}")
        tracked_entries = data[section]
        invalid = [
            relative
            for relative, checksum in tracked_entries.items()
            if inventory_entries.get(relative) != checksum
        ]
        if invalid:
            raise ComparisonError(
                f"baseline {section} entries do not match the Shop inventory: "
                + ", ".join(sorted(invalid)[:10])
            )
    return data


def resource_package_root(views: Path) -> Path | None:
    views = views.resolve()
    if views.name == "views" and views.parent.name == "Resources" and views.parent.parent.name == "src":
        return views.parent.parent.parent
    if views.name == "views" and views.parent.name in {"Resources", "resources"}:
        return views.parent.parent
    for parent in views.parents:
        composer_path = parent / "composer.json"
        if not composer_path.is_file() or not (parent / "src/Providers").is_dir():
            continue
        try:
            composer = json.loads(composer_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(composer, dict) and composer.get("name") not in {None, "bagisto/bagisto"}:
            return parent
    return None


def require_shop_package(upstream_views: Path) -> Path:
    package_root = resource_package_root(upstream_views)
    if package_root is None:
        raise ComparisonError("baseline audit requires an installed Shop package-shaped upstream")
    composer_path = package_root / "composer.json"
    if not composer_path.is_file():
        raise ComparisonError(f"upstream package has no composer.json: {package_root}")
    try:
        composer = json.loads(composer_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ComparisonError(f"invalid upstream composer.json: {error}") from error
    composer_name = composer.get("name") if isinstance(composer, dict) else None
    if composer_name != "bagisto/laravel-shop":
        raise ComparisonError(
            f"baseline upstream must be bagisto/laravel-shop, found {composer_name!r}"
        )
    expected_views = discovered_view_root(package_root)
    if (
        expected_views is None
        or upstream_views.resolve() != expected_views.resolve()
        or not collect_files(expected_views)
    ):
        raise ComparisonError(
            "installed bagisto/laravel-shop must provide one non-empty discovered Blade view root"
        )
    return package_root


def build_source_files(package_root: Path) -> dict[str, Path]:
    package_root = package_root.resolve()
    javascript_suffixes = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"}
    files: dict[str, Path] = {}
    package_json = package_root / "package.json"
    if package_json.is_file() and not package_json.is_symlink():
        files[package_json.relative_to(package_root).as_posix()] = package_json
    for pattern in (
        "vite.config.*",
        "tailwind.config.*",
        "postcss.config.*",
        "browserslist.config.*",
        ".browserslistrc",
    ):
        for path in sorted(package_root.glob(pattern)):
            if path.is_file() and not path.is_symlink():
                files[path.relative_to(package_root).as_posix()] = path

    def local_module(source_path: Path, specifier: str) -> Path | None:
        if not specifier.startswith("."):
            return None
        clean_specifier = specifier.split("?", 1)[0].split("#", 1)[0]
        unresolved = source_path.parent / clean_specifier
        choices = [unresolved]
        if not unresolved.suffix:
            choices.extend(
                unresolved.with_suffix(suffix)
                for suffix in (*sorted(javascript_suffixes), ".json")
            )
            choices.extend(
                unresolved / f"index{suffix}"
                for suffix in (*sorted(javascript_suffixes), ".json")
            )
        for choice in choices:
            candidate = choice.resolve(strict=False)
            try:
                candidate.relative_to(package_root)
            except ValueError:
                continue
            if candidate.is_file() and not candidate.is_symlink():
                return candidate
        return None

    if package_json.is_file():
        try:
            package_data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package_data = {}
        scripts = package_data.get("scripts", {}) if isinstance(package_data, dict) else {}
        for command in scripts.values() if isinstance(scripts, dict) else ():
            if not isinstance(command, str):
                continue
            try:
                command_tokens = shlex.split(command, posix=True)
            except ValueError as error:
                raise ComparisonError(f"could not parse package.json build script safely: {error}") from error
            for token in command_tokens:
                path_token = token.split("=", 1)[1] if token.startswith("-") and "=" in token else token
                path_token = path_token.rstrip(";")
                path_value = Path(path_token)
                if (
                    path_value.is_absolute()
                    or not path_value.parts
                    or ".." in path_value.parts
                    or path_value.suffix.lower() not in javascript_suffixes | {".json"}
                ):
                    continue
                candidate = (package_root / path_value).resolve(strict=False)
                try:
                    candidate.relative_to(package_root)
                except ValueError:
                    continue
                if candidate.is_file() and not candidate.is_symlink():
                    files[candidate.relative_to(package_root).as_posix()] = candidate

    queue = [
        path
        for path in files.values()
        if path.suffix.lower() in javascript_suffixes
    ]
    inspected: set[Path] = set()
    while queue:
        source_path = queue.pop()
        if source_path in inspected:
            continue
        inspected.add(source_path)
        source = source_path.read_text(encoding="utf-8", errors="ignore")
        try:
            specifiers = javascript_module_specifiers(source)
        except JavaScriptScanError as error:
            relative_source = source_path.relative_to(package_root).as_posix()
            raise ComparisonError(
                f"could not complete JavaScript build-contract scan for {relative_source}: {error}"
            ) from error
        for specifier in specifiers:
            candidate = local_module(source_path, specifier)
            if candidate is None:
                continue
            relative = candidate.relative_to(package_root).as_posix()
            if relative not in files:
                files[relative] = candidate
                if candidate.suffix.lower() in javascript_suffixes:
                    queue.append(candidate)
    return files


def installed_bagisto_version(shop_package: Path) -> str | None:
    candidates = (
        shop_package.parent / "Core/src/Core.php",
        shop_package.parent / "laravel-core/src/Core.php",
    )
    for candidate in candidates:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        source = candidate.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"\bBAGISTO_VERSION\s*=\s*['\"]([^'\"]+)['\"]", source)
        if match:
            return match.group(1)
    root = discover_root(shop_package, search_parents=True)
    if root is not None:
        return installed_version(root, "bagisto/laravel-core") or installed_version(
            root,
            "bagisto/laravel-shop",
        )
    return None


def shop_assets_root(shop_package: Path) -> Path:
    """Derive the installed Shop source-asset root from literal existing Vite inputs."""
    package = shop_package.resolve()
    entries = set(literal_vite_input_files(package))
    common = literal_vite_assets_root(package)
    if not entries or common is None:
        raise ComparisonError(
            f"could not derive Shop assets from literal existing Vite inputs under {shop_package}"
        )
    return common


def inventory_files(section: str, shop_package: Path) -> dict[str, Path]:
    if section == "views":
        views = discovered_view_root(shop_package)
        if views is None:
            raise ComparisonError("installed Shop package has no unique discovered Blade view root")
        return collect_files(views)
    if section == "assets":
        return collect_files(shop_assets_root(shop_package))
    return build_source_files(shop_package)


def registered_namespace_roots(root: Path, namespace: str, current: Path | None) -> set[Path]:
    candidates: set[Path] = {current.resolve()} if current is not None else set()
    candidates.update(path.parent.resolve() for path in root.glob("packages/*/*/composer.json"))
    for record in installed_package_records(root):
        install_path = record.get("install_path")
        if isinstance(install_path, str):
            candidates.add((root / "vendor/composer" / install_path).resolve())

    matches: set[Path] = set()
    pattern = re.compile(
        rf"loadViewsFrom\s*\([^;]*['\"]{re.escape(namespace)}['\"]\s*\)",
        flags=re.S,
    )
    for candidate in candidates:
        providers = candidate / "src/Providers"
        if not providers.is_dir() or not package_is_registered(root, candidate):
            continue
        provider_text = "\n".join(
            strip_php_comments(path.read_text(encoding="utf-8", errors="ignore"))
            for path in sorted(providers.glob("*ServiceProvider.php"))
        )
        if pattern.search(provider_text):
            matches.add(candidate)
    return matches


def theme_source_matches_config(root: Path, theme_code: str, theme_views: Path) -> bool:
    config_path = root / "config/themes.php"
    try:
        configured = parse_php_config(config_path).get("shop", {})
    except ConfigParseError as error:
        raise ComparisonError(f"could not parse config/themes.php safely: {error}") from error
    if not isinstance(configured, dict) or theme_code not in configured:
        raise ComparisonError(f"shop theme is not configured: {theme_code}")
    theme = configured[theme_code]
    if not isinstance(theme, dict):
        raise ComparisonError(f"shop theme configuration is not an object: {theme_code}")

    configured_path = theme.get("views_path")
    configured_path_matches = False
    if isinstance(configured_path, str):
        path = Path(configured_path)
        path = path if path.is_absolute() else root / path
        if path.exists() and path.resolve() == theme_views.resolve():
            configured_path_matches = True

    package_root = resource_package_root(theme_views)
    namespace = theme.get("views_namespace")
    namespace_roots: set[Path] = set()
    if isinstance(namespace, str) and namespace:
        namespace_roots = registered_namespace_roots(root, namespace, package_root)
        if len(namespace_roots) > 1:
            rendered = ", ".join(str(path) for path in sorted(namespace_roots))
            raise ComparisonError(
                f"configured view namespace {namespace!r} is registered by multiple packages: {rendered}"
            )
        return bool(
            package_root is not None
            and len(namespace_roots) == 1
            and package_root.resolve() in namespace_roots
        )
    if configured_path_matches:
        return True
    if package_root is None or not package_is_registered(root, package_root):
        return False
    providers = package_root / "src/Providers"
    provider_text = "\n".join(
        strip_php_comments(path.read_text(encoding="utf-8", errors="ignore"))
        for path in sorted(providers.glob("*ServiceProvider.php"))
    ) if providers.is_dir() else ""
    if isinstance(configured_path, str) and "publishes" in provider_text:
        configured_destination = Path(configured_path)
        configured_destination = (
            configured_destination
            if configured_destination.is_absolute()
            else root / configured_destination
        )
        if not configured_destination.is_dir():
            return False
        normalized = PurePosixPath(configured_path.replace("\\", "/")).as_posix()
        candidates = {normalized, normalized.removeprefix("resources/")}
        if any(candidate and candidate in provider_text.replace("\\", "/") for candidate in candidates):
            return True
    return False


def hash_if_file(root: Path | None, relative: str) -> str | None:
    if root is None:
        return None
    path = root / relative
    if path.is_symlink() or not path.is_file():
        return None
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return digest_hex(path)


def analyze_baseline_section(
    entries: dict[str, str],
    theme_root: Path | None,
    upstream_root: Path | None,
    theme_files: dict[str, Path],
    upstream_files: dict[str, Path],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tracked": len(entries),
        "upstream_changed": [],
        "theme_changed": [],
        "concurrent_changes": [],
        "upstream_missing": [],
        "theme_missing": [],
        "theme_untracked": sorted((set(theme_files) & set(upstream_files)) - set(entries)),
    }
    for relative, original_hash in sorted(entries.items()):
        upstream_hash = hash_if_file(upstream_root, relative)
        theme_hash = hash_if_file(theme_root, relative)
        if upstream_hash is None:
            result["upstream_missing"].append(relative)
        elif upstream_hash != original_hash:
            result["upstream_changed"].append(relative)
        if theme_hash is None:
            result["theme_missing"].append(relative)
        elif theme_hash != original_hash:
            result["theme_changed"].append(relative)
        if (
            upstream_hash is not None
            and theme_hash is not None
            and upstream_hash != original_hash
            and theme_hash != original_hash
            and upstream_hash != theme_hash
        ):
            result["concurrent_changes"].append(relative)
    return result


def analyze_inventory_section(entries: dict[str, str], current_files: dict[str, Path]) -> dict[str, Any]:
    baseline_names = set(entries)
    current_names = set(current_files)
    changed = [
        relative
        for relative in sorted(baseline_names & current_names)
        if digest_hex(current_files[relative]) != entries[relative]
    ]
    return {
        "tracked": len(entries),
        "upstream_changed": changed,
        "upstream_missing": sorted(baseline_names - current_names),
        "upstream_added": sorted(current_names - baseline_names),
    }


def analyze_baseline(
    path: Path,
    theme_views: Path,
    upstream_views: Path,
    expected_theme_code: str | None = None,
) -> dict[str, Any]:
    data = load_baseline(path)
    baseline_code = data["theme_code"]
    if expected_theme_code and baseline_code != expected_theme_code:
        raise ComparisonError(
            f"baseline belongs to theme {baseline_code!r}, not {expected_theme_code!r}"
        )
    detected_theme_package = resource_package_root(theme_views)
    if data["scaffold_mode"] == "overlay" and detected_theme_package is not None:
        raise ComparisonError("overlay baseline is bound to a package-shaped theme source")
    if data["scaffold_mode"] != "overlay" and detected_theme_package is None:
        raise ComparisonError(
            f"{data['scaffold_mode']} baseline requires a package-shaped theme source"
        )
    theme_root = detected_theme_package or theme_views.parent
    package_assets_path = Path(data["theme"]["package_assets_directory"])
    upstream_package = require_shop_package(upstream_views)
    theme_assets = next(
        (candidate for candidate in (theme_root / package_assets_path,) if candidate.is_dir()),
        None,
    )
    upstream_assets = shop_assets_root(upstream_package)
    installed_assets_directory = upstream_assets.relative_to(upstream_package).as_posix()
    theme_file_maps = {
        "views": collect_files(theme_views),
        "assets": collect_files(theme_assets) if theme_assets else {},
        "build_sources": build_source_files(theme_root),
    }
    upstream_file_maps = {
        section: inventory_files(section, upstream_package)
        for section in ("views", "assets", "build_sources")
    }
    sections = {
        "views": analyze_baseline_section(
            data["views"],
            theme_views,
            upstream_views,
            theme_file_maps["views"],
            upstream_file_maps["views"],
        ),
        "assets": analyze_baseline_section(
            data["assets"],
            theme_assets,
            upstream_assets,
            theme_file_maps["assets"],
            upstream_file_maps["assets"],
        ),
        "build_sources": analyze_baseline_section(
            data["build_sources"],
            theme_root,
            upstream_package,
            theme_file_maps["build_sources"],
            upstream_file_maps["build_sources"],
        ),
    }
    inventory_sections = {
        section: analyze_inventory_section(
            data["shop_inventory"][section],
            upstream_file_maps[section],
        )
        for section in ("views", "assets", "build_sources")
    }
    required_ownership = {
        "overlay": (),
        "package": ("assets", "build_sources"),
        "full-fork": ("views", "assets", "build_sources"),
    }[data["scaffold_mode"]]
    ownership_missing = {
        section: sorted(set(data["shop_inventory"][section]) - set(data[section]))
        for section in required_ownership
    }
    baseline_version = data["shop"].get("bagisto_version")
    current_version = installed_bagisto_version(upstream_package)
    version_changed = bool(
        baseline_version
        and current_version
        and baseline_version != current_version
    )
    version_unverifiable = not baseline_version or not current_version
    asset_topology_changed = data["shop"]["assets_directory"] != installed_assets_directory
    return {
        "path": str(path),
        "theme_code": data.get("theme_code"),
        "scaffold_mode": data.get("scaffold_mode"),
        "shop": data.get("shop", {}),
        "summary": {
            "upstream_changed": sum(len(section["upstream_changed"]) for section in inventory_sections.values()),
            "upstream_missing": sum(len(section["upstream_missing"]) for section in inventory_sections.values()),
            "upstream_added": sum(len(section["upstream_added"]) for section in inventory_sections.values()),
            "theme_changed": sum(len(section["theme_changed"]) for section in sections.values()),
            "concurrent_changes": sum(len(section["concurrent_changes"]) for section in sections.values()),
            "theme_missing": sum(len(section["theme_missing"]) for section in sections.values()),
            "theme_untracked": sum(len(section["theme_untracked"]) for section in sections.values()),
            "ownership_missing": sum(len(paths) for paths in ownership_missing.values()),
            "version_changed": int(version_changed),
            "version_unverifiable": int(version_unverifiable),
            "asset_topology_changed": int(asset_topology_changed),
        },
        "sections": sections,
        "shop_inventory": inventory_sections,
        "ownership_missing": ownership_missing,
        "versions": {
            "baseline": baseline_version,
            "installed": current_version,
        },
        "asset_directories": {
            "baseline": data["shop"]["assets_directory"],
            "installed": installed_assets_directory,
        },
    }


def compare(theme_views: Path, upstream_views: Path) -> dict[str, list[str]]:
    theme_files = collect_files(theme_views)
    upstream_files = collect_files(upstream_views)
    theme_names = set(theme_files)
    upstream_names = set(upstream_files)
    common = sorted(theme_names & upstream_names)

    identical: list[str] = []
    modified: list[str] = []
    for relative in common:
        theme_path = theme_files[relative]
        upstream_path = upstream_files[relative]
        if theme_path.stat().st_size == upstream_path.stat().st_size and digest(theme_path) == digest(upstream_path):
            identical.append(relative)
        else:
            modified.append(relative)

    return {
        "identical": identical,
        "modified": modified,
        "theme_only": sorted(theme_names - upstream_names),
        "upstream_only": sorted(upstream_names - theme_names),
    }


def failure_requested(
    fail_on: str,
    files: dict[str, list[str]],
    baseline: dict[str, Any] | None,
) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "baseline-drift":
        return not baseline or bool(
            baseline["summary"]["upstream_changed"]
            or baseline["summary"]["upstream_missing"]
            or baseline["summary"]["upstream_added"]
            or baseline["summary"]["theme_missing"]
            or baseline["summary"]["theme_untracked"]
            or baseline["summary"]["ownership_missing"]
            or baseline["summary"]["version_changed"]
            or baseline["summary"]["version_unverifiable"]
            or baseline["summary"]["asset_topology_changed"]
        )
    if fail_on == "baseline-conflict":
        return bool(baseline and baseline["summary"]["concurrent_changes"])
    if fail_on == "non-identical":
        return any(files[name] for name in ("modified", "theme_only", "upstream_only"))
    return bool(files[fail_on.replace("-", "_")])


def result_document(
    root: Path | None,
    selector_type: str,
    selector_value: str,
    theme_views: Path,
    upstream_views: Path,
    files: dict[str, list[str]],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "project_root": str(root) if root else None,
        "selector": {"type": selector_type, "value": selector_value},
        "theme_views": str(theme_views),
        "upstream_views": str(upstream_views),
        "summary": {name: len(paths) for name, paths in files.items()},
        "files": files,
        "baseline": baseline,
    }


def print_paths(title: str, paths: list[str]) -> None:
    print(f"\n{title} ({len(paths)})")
    if paths:
        for path in paths:
            print(f"  {path}")
    else:
        print("  none")


def print_human(result: dict[str, Any], show_all: bool) -> None:
    print("Bagisto theme view comparison")
    print(f"  Theme views:    {result['theme_views']}")
    print(f"  Upstream views: {result['upstream_views']}")
    summary = result["summary"]
    print("\nClassification")
    print(f"  Identical overrides: {summary['identical']}")
    print(f"  Modified overrides:  {summary['modified']}")
    print(f"  Theme-only files:    {summary['theme_only']}")
    print(f"  Upstream-only files: {summary['upstream_only']} (inherited by sparse themes)")

    files = result["files"]
    print_paths("Modified overrides", files["modified"])
    print_paths("Theme-only files", files["theme_only"])
    if show_all:
        print_paths("Identical overrides", files["identical"])
        print_paths("Upstream-only files", files["upstream_only"])
    elif summary["identical"] or summary["upstream_only"]:
        print("\nUse --show-all to list identical overrides and inherited upstream files.")

    baseline = result.get("baseline")
    if not baseline:
        print("\nUpgrade baseline: not found")
        return

    baseline_summary = baseline["summary"]
    print(f"\nUpgrade baseline: {baseline['path']}")
    print(f"  Upstream changed:   {baseline_summary['upstream_changed']}")
    print(f"  Upstream removed:   {baseline_summary['upstream_missing']}")
    print(f"  Upstream added:     {baseline_summary['upstream_added']}")
    print(f"  Theme differs:      {baseline_summary['theme_changed']} (expected for maintained customizations)")
    print(f"  Concurrent changes: {baseline_summary['concurrent_changes']} (manual reconciliation risk)")
    print(f"  Theme removed:      {baseline_summary['theme_missing']}")
    print(f"  Theme untracked:    {baseline_summary['theme_untracked']}")
    print(f"  Required unowned:   {baseline_summary['ownership_missing']}")
    if baseline_summary["version_changed"]:
        print(
            "  Bagisto version:    "
            f"{baseline['versions']['baseline']} -> {baseline['versions']['installed']}"
        )
    if baseline_summary["version_unverifiable"]:
        print(
            "  Bagisto version:    comparison unavailable "
            f"({baseline['versions']['baseline']} -> {baseline['versions']['installed']})"
        )
    if baseline_summary["asset_topology_changed"]:
        print(
            "  Shop asset root:    "
            f"{baseline['asset_directories']['baseline']} -> "
            f"{baseline['asset_directories']['installed']}"
        )
    if show_all:
        for section_name, section in baseline["sections"].items():
            for classification in (
                "upstream_changed",
                "upstream_missing",
                "concurrent_changes",
                "theme_missing",
                "theme_untracked",
            ):
                print_paths(
                    f"Baseline {section_name}: {classification.replace('_', ' ')}",
                    section[classification],
                )
        for section_name, section in baseline["shop_inventory"].items():
            for classification in ("upstream_changed", "upstream_missing", "upstream_added"):
                print_paths(
                    f"Shop inventory {section_name}: {classification.replace('_', ' ')}",
                    section[classification],
                )
        for section_name, paths in baseline["ownership_missing"].items():
            print_paths(f"Required ownership {section_name}: missing", paths)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a configured Bagisto shop theme, a theme views directory, or a theme "
            "package against the installed bagisto/laravel-shop views. Files are classified "
            "as identical, modified, theme-only, or upstream-only. When a scaffold baseline "
            "is available, also detect upstream drift and concurrent edits. Nothing is changed."
        )
    )
    parser.add_argument(
        "--root",
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Bagisto root or a path below it (default: current directory)",
    )
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--theme", "--theme-code", metavar="CODE", help="configured shop theme code")
    selector.add_argument(
        "--theme-path",
        "--theme-views",
        "--theme-package",
        dest="theme_path",
        type=Path,
        metavar="PATH",
        help="theme package root, theme root, or views directory",
    )
    parser.add_argument(
        "--upstream-views",
        type=Path,
        help="Shop package root or views directory; otherwise discover the installed package",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="baseline JSON or containing directory; otherwise discover it at the exact theme source root",
    )
    parser.add_argument(
        "--expected-theme-code",
        help="bind a path-selected source and baseline to this configured theme identity",
    )
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit machine-readable JSON")
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="list identical and upstream-only files in human output (JSON always includes them)",
    )
    parser.add_argument(
        "--fail-on",
        choices=(
            "none",
            "modified",
            "theme-only",
            "upstream-only",
            "non-identical",
            "baseline-drift",
            "baseline-conflict",
        ),
        default="none",
        help="return status 1 when selected differences exist; baseline-drift also fails when no baseline exists",
    )
    parser.add_argument(
        "--no-parent-search",
        action="store_true",
        help="require --root itself to be the Bagisto root",
    )
    return parser


def emit_error(message: str, as_json: bool, status: int) -> int:
    if as_json:
        print(json.dumps({"schema_version": 1, "error": message}, indent=2))
    else:
        print(f"error: {message}", file=sys.stderr)
    return status


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.expected_theme_code and not re.fullmatch(r"[a-z][a-z0-9-]*", args.expected_theme_code):
        return emit_error("--expected-theme-code must match [a-z][a-z0-9-]*", args.as_json, EXIT_INVALID)
    if args.theme and args.expected_theme_code and args.theme != args.expected_theme_code:
        return emit_error("--theme and --expected-theme-code disagree", args.as_json, EXIT_INVALID)
    needs_project = bool(
        args.theme is not None
        or args.expected_theme_code is not None
        or args.upstream_views is None
        or args.baseline is not None
        or args.fail_on.startswith("baseline-")
    )
    root = discover_root(args.root, search_parents=not args.no_parent_search)
    if needs_project and root is None:
        return emit_error(
            f"no Bagisto project root found from {args.root.expanduser()}",
            args.as_json,
            EXIT_NOT_FOUND,
        )

    base = root or args.root.expanduser().resolve()
    try:
        if args.theme is not None:
            if root is None:  # guarded above; keeps type checkers and future edits honest
                raise ComparisonError("a project root is required to resolve --theme")
            theme_views = configured_theme_views(root, args.theme)
            selector_type = "configured-theme"
            selector_value = args.theme
        else:
            theme_views = locate_views_path(args.theme_path, base, "theme path")
            selector_type = "path"
            selector_value = str(args.theme_path)

        if args.upstream_views is not None:
            upstream_views = locate_views_path(args.upstream_views, base, "upstream path")
        else:
            if root is None:  # guarded above
                raise ComparisonError("a project root is required to discover Shop views")
            package = find_package(root, "bagisto/laravel-shop")
            if package is None:
                raise ComparisonError("the bagisto/laravel-shop package was not found under packages/ or vendor/")
            upstream_views = discovered_view_root(package[0])
            if upstream_views is None:
                raise ComparisonError("installed Shop package has no unique discovered Blade view root")

        files = compare(theme_views, upstream_views)
        binding_code = args.theme or args.expected_theme_code
        if binding_code and root is not None and not theme_source_matches_config(
            root,
            binding_code,
            theme_views,
        ):
            raise ComparisonError(
                f"theme source is not the configured/registered source for {binding_code!r}: "
                f"{theme_views}"
            )
        selected_baseline = baseline_path(args.baseline, theme_views, base)
        if selected_baseline and root is None:
            raise ComparisonError(
                "baseline audits require a discovered Bagisto project and installed Shop binding"
            )
        if selected_baseline and root is not None:
            baseline_code = load_baseline(selected_baseline)["theme_code"]
            if binding_code and baseline_code != binding_code:
                raise ComparisonError(
                    f"baseline belongs to theme {baseline_code!r}, not {binding_code!r}"
                )
            if not binding_code and not theme_source_matches_config(root, baseline_code, theme_views):
                raise ComparisonError(
                    f"theme source is not the configured/registered source for {baseline_code!r}: "
                    f"{theme_views}"
                )
            installed_shop = find_package(root, "bagisto/laravel-shop")
            if installed_shop is None:
                raise ComparisonError("the installed bagisto/laravel-shop package was not found")
            installed_views = discovered_view_root(installed_shop[0])
            if installed_views is None:
                raise ComparisonError("installed Shop package has no unique discovered Blade view root")
            if upstream_views.resolve() != installed_views.resolve():
                raise ComparisonError(
                    "baseline upstream must resolve to the installed bagisto/laravel-shop source"
                )
        baseline = (
            analyze_baseline(
                selected_baseline,
                theme_views,
                upstream_views,
                args.theme or args.expected_theme_code,
            )
            if selected_baseline
            else None
        )
    except (ComparisonError, PackageDiscoveryError, OSError) as error:
        return emit_error(str(error), args.as_json, EXIT_INVALID)

    result = result_document(
        root,
        selector_type,
        selector_value,
        theme_views,
        upstream_views,
        files,
        baseline,
    )
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result, args.show_all)
    return EXIT_DIFFERENCES if failure_requested(args.fail_on, files, baseline) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
