#!/usr/bin/env python3
"""Create a collision-safe Bagisto shop-theme scaffold from the installed Shop package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from diff_theme_overrides import (
    ComparisonError,
    build_source_files,
    installed_bagisto_version,
    shop_assets_root,
)
from inspect_theme_environment import PackageDiscoveryError, discovered_view_root, find_package


THEME_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
PHP_IDENTIFIER_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
PHP_RESERVED = {
    "class",
    "enum",
    "function",
    "interface",
    "namespace",
    "trait",
}


class ScaffoldError(RuntimeError):
    pass


class ScaffoldConflictError(ScaffoldError):
    """Report project-relative destinations that would be overwritten."""

    def __init__(self, paths: list[str]) -> None:
        self.paths = sorted(dict.fromkeys(paths))
        displayed = self.paths[:20]
        lines = "\n".join(f"  - {path}" for path in displayed)
        omitted = len(self.paths) - len(displayed)
        suffix = f"\n  ... and {omitted} more" if omitted else ""
        super().__init__(
            f"refusing to overwrite {len(self.paths)} conflicting project-relative paths:\n"
            f"{lines}{suffix}"
        )


@dataclass(frozen=True)
class FileAction:
    source: Path | None
    destination: Path
    content: str | None = None


@dataclass(frozen=True)
class ThemeFeatures:
    parent: bool
    views_namespace: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or create a Bagisto shop theme without overwriting existing files. "
            "Dry-run is the default; pass --apply to write the scaffold."
        )
    )
    parser.add_argument("--project-root", default=".", help="Bagisto project root")
    parser.add_argument("--theme-code", required=True, help="Lowercase theme config key")
    parser.add_argument("--display-name", required=True, help="Admin-facing theme name")
    parser.add_argument(
        "--mode",
        choices=("overlay", "package", "full-fork"),
        default="package",
        help="View-only resource overlay, sparse package, or deliberate complete Shop fork",
    )
    parser.add_argument("--base-theme", help="Theme to inherit; defaults to themes.shop-default")
    parser.add_argument("--vendor", help="PascalCase PHP vendor; required for package modes")
    parser.add_argument("--package", help="PascalCase PHP package; required for package modes")
    parser.add_argument(
        "--registration",
        choices=("local", "composer"),
        default="local",
        help="Use host PSR-4/provider wiring or Composer package discovery (default: local)",
    )
    parser.add_argument(
        "--bagisto-constraint",
        help="Explicit supported bagisto/bagisto range; required with --registration composer",
    )
    parser.add_argument(
        "--theme-license",
        help="Theme package SPDX license expression; required with --registration composer",
    )
    parser.add_argument(
        "--theme-license-file",
        type=Path,
        help="Existing full theme license text inside the project; required with --registration composer",
    )
    parser.add_argument(
        "--package-dir",
        help="Package path relative to project root; defaults to packages/<vendor>/<package>",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Relative Shop Blade view to seed; repeat for multiple files",
    )
    parser.add_argument("--apply", action="store_true", help="Write new files; never overwrite conflicts")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not THEME_CODE_RE.fullmatch(args.theme_code):
        raise ScaffoldError("--theme-code must match [a-z][a-z0-9-]*")

    if not args.display_name.strip() or any(ord(char) < 32 for char in args.display_name):
        raise ScaffoldError("--display-name must be non-empty and contain no control characters")

    if args.mode != "overlay":
        for flag, value in (("--vendor", args.vendor), ("--package", args.package)):
            if not value or not PHP_IDENTIFIER_RE.fullmatch(value) or value.lower() in PHP_RESERVED:
                raise ScaffoldError(f"{flag} is required and must be a PascalCase PHP identifier")

    if args.mode == "overlay" and (
        args.registration != "local"
        or args.bagisto_constraint
        or args.theme_license
        or args.theme_license_file
    ):
        raise ScaffoldError("overlay mode has no package registration or package-license options")
    if args.registration == "composer":
        if not args.bagisto_constraint or any(ord(char) < 32 for char in args.bagisto_constraint):
            raise ScaffoldError("--bagisto-constraint is required with --registration composer")
        if not args.theme_license or not args.theme_license_file:
            raise ScaffoldError(
                "--theme-license and --theme-license-file are required with --registration composer"
            )
    elif args.bagisto_constraint:
        raise ScaffoldError("--bagisto-constraint is only valid with --registration composer")

    if bool(args.theme_license) != bool(args.theme_license_file):
        raise ScaffoldError("--theme-license and --theme-license-file must be supplied together")
    if args.theme_license and (
        len(args.theme_license) > 200
        or not re.fullmatch(r"[A-Za-z0-9.+() -]+", args.theme_license)
    ):
        raise ScaffoldError("--theme-license must be a safe SPDX expression or Composer license identifier")

    for relative in args.override:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.name.endswith(".blade.php"):
            raise ScaffoldError(f"unsafe or non-Blade --override path: {relative}")


def find_project_root(candidate: Path) -> Path:
    candidate = candidate.expanduser().resolve()
    for path in (candidate, *candidate.parents):
        if (path / "artisan").is_file() and (path / "config/themes.php").is_file():
            return path
    raise ScaffoldError(f"no Bagisto root found from {candidate}")


def find_shop_root(project_root: Path) -> Path:
    try:
        match = find_package(project_root, "bagisto/laravel-shop")
    except PackageDiscoveryError as error:
        raise ScaffoldError(str(error)) from error
    if match is None:
        raise ScaffoldError("cannot locate the installed bagisto/laravel-shop package")
    package = match[0].resolve()
    views = discovered_view_root(package)
    if views is None or not any(
        path.is_file() and not path.is_symlink() for path in views.rglob("*")
    ):
        raise ScaffoldError("installed bagisto/laravel-shop has no non-empty Shop view tree")
    try:
        shop_assets_root(package)
    except ComparisonError as error:
        raise ScaffoldError(str(error)) from error
    return package


def find_theme_package_root(project_root: Path) -> Path | None:
    installed_path = project_root / "vendor/composer/installed.json"
    if installed_path.is_file():
        installed = json.loads(installed_path.read_text(encoding="utf-8"))
        records = installed.get("packages", []) if isinstance(installed, dict) else installed
        if isinstance(records, list):
            for record in records:
                if not isinstance(record, dict) or record.get("name") != "bagisto/laravel-theme":
                    continue
                install_path = record.get("install_path")
                if isinstance(install_path, str):
                    candidate = (installed_path.parent / install_path).resolve()
                    if (candidate / "src/Themes.php").is_file():
                        return candidate

    candidates = (
        project_root / "packages/Webkul/Theme",
        project_root / "vendor/bagisto/laravel-theme",
        project_root / "vendor/webkul/theme",
    )
    for candidate in candidates:
        if (candidate / "src/Themes.php").is_file():
            return candidate.resolve()

    for composer_path in (project_root / "vendor").glob("*/*/composer.json"):
        try:
            composer = json.loads(composer_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if composer.get("name") == "bagisto/laravel-theme" and (composer_path.parent / "src/Themes.php").is_file():
            return composer_path.parent.resolve()
    return None


def detect_theme_features(project_root: Path, config_path: Path) -> ThemeFeatures:
    """Detect optional theme configuration keys from installed code, then config evidence."""
    theme_root = find_theme_package_root(project_root)
    if theme_root:
        implementation = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (
                theme_root / "src/Themes.php",
                theme_root / "src/Theme.php",
                theme_root / "src/ThemeViewFinder.php",
            )
            if path.is_file()
        )
        return ThemeFeatures(
            parent=bool(re.search(r"\[['\"]parent['\"]\]", implementation) and "setParent" in implementation),
            views_namespace=bool(
                re.search(r"views_namespace|viewsNamespace", implementation)
                and "ThemeViewFinder" in implementation
            ),
        )

    config = config_path.read_text(encoding="utf-8")
    shop_block = php_array_block(config, "shop")
    return ThemeFeatures(
        parent=bool(re.search(r"['\"]parent['\"]\s*=>", shop_block)),
        views_namespace=bool(re.search(r"['\"]views_namespace['\"]\s*=>", shop_block)),
    )


def matching_bracket(text: str, opening_index: int) -> int:
    pairs = {"[": "]", "(": ")", "{": "}"}
    opening = text[opening_index]
    closing = pairs[opening]
    depth = 0
    quote: str | None = None
    escaped = False

    for index in range(opening_index, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return index
    raise ScaffoldError("unbalanced PHP configuration array")


def php_array_block(text: str, key: str) -> str:
    match = re.search(rf"['\"]{re.escape(key)}['\"]\s*=>\s*\[", text)
    if not match:
        raise ScaffoldError(f"cannot find PHP array key: {key}")
    opening = text.find("[", match.start())
    return text[opening + 1 : matching_bracket(text, opening)]


def php_string(text: str, key: str, required: bool = True) -> str | None:
    match = re.search(rf"['\"]{re.escape(key)}['\"]\s*=>\s*(['\"])(.*?)\1", text)
    if match:
        return match.group(2)
    if required:
        raise ScaffoldError(f"cannot read string key {key} from PHP configuration")
    return None


def read_base_theme(config_path: Path, requested: str | None) -> tuple[str, dict[str, str]]:
    text = config_path.read_text(encoding="utf-8")
    default_code = php_string(text, "shop-default")
    code = requested or default_code
    shop_block = php_array_block(text, "shop")
    theme_block = php_array_block(shop_block, code)
    vite_block = php_array_block(theme_block, "vite")
    return code, {
        "assets_path": php_string(theme_block, "assets_path"),
        "views_path": php_string(theme_block, "views_path"),
        "hot_file": php_string(vite_block, "hot_file"),
        "build_directory": php_string(vite_block, "build_directory"),
        "package_assets_directory": php_string(vite_block, "package_assets_directory"),
    }


def read_existing_theme(config_path: Path, code: str) -> dict[str, str | None] | None:
    text = config_path.read_text(encoding="utf-8")
    shop_block = php_array_block(text, "shop")
    if not re.search(rf"['\"]{re.escape(code)}['\"]\s*=>\s*\[", shop_block):
        return None
    theme_block = php_array_block(shop_block, code)
    vite_block = php_array_block(theme_block, "vite")
    return {
        "name": php_string(theme_block, "name", required=False),
        "assets_path": php_string(theme_block, "assets_path", required=False),
        "views_path": php_string(theme_block, "views_path", required=False),
        "views_namespace": php_string(theme_block, "views_namespace", required=False),
        "parent": php_string(theme_block, "parent", required=False),
        "hot_file": php_string(vite_block, "hot_file", required=False),
        "build_directory": php_string(vite_block, "build_directory", required=False),
        "package_assets_directory": php_string(vite_block, "package_assets_directory", required=False),
    }


def kebab(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", value).lower()


def php_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def safe_relative_path(value: str, field: str) -> str:
    if not value or any(ord(char) < 32 for char in value) or "\\" in value:
        raise ScaffoldError(f"selected base theme has an unsafe {field}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ScaffoldError(f"selected base theme {field} must be a safe project-relative path")
    normalized = path.as_posix()
    if normalized in {".", "public"}:
        raise ScaffoldError(f"selected base theme {field} is too broad to derive safely")
    return normalized


def derive_theme_path(value: str, base_code: str, theme_code: str, field: str) -> str:
    """Derive a collision-free sibling path while preserving the selected base topology."""
    source = safe_relative_path(value, field)
    parts = list(PurePosixPath(source).parts)
    identity = re.compile(rf"(?<![A-Za-z0-9]){re.escape(base_code)}(?![A-Za-z0-9])")
    changed = False

    if field == "hot_file":
        conventional = re.fullmatch(
            rf".+-{re.escape(base_code)}(?P<suffix>-vite\.hot)",
            parts[-1],
        )
        if conventional:
            parts[-1] = theme_code + conventional.group("suffix")
            changed = True

    if not changed:
        derived: list[str] = []
        for part in parts:
            replacement, count = identity.subn(theme_code, part)
            derived.append(replacement)
            changed = changed or count > 0
        parts = derived

    if not changed:
        if field == "hot_file":
            parts[-1] = f"{theme_code}-{parts[-1]}"
        elif field in {"views_path", "build_directory"} and parts[-1].lower() in {
            "views",
            "templates",
            "build",
            "dist",
        }:
            parts.insert(-1, theme_code)
        else:
            parts.append(theme_code)

    result = safe_relative_path(PurePosixPath(*parts).as_posix(), field)
    if result == source:
        raise ScaffoldError(f"cannot derive a unique {field} from selected base theme {base_code!r}")
    return result


def theme_config_snippet(
    args: argparse.Namespace,
    base_code: str,
    base: dict[str, str],
    features: ThemeFeatures,
) -> str:
    values = generated_theme_values(args, base_code, base, features)
    namespace_line = (
        f"        'views_namespace' => {php_quote(str(values['views_namespace']))},\n"
        if values["views_namespace"]
        else ""
    )
    parent_line = (
        f"        'parent' => {php_quote(str(values['parent']))},\n"
        if values["parent"]
        else ""
    )
    return (
        f"{php_quote(args.theme_code)} => [\n"
        f"        'name' => {php_quote(str(values['name']))},\n"
        f"        'assets_path' => {php_quote(str(values['assets_path']))},\n"
        f"        'views_path' => {php_quote(str(values['views_path']))},\n"
        f"{namespace_line}{parent_line}"
        "\n"
        "        'vite' => [\n"
        f"            'hot_file' => {php_quote(str(values['hot_file']))},\n"
        f"            'build_directory' => {php_quote(str(values['build_directory']))},\n"
        f"            'package_assets_directory' => {php_quote(str(values['package_assets_directory']))},\n"
        "        ],\n"
        "    ],"
    )


def generated_theme_values(
    args: argparse.Namespace,
    base_code: str,
    base: dict[str, str],
    features: ThemeFeatures,
) -> dict[str, str | None]:
    views_path = derive_theme_path(base["views_path"], base_code, args.theme_code, "views_path")
    package_assets_directory = safe_relative_path(
        base["package_assets_directory"],
        "package_assets_directory",
    )

    if args.mode == "overlay":
        assets_path = safe_relative_path(base["assets_path"], "assets_path")
        views_namespace = None
        vite = {
            "hot_file": safe_relative_path(base["hot_file"], "hot_file"),
            "build_directory": safe_relative_path(base["build_directory"], "build_directory"),
            "package_assets_directory": package_assets_directory,
        }
    else:
        assets_path = derive_theme_path(base["assets_path"], base_code, args.theme_code, "assets_path")
        views_namespace = args.theme_code if features.views_namespace else None
        vite = {
            "hot_file": derive_theme_path(base["hot_file"], base_code, args.theme_code, "hot_file"),
            "build_directory": derive_theme_path(
                base["build_directory"],
                base_code,
                args.theme_code,
                "build_directory",
            ),
            "package_assets_directory": package_assets_directory,
        }

    return {
        "name": args.display_name.strip(),
        "assets_path": assets_path,
        "views_path": views_path,
        "views_namespace": views_namespace,
        "parent": base_code if features.parent and args.theme_code != base_code else None,
        **vite,
    }


def vite_registry_snippet(args: argparse.Namespace, values: dict[str, str | None]) -> str | None:
    if args.mode == "overlay":
        return None
    return (
        f"{php_quote(args.theme_code)} => [\n"
        f"        'hot_file' => {php_quote(str(values['hot_file']))},\n"
        f"        'build_directory' => {php_quote(str(values['build_directory']))},\n"
        f"        'package_assets_directory' => {php_quote(str(values['package_assets_directory']))},\n"
        "    ],"
    )


def package_location(args: argparse.Namespace, root: Path) -> Path:
    relative = Path(args.package_dir) if args.package_dir else Path("packages") / args.vendor / args.package
    if relative.is_absolute() or ".." in relative.parts:
        raise ScaffoldError("--package-dir must stay inside the project root")
    if relative.parts and relative.parts[0] in {"vendor", "node_modules", "storage", "public"}:
        raise ScaffoldError("--package-dir cannot target generated, dependency, runtime, or public directories")
    unresolved = (root / relative).absolute()
    validate_destination(root, unresolved)
    destination = unresolved.resolve()
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise ScaffoldError("--package-dir escapes the project root") from error
    return destination


def validate_destination(root: Path, destination: Path) -> None:
    """Reject writes through symlinks or outside the resolved project root."""
    root = root.resolve()
    destination = destination.absolute()
    try:
        destination.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise ScaffoldError(f"destination resolves outside the project root: {destination}") from error

    current = destination
    while current != root:
        if current.is_symlink():
            raise ScaffoldError(f"refusing to write through symlink: {current}")
        parent = current.parent
        if parent == current:
            raise ScaffoldError(f"destination is not beneath the project root: {destination}")
        current = parent


def validate_destinations(root: Path, actions: list[FileAction]) -> None:
    for action in actions:
        validate_destination(root, action.destination)


def resolve_project_file(root: Path, value: Path, label: str) -> Path:
    unresolved = value.expanduser()
    unresolved = unresolved if unresolved.is_absolute() else root / unresolved
    if unresolved.is_symlink() or not unresolved.is_file():
        raise ScaffoldError(f"{label} must be an existing non-symlink file: {unresolved}")
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ScaffoldError(f"{label} must stay inside the project root: {resolved}") from error
    return resolved


def find_bagisto_license(
    root: Path,
    shop_root: Path,
    root_composer: dict[str, Any],
) -> Path:
    names = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
    candidates = [shop_root / name for name in names]
    if root_composer.get("name") == "bagisto/bagisto":
        candidates.extend(root / name for name in names)
    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink() and candidate.stat().st_size:
            return candidate.resolve()
    raise ScaffoldError(
        "the exact installed Bagisto license notice was not found; supply it in the Shop package "
        "or use a checkout that retains the upstream notice before copying sources"
    )


def translation_namespace(args: argparse.Namespace) -> str:
    return f"{kebab(args.vendor)}-{kebab(args.package)}"


def upstream_notice_source() -> str:
    return """# Upstream notices

This scaffold contains files copied from or derived from the installed Composer package
`bagisto/laravel-shop`. The exact license notice discovered in the target checkout is
retained at `UPSTREAM-LICENSES/BAGISTO-LICENSE`.

This notice does not declare the theme author's license. Audit every bundled font, image,
icon, script, stylesheet, and later-added asset for its own attribution and redistribution
requirements before distribution.
"""


def provider_source(args: argparse.Namespace, published_views_path: str) -> str:
    namespace = f"{args.vendor}\\{args.package}"
    provider = f"{args.package}ServiceProvider"
    tag = f"{args.theme_code}-theme-views"
    translations = translation_namespace(args)
    return f"""<?php

namespace {namespace}\\Providers;

use Illuminate\\Support\\Facades\\Blade;
use Illuminate\\Support\\ServiceProvider;

class {provider} extends ServiceProvider
{{
    public function boot(): void
    {{
        $viewsPath = __DIR__.'/../Resources/views';
        $translationsPath = __DIR__.'/../Resources/lang';

        $this->loadViewsFrom($viewsPath, '{args.theme_code}');

        if (is_dir($translationsPath)) {{
            $this->loadTranslationsFrom($translationsPath, '{translations}');
        }}

        Blade::anonymousComponentPath($viewsPath.'/components', '{args.theme_code}');

        $this->publishes([
            $viewsPath => base_path({php_quote(published_views_path)}),
        ], '{tag}');
    }}
}}
"""


def composer_source(args: argparse.Namespace, root_composer: dict[str, Any]) -> str:
    namespace = f"{args.vendor}\\{args.package}\\"
    provider = f"{args.vendor}\\{args.package}\\Providers\\{args.package}ServiceProvider"
    data: dict[str, Any] = {
        "name": f"{kebab(args.vendor)}/{kebab(args.package)}",
        "type": "library",
        "description": f"{args.display_name.strip()} shop theme for Bagisto",
        "autoload": {"psr-4": {namespace: "src/"}},
    }
    if args.theme_license:
        data["license"] = args.theme_license
    root_require = root_composer.get("require", {})
    require: dict[str, str] = {}
    php_constraint = root_require.get("php")
    if php_constraint:
        require["php"] = php_constraint
    illuminate_constraint = root_require.get("illuminate/support") or root_require.get("laravel/framework")
    if illuminate_constraint:
        require["illuminate/support"] = illuminate_constraint
    if args.registration == "composer":
        require["bagisto/bagisto"] = args.bagisto_constraint
        data["extra"] = {"laravel": {"providers": [provider]}}
    if require:
        data["require"] = require
    return json.dumps(data, indent=4, ensure_ascii=False) + "\n"


def package_json_source(source: Path, args: argparse.Namespace) -> str:
    data = json.loads(source.read_text(encoding="utf-8"))
    data["name"] = f"{kebab(args.vendor)}-{kebab(args.package)}"
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def patch_vite(
    source: str,
    package_root: Path,
    project_root: Path,
    hot_file: str,
    build_directory: str,
    package_assets_directory: str,
    source_assets_directory: str,
) -> str:
    root_relative = os.path.relpath(project_root, package_root).replace(os.sep, "/")
    root_relative = "." if root_relative == "." else root_relative
    env_dir = root_relative.rstrip("/") + "/"
    replacements = [
        (r'const\s+envDir\s*=\s*["\'][^"\']+["\']', f'const envDir = "{env_dir}"'),
        (r'hotFile\s*:\s*["\'][^"\']+["\']', f'hotFile: "{env_dir}public/{hot_file}"'),
        (r'publicDirectory\s*:\s*["\'][^"\']+["\']', f'publicDirectory: "{env_dir}public"'),
        (r'buildDirectory\s*:\s*["\'][^"\']+["\']', f'buildDirectory: "{build_directory}"'),
    ]
    result = source
    for pattern, replacement in replacements:
        result, count = re.subn(pattern, replacement, result, count=1)
        if count != 1:
            raise ScaffoldError(f"installed Shop Vite config does not expose expected setting: {pattern}")
    if package_assets_directory != source_assets_directory:
        result = result.replace(source_assets_directory, package_assets_directory)
    return result


def patch_tailwind(
    source: str,
    package_root: Path,
    project_root: Path,
    shop_root: Path,
    views_path: str,
    package_assets_directory: str,
    source_assets_directory: str,
) -> str:
    shop_rel = os.path.relpath(shop_root, package_root).replace(os.sep, "/")
    published_rel = os.path.relpath(
        project_root / views_path,
        package_root,
    ).replace(os.sep, "/")
    if package_assets_directory != source_assets_directory:
        source = source.replace(source_assets_directory, package_assets_directory)
    match = re.search(r"\bcontent\s*:\s*\[", source)
    if not match:
        raise ScaffoldError("installed Shop Tailwind config has an unsupported content declaration")
    opening = source.find("[", match.start())
    closing = matching_bracket(source, opening)
    existing = source[opening + 1 : closing]
    additions = [
        f"./{package_assets_directory}/**/*.{{blade.php,js,jsx,ts,tsx,vue}}",
        f"{shop_rel}/src/Resources/**/*.{{blade.php,js,jsx,ts,tsx,vue}}",
        f"{published_rel}/**/*.{{blade.php,js,jsx,ts,tsx,vue}}",
    ]
    additions = [value for value in additions if value not in existing]
    if not additions:
        return source

    line_start = source.rfind("\n", 0, match.start()) + 1
    closing_indentation = re.match(r"[ \t]*", source[line_start:match.start()]).group(0)
    indentation = closing_indentation + "    "
    separator = "," if existing.strip() and not existing.rstrip().endswith(",") else ""
    newline = "" if existing.endswith("\n") else "\n"
    inserted = (
        separator
        + newline
        + "".join(f'{indentation}"{value}",\n' for value in additions)
        + closing_indentation
    )
    return source[:closing] + inserted + source[closing:]


def add_tree_actions(actions: list[FileAction], source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file() and not path.is_symlink():
            actions.append(FileAction(path, destination / path.relative_to(source)))


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): file_hash(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def shop_build_hashes(shop_root: Path) -> dict[str, str]:
    return {
        relative: file_hash(path)
        for relative, path in sorted(build_source_files(shop_root).items())
    }


def build_actions(
    args: argparse.Namespace,
    root: Path,
    shop_root: Path,
    root_composer: dict[str, Any],
    theme_values: dict[str, str | None],
) -> tuple[list[FileAction], Path]:
    views_source = discovered_view_root(shop_root)
    if views_source is None:
        raise ScaffoldError("installed bagisto/laravel-shop has no unique discovered Blade view root")
    actions: list[FileAction] = []
    copied_view_sources: list[Path] = []
    copied_asset_sources: list[Path] = []
    build_sources: list[Path] = []
    package_root: Path | None = None
    try:
        assets_source = shop_assets_root(shop_root)
    except ComparisonError as error:
        raise ScaffoldError(str(error)) from error
    shop_assets_directory = assets_source.relative_to(shop_root).as_posix()
    bagisto_release = installed_bagisto_version(shop_root)
    if not bagisto_release:
        raise ScaffoldError(
            "cannot create an auditable baseline because the installed Bagisto version is unavailable"
        )

    if args.mode == "overlay":
        unresolved_target = root / str(theme_values["views_path"])
        validate_destination(root, unresolved_target)
        target = unresolved_target.resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise ScaffoldError("overlay destination resolves outside the project root") from error
    else:
        package_root = package_location(args, root)
        target = package_root / "src/Resources/views"
        provider_path = package_root / "src/Providers" / f"{args.package}ServiceProvider.php"
        actions.extend(
            [
                FileAction(None, provider_path, provider_source(args, str(theme_values["views_path"]))),
                FileAction(None, package_root / "composer.json", composer_source(args, root_composer)),
                FileAction(None, package_root / ".gitignore", "node_modules/\n*.hot\n"),
            ]
        )

        shop_build_contract = build_source_files(shop_root)
        package_json = shop_root / "package.json"
        vite_config = next(
            (
                path
                for path in (
                    shop_root / "vite.config.js",
                    shop_root / "vite.config.cjs",
                    shop_root / "vite.config.mjs",
                    shop_root / "vite.config.ts",
                    shop_root / "vite.config.mts",
                    shop_root / "vite.config.cts",
                )
                if path.is_file()
            ),
            None,
        )
        tailwind_config = next(
            (
                path
                for path in (
                    shop_root / "tailwind.config.js",
                    shop_root / "tailwind.config.cjs",
                    shop_root / "tailwind.config.mjs",
                    shop_root / "tailwind.config.ts",
                    shop_root / "tailwind.config.mts",
                    shop_root / "tailwind.config.cts",
                )
                if path.is_file()
            ),
            None,
        )
        if not package_json.is_file() or vite_config is None or tailwind_config is None:
            raise ScaffoldError("installed Shop package lacks package.json, a Vite config, or a Tailwind config")
        actions.extend(
            [
                FileAction(package_json, package_root / "package.json", package_json_source(package_json, args)),
                FileAction(
                    vite_config,
                    package_root / vite_config.name,
                    patch_vite(
                        vite_config.read_text(encoding="utf-8"),
                        package_root,
                        root,
                        str(theme_values["hot_file"]),
                        str(theme_values["build_directory"]),
                        str(theme_values["package_assets_directory"]),
                        shop_assets_directory,
                    ),
                ),
                FileAction(
                    tailwind_config,
                    package_root / tailwind_config.name,
                    patch_tailwind(
                        tailwind_config.read_text(encoding="utf-8"),
                        package_root,
                        root,
                        shop_root,
                        str(theme_values["views_path"]),
                        str(theme_values["package_assets_directory"]),
                        shop_assets_directory,
                    ),
                ),
            ]
        )
        build_sources.extend((package_json, vite_config, tailwind_config))
        for candidate in (
            "postcss.config.cjs",
            "postcss.config.js",
            "postcss.config.mjs",
            "postcss.config.ts",
            "postcss.config.mts",
            "postcss.config.cts",
        ):
            source = shop_root / candidate
            if source.is_file():
                actions.append(FileAction(source, package_root / candidate))
                build_sources.append(source)
                break
        else:
            raise ScaffoldError("installed Shop package lacks a PostCSS configuration")

        handled_sources = {path.resolve() for path in build_sources}
        for relative, source in sorted(shop_build_contract.items()):
            if source.resolve() in handled_sources:
                continue
            actions.append(FileAction(source, package_root / relative))
            build_sources.append(source)
            handled_sources.add(source.resolve())

        copied_asset_sources = [path for path in sorted(assets_source.rglob("*")) if path.is_file() and not path.is_symlink()]
        add_tree_actions(
            actions,
            assets_source,
            package_root / str(theme_values["package_assets_directory"]),
        )

    notice_root = package_root if package_root else target.parent
    bagisto_license = find_bagisto_license(root, shop_root, root_composer)
    actions.extend(
        [
            FileAction(
                bagisto_license,
                notice_root / "UPSTREAM-LICENSES/BAGISTO-LICENSE",
            ),
            FileAction(
                None,
                notice_root / "UPSTREAM-NOTICES.md",
                upstream_notice_source(),
            ),
        ]
    )
    if args.theme_license_file:
        if package_root is None:  # rejected by argument validation; defensive for future modes
            raise ScaffoldError("a theme license file requires a package mode")
        theme_license = resolve_project_file(
            root,
            args.theme_license_file,
            "--theme-license-file",
        )
        actions.append(FileAction(theme_license, package_root / "LICENSE"))

    if args.mode == "full-fork":
        copied_view_sources = [path for path in sorted(views_source.rglob("*")) if path.is_file() and not path.is_symlink()]
        add_tree_actions(actions, views_source, target)
    else:
        for relative_value in args.override:
            relative = Path(relative_value)
            source = views_source / relative
            if not source.is_file():
                raise ScaffoldError(f"Shop view does not exist: {relative_value}")
            copied_view_sources.append(source)
            actions.append(FileAction(source, target / relative))

    try:
        shop_source = str(shop_root.relative_to(root))
    except ValueError:
        shop_source = None
    baseline = {
        "schema_version": 1,
        "theme_code": args.theme_code,
        "scaffold_mode": args.mode,
        "shop": {
            "composer_name": "bagisto/laravel-shop",
            "bagisto_version": bagisto_release,
            "assets_directory": shop_assets_directory,
            "source_path": shop_source,
        },
        "theme": {
            "package_assets_directory": str(theme_values["package_assets_directory"]),
        },
        "views": {
            path.relative_to(views_source).as_posix(): file_hash(path)
            for path in copied_view_sources
        },
        "assets": {
            path.relative_to(assets_source).as_posix(): file_hash(path)
            for path in copied_asset_sources
        },
        "build_sources": {
            path.relative_to(shop_root).as_posix(): file_hash(path)
            for path in build_sources
        },
        "shop_inventory": {
            "views": tree_hashes(views_source),
            "assets": tree_hashes(assets_source),
            "build_sources": shop_build_hashes(shop_root),
        },
    }
    baseline_root = package_root if package_root else target.parent
    actions.append(
        FileAction(
            None,
            baseline_root / ".bagisto-theme-baseline.json",
            json.dumps(baseline, indent=2, sort_keys=True) + "\n",
        )
    )

    return actions, target


def destination_state(action: FileAction) -> str:
    if action.destination.is_symlink():
        return "conflict"
    if not action.destination.exists():
        return "create"
    if not action.destination.is_file():
        return "conflict"
    expected = action.content.encode() if action.content is not None else action.source.read_bytes()
    return "unchanged" if action.destination.read_bytes() == expected else "conflict"


def conflict_error(
    actions_and_states: list[tuple[FileAction, str]],
    root: Path,
) -> ScaffoldConflictError:
    paths: list[str] = []
    for action, state in actions_and_states:
        if state != "conflict":
            continue
        try:
            path = action.destination.absolute().relative_to(root.resolve()).as_posix()
        except ValueError:
            path = str(action.destination.absolute())
        paths.append(path)
    return ScaffoldConflictError(paths)


def apply_actions(actions: list[FileAction], root: Path) -> dict[str, int]:
    validate_destinations(root, actions)
    states = {"create": 0, "unchanged": 0, "conflict": 0}
    assessed = [(action, destination_state(action)) for action in actions]
    for _, state in assessed:
        states[state] += 1
    if states["conflict"]:
        raise conflict_error(assessed, root)
    for action, state in assessed:
        if state != "create":
            continue
        validate_destination(root, action.destination)
        action.destination.parent.mkdir(parents=True, exist_ok=True)
        validate_destination(root, action.destination)
        if action.content is not None:
            action.destination.write_text(action.content, encoding="utf-8")
        else:
            shutil.copy2(action.source, action.destination)
    return states


def planned_action_manifest(
    action_states: list[tuple[FileAction, str]],
    root: Path,
    shop_root: Path,
) -> list[dict[str, str | None]]:
    """Expose every planned write without leaking host-specific absolute paths."""
    root = root.resolve()
    shop_root = shop_root.resolve()
    manifest: list[dict[str, str | None]] = []
    for action, state in sorted(
        action_states,
        key=lambda item: item[0].destination.resolve(strict=False).as_posix(),
    ):
        destination = action.destination.resolve(strict=False).relative_to(root).as_posix()
        if action.content is not None:
            if action.source is not None:
                copied = action.source.resolve()
                try:
                    source = copied.relative_to(shop_root).as_posix()
                    source_kind = "generated-from-installed-shop"
                except ValueError:
                    source = copied.relative_to(root).as_posix()
                    source_kind = "generated-from-project-file"
            else:
                source_kind = "generated"
                source = None
            checksum = hashlib.sha256(action.content.encode("utf-8")).hexdigest()
        else:
            copied = action.source.resolve()
            try:
                source = copied.relative_to(shop_root).as_posix()
                source_kind = "installed-shop-file"
            except ValueError:
                try:
                    source = copied.relative_to(root).as_posix()
                    source_kind = "project-file"
                except ValueError as error:
                    raise ScaffoldError(
                        f"cannot report a safe project-relative source for {destination}"
                    ) from error
            checksum = file_hash(copied)
        manifest.append(
            {
                "destination": destination,
                "source_kind": source_kind,
                "source": source,
                "state": state,
                "sha256": checksum,
            }
        )
    return manifest


def integration_payload(
    args: argparse.Namespace,
    root: Path,
    target: Path,
    base_code: str,
    base: dict[str, str],
    features: ThemeFeatures,
    values: dict[str, str | None],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "theme_code": args.theme_code,
        "mode": args.mode,
        "base_theme": base_code,
        "scaffold_path": str(target.relative_to(root)),
        "themes_php_entry": theme_config_snippet(args, base_code, base, features),
        "activation": "Build and validate first, then select the theme on only the intended channel.",
        "global_default_changed": False,
        "upstream_license_notice": str(
            ((package_location(args, root) if args.mode != "overlay" else target.parent)
            / "UPSTREAM-LICENSES/BAGISTO-LICENSE").relative_to(root)
        ),
    }
    registry = vite_registry_snippet(args, values)
    if registry:
        namespace = f"{args.vendor}\\{args.package}"
        payload.update({
            "bagisto_vite_entry": registry,
            "registration_strategy": args.registration,
            "composer_package": f"{kebab(args.vendor)}/{kebab(args.package)}",
            "package_directory": str(package_location(args, root).relative_to(root)),
            "public_build_directory": str(PurePosixPath("public") / str(values["build_directory"])),
            "translation_namespace": translation_namespace(args),
            "theme_license": args.theme_license,
            "theme_license_file": "LICENSE" if args.theme_license_file else None,
        })
        if args.registration == "local":
            payload["local_registration"] = {
                "composer_psr4": f"{namespace}\\ => {target.parents[2].relative_to(root) if 'src' in target.parts else target.relative_to(root)}/src",
                "provider": f"{namespace}\\Providers\\{args.package}ServiceProvider::class",
            }
        else:
            payload["composer_registration"] = {
                "package": f"{kebab(args.vendor)}/{kebab(args.package)}",
                "bagisto_constraint": args.bagisto_constraint,
                "provider": "Laravel package discovery",
            }
    return payload


def render_human(payload: dict[str, Any], states: dict[str, int], applied: bool) -> None:
    print(f"Mode: {payload['mode']}")
    print(f"Theme code: {payload['theme_code']}")
    print(f"Scaffold: {payload['scaffold_path']}")
    print(f"Files: {states['create']} create, {states['unchanged']} unchanged, {states['conflict']} conflict")
    print("Status: applied" if applied else "Status: dry-run (pass --apply to write)")
    print(f"Upstream license notice: {payload['upstream_license_notice']}")
    print("\nPlanned file actions")
    for action in payload["planned_actions"]:
        source = action["source"] or "generated content"
        print(
            f"  {action['state']:<9} {action['destination']} <- {source} "
            f"[{action['sha256'][:12]}]"
        )
    print("\nMerge this entry into config/themes.php under shop (preserve every existing theme):\n")
    print(payload["themes_php_entry"])
    if payload.get("bagisto_vite_entry"):
        print("\nAdd this to config/bagisto-vite.php only when using explicit namespaced asset helpers:\n")
        print(payload["bagisto_vite_entry"])
        if payload.get("registration_strategy") == "local":
            print("\nRegistration: local checkout. Merge only the reported PSR-4 mapping and provider, then composer dump-autoload.")
        else:
            print("\nRegistration: Composer distribution. Install the generated package and rely only on Laravel discovery.")
        print(f"\nTranslation namespace: {payload['translation_namespace']}")
        if payload.get("theme_license"):
            print(f"Theme package license: {payload['theme_license']} (full text copied to LICENSE)")
        else:
            print("Theme package license: undecided; choose one before distribution.")
    print("\nDo not change themes.shop-default. Build and validate before channel activation.")


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        root = find_project_root(Path(args.project_root))
        shop_root = find_shop_root(root)
        root_composer = json.loads((root / "composer.json").read_text(encoding="utf-8"))
        themes_config = root / "config/themes.php"
        base_code, base = read_base_theme(themes_config, args.base_theme)
        features = detect_theme_features(root, themes_config)
        existing = read_existing_theme(themes_config, args.theme_code)
        expected = generated_theme_values(args, base_code, base, features)
        if existing is not None and args.theme_code == base_code:
            raise ScaffoldError("refusing to scaffold over the configured fallback theme; use an explicit update workflow")
        if existing is not None and existing != expected:
            mismatched = sorted(key for key, value in expected.items() if existing.get(key) != value)
            raise ScaffoldError(
                "theme code already exists with different configuration: " + ", ".join(mismatched)
            )
        actions, target = build_actions(args, root, shop_root, root_composer, expected)
        validate_destinations(root, actions)
        action_states = [(action, destination_state(action)) for action in actions]
        assessed = {"create": 0, "unchanged": 0, "conflict": 0}
        for _, state in action_states:
            assessed[state] += 1
        if assessed["conflict"]:
            raise conflict_error(action_states, root)
        states = apply_actions(actions, root) if args.apply else assessed
        if args.apply:
            validate_destination(root, target)
            target.mkdir(parents=True, exist_ok=True)
            validate_destination(root, target)
        payload = integration_payload(args, root, target, base_code, base, features, expected)
        payload["files"] = states
        payload["planned_actions"] = planned_action_manifest(action_states, root, shop_root)
        payload["applied"] = args.apply
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            render_human(payload, states, args.apply)
        return 0
    except (ScaffoldError, json.JSONDecodeError, OSError) as error:
        if args.json:
            payload: dict[str, Any] = {
                "schema_version": 1,
                "error": str(error),
            }
            if isinstance(error, ScaffoldConflictError):
                payload["conflicts"] = {
                    "count": len(error.paths),
                    "paths": error.paths[:20],
                    "truncated": len(error.paths) > 20,
                }
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
