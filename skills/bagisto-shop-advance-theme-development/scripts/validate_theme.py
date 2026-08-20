#!/usr/bin/env python3
"""Run read-only structural checks for a Bagisto shop theme."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from diff_theme_overrides import (
    ComparisonError,
    analyze_baseline,
    registered_namespace_roots,
    shop_assets_root,
)
from inspect_theme_environment import (
    JavaScriptScanError,
    PackageDiscoveryError,
    _javascript_default_import_bindings,
    _javascript_matching_token,
    discovered_view_root,
    find_package,
    javascript_module_specifiers,
    javascript_tokens,
    strip_php_comments,
)


THEME_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
NODE_BUILTINS = {
    "assert",
    "async_hooks",
    "buffer",
    "child_process",
    "cluster",
    "console",
    "constants",
    "crypto",
    "dgram",
    "diagnostics_channel",
    "dns",
    "domain",
    "events",
    "fs",
    "http",
    "http2",
    "https",
    "module",
    "net",
    "os",
    "path",
    "perf_hooks",
    "process",
    "punycode",
    "querystring",
    "readline",
    "repl",
    "stream",
    "string_decoder",
    "sys",
    "timers",
    "tls",
    "trace_events",
    "tty",
    "url",
    "util",
    "v8",
    "vm",
    "wasi",
    "worker_threads",
    "zlib",
}


class ValidationError(RuntimeError):
    pass


@dataclass
class Finding:
    level: str
    check: str
    message: str
    path: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Bagisto shop theme without changing files, querying the database, or using the network."
    )
    parser.add_argument("--project-root", default=".", help="Bagisto project root")
    parser.add_argument("--theme-code", required=True, help="Theme key from config/themes.php")
    parser.add_argument("--package-dir", help="Optional theme package directory, relative to project root")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings remain")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args()


def find_project_root(candidate: Path) -> Path:
    candidate = candidate.expanduser().resolve()
    for path in (candidate, *candidate.parents):
        if (path / "artisan").is_file() and (path / "config/themes.php").is_file():
            return path
    raise ValidationError(f"no Bagisto project root found from {candidate}")


def find_shop_root(root: Path) -> Path:
    try:
        match = find_package(root, "bagisto/laravel-shop")
    except PackageDiscoveryError as error:
        raise ValidationError(str(error)) from error
    if match is None:
        raise ValidationError("cannot locate the installed bagisto/laravel-shop package")
    package = match[0].resolve()
    views = discovered_view_root(package)
    if views is None or not any(
        path.is_file() and not path.is_symlink() for path in views.rglob("*")
    ):
        raise ValidationError("installed bagisto/laravel-shop has no non-empty Shop view tree")
    try:
        shop_assets_root(package)
    except ComparisonError as error:
        raise ValidationError(str(error)) from error
    return package


def shop_views_root(shop_root: Path) -> Path:
    views = discovered_view_root(shop_root)
    if views is None:
        raise ValidationError("installed Shop package has no unique discovered Blade view root")
    return views


def matching_bracket(text: str, opening_index: int) -> int:
    opening = text[opening_index]
    closing = {"[": "]", "(": ")", "{": "}"}[opening]
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
    raise ValidationError("unbalanced PHP configuration array")


def php_array_block(text: str, key: str) -> str:
    match = re.search(rf"['\"]{re.escape(key)}['\"]\s*=>\s*\[", text)
    if not match:
        raise ValidationError(f"missing PHP array key {key}")
    opening = text.find("[", match.start())
    return text[opening + 1 : matching_bracket(text, opening)]


def php_string(text: str, key: str) -> str | None:
    match = re.search(rf"['\"]{re.escape(key)}['\"]\s*=>\s*(['\"])(.*?)\1", text)
    return match.group(2) if match else None


def theme_config(root: Path, code: str) -> dict[str, str | None]:
    text = (root / "config/themes.php").read_text(encoding="utf-8")
    shop = php_array_block(text, "shop")
    theme = php_array_block(shop, code)
    vite = php_array_block(theme, "vite")
    return {
        "name": php_string(theme, "name"),
        "assets_path": php_string(theme, "assets_path"),
        "views_path": php_string(theme, "views_path"),
        "views_namespace": php_string(theme, "views_namespace"),
        "parent": php_string(theme, "parent"),
        "hot_file": php_string(vite, "hot_file"),
        "build_directory": php_string(vite, "build_directory"),
        "package_assets_directory": php_string(vite, "package_assets_directory"),
    }


def add(findings: list[Finding], level: str, check: str, message: str, path: Path | None = None) -> None:
    findings.append(Finding(level, check, message, str(path) if path else None))


def resolve_project_path(root: Path, configured: str | None) -> Path | None:
    if not configured:
        return None
    value = Path(configured)
    if value.is_absolute():
        return value
    return root / value


def find_package_root(root: Path, explicit: str | None, code: str, build_directory: str | None) -> Path | None:
    if explicit:
        path = (root / explicit).resolve() if not Path(explicit).is_absolute() else Path(explicit).resolve()
        try:
            path.relative_to(root)
        except ValueError as error:
            raise ValidationError("--package-dir must stay inside the project root") from error
        return path

    composer_candidates = [
        *root.glob("packages/*/*/composer.json"),
        *root.glob("vendor/*/*/composer.json"),
    ]
    matches: set[Path] = set()
    for composer_path in composer_candidates:
        package_root = composer_path.parent
        try:
            composer = json.loads(composer_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if composer.get("name") == "bagisto/laravel-shop":
            continue
        vite = vite_config_path(package_root)
        provider_matches = list((package_root / "src/Providers").glob("*ServiceProvider.php"))
        combined = ""
        if vite:
            combined += vite.read_text(encoding="utf-8", errors="ignore")
        for provider in provider_matches:
            combined += provider.read_text(encoding="utf-8", errors="ignore")
        active_combined = strip_template_comments(combined)
        namespace_pattern = rf"loadViewsFrom\s*\([^;]*['\"]{re.escape(code)}['\"]\s*\)"
        if re.search(namespace_pattern, active_combined, flags=re.S) or (
            build_directory and build_directory in active_combined
        ):
            matches.add(package_root.resolve())
    if len(matches) > 1:
        raise ValidationError(
            f"multiple theme packages match {code!r}: "
            + ", ".join(str(path) for path in sorted(matches))
        )
    return next(iter(matches)) if matches else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_views(theme_views: Path, shop_views: Path) -> tuple[int, int, int, int]:
    theme_files = {
        path.relative_to(theme_views): path
        for path in theme_views.rglob("*.blade.php")
        if path.is_file() and not path.is_symlink()
    }
    shop_files = {
        path.relative_to(shop_views): path
        for path in shop_views.rglob("*.blade.php")
        if path.is_file() and not path.is_symlink()
    }
    common = theme_files.keys() & shop_files.keys()
    identical = sum(sha256(theme_files[path]) == sha256(shop_files[path]) for path in common)
    modified = len(common) - identical
    return identical, modified, len(theme_files.keys() - shop_files.keys()), len(shop_files.keys() - theme_files.keys())


def strip_javascript_comments(source: str) -> str:
    """Remove JavaScript comments without exposing strings to import/config regexes."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    while index < len(source):
        char = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and following == "/":
            output.extend((" ", " "))
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and following == "*":
            output.extend((" ", " "))
            index += 2
            while index < len(source):
                if index + 1 < len(source) and source[index : index + 2] == "*/":
                    output.extend((" ", " "))
                    index += 2
                    break
                output.append("\n" if source[index] == "\n" else " ")
                index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def js_matching_bracket(source: str, opening_index: int) -> int:
    pairs = {"(": ")", "[": "]", "{": "}"}
    opening = source[opening_index]
    if opening not in pairs:
        raise ValidationError("expected a JavaScript opening bracket")
    stack: list[str] = []
    quote: str | None = None
    escaped = False
    for index in range(opening_index, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif char in pairs.values():
            if not stack or char != stack.pop():
                raise ValidationError("unbalanced JavaScript configuration")
            if not stack:
                return index
    raise ValidationError("unbalanced JavaScript configuration")


def split_js_top_level(source: str) -> list[str]:
    parts: list[str] = []
    start = 0
    stack: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    quote: str | None = None
    escaped = False
    for index, char in enumerate(source):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char in pairs:
            stack.append(pairs[char])
        elif char in pairs.values():
            if stack and char == stack[-1]:
                stack.pop()
        elif char == "," and not stack:
            parts.append(source[start:index].strip())
            start = index + 1
    tail = source[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def normalize_js(source: str) -> str:
    output: list[str] = []
    quote: str | None = None
    escaped = False
    pending_space = False
    for char in source.strip():
        if quote:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            if pending_space and output and output[-1] not in "([{,:":
                output.append(" ")
            pending_space = False
            quote = char
            output.append(char)
        elif char.isspace():
            pending_space = True
        else:
            if pending_space and output and output[-1] not in "([{,:" and char not in ")]},;:":
                output.append(" ")
            pending_space = False
            output.append(char)
    return "".join(output)


def js_object_properties(value: str) -> dict[str, str]:
    value = strip_javascript_comments(value).strip()
    if not value.startswith("{"):
        return {}
    try:
        closing = js_matching_bracket(value, 0)
    except ValidationError:
        return {}
    properties: dict[str, str] = {}
    for item in split_js_top_level(value[1:closing]):
        match = re.match(r"\s*(?:(['\"])(.*?)\1|([A-Za-z_$][\w$-]*|\d+))\s*:\s*", item, flags=re.S)
        if match:
            properties[match.group(2) or match.group(3)] = item[match.end() :].strip()
    return properties


def js_array_items(value: str) -> list[str]:
    value = strip_javascript_comments(value).strip()
    if not value.startswith("["):
        return []
    try:
        closing = js_matching_bracket(value, 0)
    except ValidationError:
        return []
    return split_js_top_level(value[1:closing])


def js_literal_string(value: str) -> str | None:
    match = re.fullmatch(r"\s*(['\"])(.*?)\1\s*", value, flags=re.S)
    return match.group(2) if match else None


def js_array_strings_from_value(value: str | None) -> list[str]:
    if not value:
        return []
    strings: list[str] = []
    for item in js_array_items(value):
        literal = js_literal_string(item)
        if literal is not None:
            strings.append(literal)
    return strings


def exported_js_object(source: str) -> str | None:
    source = strip_javascript_comments(source)
    matches = [
        re.search(r"\bmodule\s*\.\s*exports\s*=", source),
        re.search(r"\bexport\s+default\b", source),
    ]
    match = next((candidate for candidate in matches if candidate), None)
    if not match:
        return None
    opening = source.find("{", match.end())
    if opening < 0:
        return None
    try:
        closing = js_matching_bracket(source, opening)
    except ValidationError:
        return None
    return source[opening : closing + 1]


def module_specifiers(source: str, suffix: str = "") -> set[str]:
    segments = [source]
    if suffix.lower() == ".vue":
        segments = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", source, flags=re.I | re.S)
    try:
        return {
            specifier
            for segment in segments
            for specifier in javascript_module_specifiers(segment)
        }
    except JavaScriptScanError as error:
        raise ValidationError(str(error)) from error


def bare_imports(source: str, suffix: str = "") -> set[str]:
    imports: set[str] = set()
    for specifier in module_specifiers(source, suffix):
        if specifier.startswith((".", "/", "#", "node:")):
            continue
        parts = specifier.split("/")
        package = "/".join(parts[:2]) if specifier.startswith("@") else parts[0]
        if package not in NODE_BUILTINS:
            imports.add(package)
    return imports


def source_files(root: Path) -> list[Path]:
    extensions = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue"}
    if not root.is_dir():
        return []
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and "node_modules" not in path.parts
        and path.suffix.lower() in extensions
    ]


def resolve_local_javascript(source_path: Path, specifier: str, package_root: Path) -> Path | None:
    if not specifier.startswith("."):
        return None
    clean_specifier = specifier.split("?", 1)[0].split("#", 1)[0]
    candidate = (source_path.parent / clean_specifier).resolve()
    choices = [candidate]
    if not candidate.suffix:
        suffixes = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".json")
        choices.extend(candidate.with_suffix(suffix) for suffix in suffixes)
        choices.extend(candidate / f"index{suffix}" for suffix in suffixes)
    for choice in choices:
        try:
            choice.relative_to(package_root.resolve())
        except ValueError:
            continue
        if choice.is_file() and not choice.is_symlink():
            return choice
    return None


def javascript_contract_files(
    package_root: Path,
    package_assets_directory: str,
) -> list[Path]:
    assets_path = Path(package_assets_directory)
    if assets_path.is_absolute() or not assets_path.parts or ".." in assets_path.parts:
        return []
    package_assets_root = package_root / assets_path
    initial = set(source_files(package_assets_root))
    for pattern in (
        "*.config.js",
        "*.config.jsx",
        "*.config.mjs",
        "*.config.cjs",
        "*.config.ts",
        "*.config.tsx",
        "*.config.mts",
        "*.config.cts",
    ):
        initial.update(path for path in package_root.glob(pattern) if path.is_file() and not path.is_symlink())
    queue = list(initial)
    discovered = set(initial)
    while queue:
        source_path = queue.pop()
        source = source_path.read_text(encoding="utf-8", errors="ignore")
        for specifier in module_specifiers(source, source_path.suffix):
            resolved = resolve_local_javascript(source_path, specifier, package_root)
            if resolved and resolved not in discovered:
                discovered.add(resolved)
                queue.append(resolved)
    return sorted(discovered)


def javascript_module_aliases(source: str) -> dict[str, str]:
    source = strip_javascript_comments(source)
    aliases: dict[str, str] = {}
    patterns = (
        r"\bimport\s+([A-Za-z_$][\w$]*)\s*(?:,\s*\{[^;]*?\})?\s+from\s+['\"]([^'\"]+)['\"]",
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, source, flags=re.S):
            aliases[match.group(1)] = match.group(2)
    return aliases


def vite_contract(source: str) -> dict[str, Any] | None:
    source = strip_javascript_comments(source)
    aliases = javascript_module_aliases(source)
    tokens = javascript_tokens(source)
    if any(token.kind == "invalid" for token in tokens):
        return None
    laravel_bindings = _javascript_default_import_bindings(tokens, "laravel-vite-plugin")
    plugin_objects: list[tuple[str, dict[str, str]]] = []
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.value not in laravel_bindings:
            continue
        if index and tokens[index - 1].value in {".", "#"}:
            continue
        if (
            index + 2 >= len(tokens)
            or tokens[index + 1].value != "("
            or tokens[index + 2].value != "{"
        ):
            continue
        closing_index = _javascript_matching_token(tokens, index + 2)
        if closing_index is None:
            continue
        opening = tokens[index + 2].start
        closing = tokens[closing_index].end
        properties = js_object_properties(source[opening:closing])
        if properties:
            plugin_objects.append((token.value, properties))
    configured = next(
        (
            (identity, properties)
            for identity, properties in plugin_objects
            if {"input", "buildDirectory", "publicDirectory"}.issubset(properties)
        ),
        None,
    )
    if not configured:
        return None
    identity, properties = configured
    plugin_identities: list[str] = []
    for match in re.finditer(r"\bplugins\s*:\s*\[", source):
        opening = source.find("[", match.start())
        try:
            closing = js_matching_bracket(source, opening)
        except ValidationError:
            continue
        items = js_array_items(source[opening : closing + 1])
        identities: list[str] = []
        for item in items:
            call = re.match(r"\s*([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)*)\s*\(", item)
            if call:
                identities.append(re.sub(r"\s+", "", call.group(1)))
        if identity in identities:
            plugin_identities = identities
            break
    def canonical_plugin(plugin_identity: str) -> str:
        root_identity = plugin_identity.split(".", maxsplit=1)[0]
        return aliases.get(root_identity, plugin_identity)

    return {
        "hot_file": js_literal_string(properties.get("hotFile", "")),
        "public_directory": js_literal_string(properties.get("publicDirectory", "")),
        "build_directory": js_literal_string(properties.get("buildDirectory", "")),
        "input": js_array_strings_from_value(properties.get("input")),
        "plugins": [canonical_plugin(plugin_identity) for plugin_identity in plugin_identities],
        "asset_plugin": "laravel-vite-plugin",
    }


def tailwind_contract(source: str) -> dict[str, Any] | None:
    exported = exported_js_object(source)
    if not exported:
        return None
    properties = js_object_properties(exported)
    if not {"content", "theme", "plugins"}.issubset(properties):
        return None
    theme_properties = js_object_properties(properties["theme"])
    return {
        "content": js_array_strings_from_value(properties["content"]),
        "theme": theme_properties,
        "plugins": [normalize_js(item) for item in js_array_items(properties["plugins"])],
        "safelist": [normalize_js(item) for item in js_array_items(properties.get("safelist", "[]"))],
    }


def vite_config_path(package_root: Path) -> Path | None:
    return next(
        (
            path
            for path in (
                package_root / "vite.config.js",
                package_root / "vite.config.ts",
                package_root / "vite.config.mjs",
                package_root / "vite.config.cjs",
                package_root / "vite.config.mts",
                package_root / "vite.config.cts",
            )
            if path.is_file()
        ),
        None,
    )


def strip_template_comments(source: str) -> str:
    source = re.sub(r"\{\{--.*?--\}\}", "", source, flags=re.S)
    source = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    return strip_php_comments(source)


def template_region(source: str, position: int) -> str:
    head_open = re.search(r"<head\b", source, flags=re.I)
    head_close = re.search(r"</head\s*>", source, flags=re.I)
    body_open = re.search(r"<body\b", source, flags=re.I)
    body_close = re.search(r"</body\s*>", source, flags=re.I)
    if head_open and head_close and head_open.start() <= position <= head_close.end():
        return "head"
    if body_open and body_close and body_open.start() <= position <= body_close.end():
        return "body"
    return "document"


def template_calls(source: str, pattern: str, include_name: bool = False) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    for match in re.finditer(pattern, source):
        opening = source.find("(", match.start(), match.end() + 1)
        if opening < 0:
            continue
        try:
            closing = matching_bracket(source, opening)
        except ValidationError:
            continue
        arguments = normalize_js(source[opening + 1 : closing])
        name = re.sub(r"\s+", "", match.group(1)) if include_name else ""
        value = f"{name}({arguments})" if include_name else arguments
        calls.append((value, template_region(source, match.start())))
    return calls


def php_props_contract(source: str) -> dict[str, str]:
    match = re.search(r"@props\s*\(", source)
    if not match:
        return {}
    opening = source.find("(", match.start())
    try:
        closing = matching_bracket(source, opening)
    except ValidationError:
        return {}
    arguments = source[opening + 1 : closing].strip()
    if arguments.startswith("["):
        try:
            arguments = arguments[1 : matching_bracket(arguments, 0)]
        except ValidationError:
            return {}
    props: dict[str, str] = {}
    for item in split_js_top_level(arguments):
        prop = re.match(r"\s*(['\"])(.*?)\1\s*=>\s*(.*?)\s*$", item, flags=re.S)
        if prop:
            props[prop.group(2)] = normalize_js(prop.group(3))
    return props


def layout_contract(source: str) -> dict[str, Any]:
    source = strip_template_comments(source)
    main_match = re.search(r"<main\b[^>]*\bid\s*=\s*['\"]([^'\"]+)", source, flags=re.I)
    meta_contract: set[str] = set()
    for tag in re.findall(r"<meta\b[^>]*>", source, flags=re.I | re.S):
        for attribute in ("charset", "name", "http-equiv"):
            match = re.search(rf"\b{attribute}\s*=\s*['\"]([^'\"]+)", tag, flags=re.I)
            if match:
                meta_contract.add(f"{attribute.lower()}:{match.group(1).lower()}")
    ids = set(re.findall(r"\bid\s*=\s*['\"]([^'\"]+)", source, flags=re.I))
    fragment_links = set(re.findall(r"<a\b[^>]*\bhref\s*=\s*['\"]#([^'\"]+)", source, flags=re.I | re.S))
    components = set(re.findall(r"<x-([A-Za-z0-9_:.-]+)", source))
    config_keys = set(re.findall(r"getConfigData\(\s*['\"]([^'\"]+)", source))
    return {
        "events": template_calls(source, r"\bview_render_event\s*\("),
        "stacks": template_calls(source, r"@stack\s*\("),
        "vite_directives": template_calls(source, r"@(\w*[Vv]ite\w*)\s*\(", include_name=True),
        "mounts": template_calls(source, r"\b([A-Za-z_$][\w$]*\s*\.\s*mount)\s*\(", include_name=True),
        "props": php_props_contract(source),
        "meta": meta_contract,
        "components": components,
        "config_keys": config_keys,
        "ids": ids,
        "fragment_links": fragment_links,
        "main_id": main_match.group(1) if main_match else None,
        "has_doctype": bool(re.search(r"<!doctype\s+html\s*>", source, flags=re.I)),
        "has_title": bool(re.search(r"<title\b[^>]*>.*?</title\s*>", source, flags=re.I | re.S)),
        "has_slot": bool(re.search(r"\$slot\b", source)),
        "has_html_lang": bool(re.search(r"<html\b[^>]*\blang\s*=", source, flags=re.I | re.S)),
        "has_html_dir": bool(re.search(r"<html\b[^>]*\bdir\s*=", source, flags=re.I | re.S)),
    }


def ordered_contract_missing(expected: list[Any], actual: list[Any]) -> list[Any]:
    cursor = 0
    missing: list[Any] = []
    for item in expected:
        try:
            cursor = actual.index(item, cursor) + 1
        except ValueError:
            missing.append(item)
    return missing


def layout_contract_issues(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key, label in (("events", "ordered render events"), ("stacks", "ordered Blade stacks"), ("vite_directives", "asset directives")):
        if ordered_contract_missing(expected[key], actual[key]):
            issues.append(label)
    if expected["mounts"] != actual["mounts"]:
        issues.append("Vue mount calls")
    for key, label in (("meta", "metadata"), ("components", "layout components"), ("config_keys", "runtime configuration hooks")):
        if expected[key] - actual[key]:
            issues.append(label)
    missing_props = [
        name
        for name, default in expected["props"].items()
        if actual["props"].get(name) != default
    ]
    if missing_props:
        issues.append("layout props/defaults")
    if expected["main_id"] and expected["main_id"] != actual["main_id"]:
        issues.append(f"main landmark id ({expected['main_id']})")
    for key, label in (
        ("has_doctype", "HTML doctype"),
        ("has_title", "document title"),
        ("has_slot", "Blade slot"),
        ("has_html_lang", "html lang attribute"),
        ("has_html_dir", "html dir attribute"),
    ):
        if expected[key] and not actual[key]:
            issues.append(label)
    missing_fragments = expected["fragment_links"] - actual["fragment_links"]
    broken_fragments = {fragment for fragment in actual["fragment_links"] if fragment not in actual["ids"]}
    if missing_fragments or broken_fragments:
        issues.append("in-page accessibility targets")
    return issues


def flattened_js_object(value: str, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], str]:
    properties = js_object_properties(value)
    if not properties:
        return {prefix: normalize_js(value)} if prefix else {}
    flattened: dict[tuple[str, ...], str] = {}
    for key, child in properties.items():
        child_properties = js_object_properties(child)
        if child_properties:
            flattened.update(flattened_js_object(child, (*prefix, key)))
        else:
            flattened[(*prefix, key)] = normalize_js(child)
    return flattened


def tailwind_contract_issues(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    missing_content = [pattern for pattern in expected["content"] if pattern not in actual["content"]]
    if missing_content:
        issues.append("content globs (" + ", ".join(missing_content) + ")")

    for section, expected_value in expected["theme"].items():
        actual_value = actual["theme"].get(section)
        if actual_value is None:
            issues.append(f"theme.{section}")
            continue
        expected_leaves = flattened_js_object(expected_value, (section,))
        actual_leaves = flattened_js_object(actual_value, (section,))
        if section == "extend":
            missing_paths = sorted(set(expected_leaves) - set(actual_leaves))
            if missing_paths:
                issues.append("theme.extend keys (" + ", ".join(".".join(path) for path in missing_paths) + ")")
        else:
            changed_paths = sorted(
                path
                for path, value in expected_leaves.items()
                if actual_leaves.get(path) != value
            )
            if changed_paths:
                issues.append("theme values (" + ", ".join(".".join(path) for path in changed_paths) + ")")

    if ordered_contract_missing(expected["plugins"], actual["plugins"]):
        issues.append("plugins")
    if ordered_contract_missing(expected["safelist"], actual["safelist"]):
        issues.append("safelist")
    return issues


def glob_references_root(pattern: str, config_root: Path, target_root: Path) -> bool:
    static_prefix = re.split(r"[*?\[{]", pattern, maxsplit=1)[0].rstrip("/") or "."
    prefix_path = (config_root / static_prefix).resolve()
    target_root = target_root.resolve()
    try:
        prefix_path.relative_to(target_root)
        return True
    except ValueError:
        try:
            target_root.relative_to(prefix_path)
            return True
        except ValueError:
            return False


def manifest_contract_issues(manifest: Any, build_root: Path, required_entries: list[str]) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest root is not an object"]
    issues: list[str] = []
    for entry in required_entries:
        record = manifest.get(entry)
        if not isinstance(record, dict):
            issues.append(f"missing entry {entry}")
        elif record.get("isEntry") is not True:
            issues.append(f"{entry} is not marked as an entry")

    build_root = build_root.resolve()
    for key, record in manifest.items():
        if not isinstance(record, dict):
            issues.append(f"record {key} is not an object")
            continue
        file_value = record.get("file")
        if not isinstance(file_value, str):
            issues.append(f"record {key} has no output file")
        else:
            output_values = [file_value]
            for field in ("css", "assets"):
                values = record.get(field, [])
                if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                    issues.append(f"record {key} has an invalid {field} list")
                    continue
                output_values.extend(values)
            for output in output_values:
                output_path = Path(output)
                if output_path.is_absolute() or ".." in output_path.parts or "\\" in output:
                    issues.append(f"record {key} has an unsafe output path {output}")
                    continue
                resolved = (build_root / output_path).resolve()
                try:
                    resolved.relative_to(build_root)
                except ValueError:
                    issues.append(f"record {key} escapes the build directory: {output}")
                    continue
                if not resolved.is_file():
                    issues.append(f"record {key} references missing output {output}")
        for field in ("imports", "dynamicImports"):
            references = record.get(field, [])
            if not isinstance(references, list) or not all(isinstance(value, str) for value in references):
                issues.append(f"record {key} has an invalid {field} list")
                continue
            for reference in references:
                if reference not in manifest:
                    issues.append(f"record {key} references missing manifest key {reference}")
    return issues


def discover_master_layout(views_root: Path) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for path in views_root.rglob("*.blade.php"):
        if not path.is_file() or path.is_symlink():
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"<html\b", source, flags=re.I) or not re.search(r"\bapp\s*\.\s*mount\s*\(", source):
            continue
        contract = layout_contract(source)
        score = sum(
            (
                contract["has_doctype"],
                contract["has_title"],
                contract["has_slot"],
                bool(contract["main_id"]),
                bool(contract["vite_directives"]),
                bool(contract["events"]),
            )
        )
        candidates.append((score, path))
    if not candidates:
        return None
    best_score = max(score for score, _ in candidates)
    best = sorted(path for score, path in candidates if score == best_score)
    return best[0] if len(best) == 1 else None


def theme_baseline_path(package_root: Path | None, views_root: Path) -> Path | None:
    candidates = (
        (package_root / ".bagisto-theme-baseline.json",)
        if package_root
        else (
            views_root / ".bagisto-theme-baseline.json",
            views_root.parent / ".bagisto-theme-baseline.json",
        )
    )
    matches = [path for path in candidates if path.is_file()]
    if len(matches) > 1:
        raise ValidationError(
            "multiple accepted baselines exist for this theme source: "
            + ", ".join(str(path) for path in matches)
        )
    return matches[0] if matches else None


def baseline_problem_paths(analysis: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    if analysis["summary"].get("version_changed"):
        paths.append(
            "Bagisto version "
            f"{analysis['versions']['baseline']} -> {analysis['versions']['installed']}"
        )
    if analysis["summary"].get("version_unverifiable"):
        paths.append(
            "Bagisto version comparison unavailable "
            f"({analysis['versions']['baseline']} -> {analysis['versions']['installed']})"
        )
    if analysis["summary"].get("asset_topology_changed"):
        paths.append(
            "Shop asset root "
            f"{analysis['asset_directories']['baseline']} -> "
            f"{analysis['asset_directories']['installed']}"
        )
    for section, result in analysis["shop_inventory"].items():
        for classification in ("upstream_changed", "upstream_missing", "upstream_added"):
            paths.extend(
                f"{section}/{relative} ({classification.replace('_', ' ')})"
                for relative in result[classification]
            )
    for section, result in analysis["sections"].items():
        for classification in ("concurrent_changes", "theme_missing", "theme_untracked"):
            paths.extend(
                f"{section}/{relative} ({classification.replace('_', ' ')})"
                for relative in result[classification]
            )
    for section, missing in analysis["ownership_missing"].items():
        paths.extend(f"{section}/{relative} (required ownership missing)" for relative in missing)
    return paths


def check_upgrade_baseline(
    findings: list[Finding],
    package_root: Path | None,
    views_root: Path,
    shop_root: Path,
    theme_code: str,
) -> None:
    path = theme_baseline_path(package_root, views_root)
    expected_path = package_root / ".bagisto-theme-baseline.json" if package_root else views_root.parent / ".bagisto-theme-baseline.json"
    if path is None:
        add(
            findings,
            "warn",
            "upgrade.baseline",
            "theme has no accepted Shop inventory/source baseline; upgrade drift is not auditable",
            expected_path,
        )
        return
    try:
        analysis = analyze_baseline(
            path,
            views_root,
            shop_views_root(shop_root),
            theme_code,
        )
    except (ComparisonError, OSError) as error:
        add(findings, "fail", "upgrade.baseline", f"invalid theme baseline: {error}", path)
        return

    summary = analysis["summary"]
    problem_keys = (
        "upstream_changed",
        "upstream_missing",
        "upstream_added",
        "theme_missing",
        "theme_untracked",
        "ownership_missing",
        "version_changed",
        "version_unverifiable",
        "asset_topology_changed",
    )
    if any(summary[key] for key in problem_keys):
        details = baseline_problem_paths(analysis)
        counts = ", ".join(f"{key.replace('_', ' ')}={summary[key]}" for key in problem_keys if summary[key])
        sample = "; ".join(details[:10])
        suffix = f"; +{len(details) - 10} more" if len(details) > 10 else ""
        add(
            findings,
            "fail",
            "upgrade.baseline",
            f"baseline requires reconciliation ({counts}): {sample}{suffix}",
            path,
        )
    else:
        add(
            findings,
            "pass",
            "upgrade.baseline",
            "theme-owned hashes and the installed Shop view/asset/discovered-build-contract inventory match the accepted baseline",
            path,
        )


def check_package(
    findings: list[Finding],
    root: Path,
    package_root: Path,
    code: str,
    config: dict[str, str | None],
    shop_root: Path,
) -> Path:
    composer_path = package_root / "composer.json"
    composer_registered = False
    root_composer = json.loads((root / "composer.json").read_text(encoding="utf-8"))
    registered_paths = {
        str(value).rstrip("/")
        for value in root_composer.get("autoload", {}).get("psr-4", {}).values()
    }
    expected_path = str((package_root / "src").relative_to(root)).rstrip("/")
    bootstrap_path = root / "bootstrap/providers.php"
    bootstrap = (
        strip_php_comments(bootstrap_path.read_text(encoding="utf-8", errors="ignore"))
        if bootstrap_path.is_file()
        else ""
    )
    provider_names = [path.stem for path in (package_root / "src/Providers").glob("*ServiceProvider.php")]
    locally_registered = expected_path in registered_paths and any(
        re.search(rf"\b{re.escape(name)}\s*::\s*class\b", bootstrap)
        for name in provider_names
    )
    if not composer_path.is_file():
        if locally_registered:
            add(
                findings,
                "pass",
                "package.local-registration",
                "root Composer autoload and bootstrap provider register this application-local package",
                root / "composer.json",
            )
            add(
                findings,
                "warn",
                "package.distribution",
                "package has no Composer manifest and is not independently distributable",
                composer_path,
            )
        else:
            add(findings, "fail", "package.composer", "package composer.json or complete local registration is missing", composer_path)
    else:
        try:
            composer = json.loads(composer_path.read_text(encoding="utf-8"))
            psr4 = composer.get("autoload", {}).get("psr-4", {})
            providers = composer.get("extra", {}).get("laravel", {}).get("providers", [])
            if psr4:
                add(findings, "pass", "package.composer", "Composer PSR-4 autoload metadata exists", composer_path)
            else:
                add(findings, "fail", "package.autoload", "Composer PSR-4 autoload mapping is missing", composer_path)

            package_name = composer.get("name")
            installed_names: set[str] = set()
            installed_path = root / "vendor/composer/installed.json"
            if installed_path.is_file():
                installed_data = json.loads(installed_path.read_text(encoding="utf-8"))
                installed_records = installed_data.get("packages", []) if isinstance(installed_data, dict) else installed_data
                if isinstance(installed_records, list):
                    installed_names = {
                        str(record.get("name"))
                        for record in installed_records
                        if isinstance(record, dict) and record.get("name")
                    }
            composer_registered = bool(
                package_name
                and (
                    package_name in root_composer.get("require", {})
                    or package_name in root_composer.get("require-dev", {})
                    or package_name in installed_names
                )
            )
            if composer_registered and locally_registered:
                add(
                    findings,
                    "fail",
                    "package.registration",
                    "package is both Composer-installed and locally registered; choose exactly one provider strategy",
                    root / "composer.json",
                )
            elif composer_registered and not providers:
                add(
                    findings,
                    "fail",
                    "package.discovery",
                    "Composer-installed package does not declare its Laravel service provider",
                    composer_path,
                )
            elif composer_registered:
                add(findings, "pass", "package.registration", "Composer installation and Laravel discovery load the package", composer_path)
            elif locally_registered:
                add(findings, "pass", "package.registration", "root autoload and bootstrap provider register the local package", root / "composer.json")
            else:
                add(
                    findings,
                    "fail",
                    "package.registration",
                    "package metadata exists but the host neither installs it nor registers local autoload/provider wiring",
                    root / "composer.json",
                )

            package_require = composer.get("require", {})
            laravel_constraint = package_require.get("illuminate/support") or package_require.get("laravel/framework")
            bagisto_constraint = package_require.get("bagisto/bagisto") or package_require.get("bagisto/laravel-shop")
            if not laravel_constraint:
                add(
                    findings,
                    "fail" if composer_registered else "warn",
                    "package.laravel-compatibility",
                    "package declares no Laravel support constraint",
                    composer_path,
                )
            if composer_registered and not bagisto_constraint:
                add(findings, "fail", "package.bagisto-compatibility", "distributed package declares no supported Bagisto range", composer_path)
            elif bagisto_constraint and laravel_constraint:
                add(findings, "pass", "package.compatibility", "package declares Laravel and Bagisto compatibility ranges", composer_path)
            elif not composer_registered and laravel_constraint:
                add(
                    findings,
                    "pass",
                    "package.compatibility",
                    "application-local package inherits the tested Bagisto checkout; record its source baseline",
                    composer_path,
                )

            license_value = composer.get("license")
            theme_license_file = package_root / "LICENSE"
            if license_value and theme_license_file.is_file() and not theme_license_file.is_symlink():
                add(
                    findings,
                    "pass",
                    "package.theme-license",
                    "Composer license metadata and full theme license text are present",
                    theme_license_file,
                )
            else:
                add(
                    findings,
                    "fail" if composer_registered else "warn",
                    "package.theme-license",
                    "choose the theme package license and include matching Composer metadata and full LICENSE text before distribution",
                    composer_path,
                )
        except json.JSONDecodeError as error:
            add(findings, "fail", "package.composer", f"invalid JSON: {error}", composer_path)

    upstream_license = package_root / "UPSTREAM-LICENSES/BAGISTO-LICENSE"
    upstream_notice = package_root / "UPSTREAM-NOTICES.md"
    if (
        upstream_license.is_file()
        and not upstream_license.is_symlink()
        and upstream_notice.is_file()
        and not upstream_notice.is_symlink()
    ):
        add(
            findings,
            "pass",
            "package.upstream-license",
            "copied/derived Bagisto sources retain an upstream license and notice",
            upstream_license,
        )
    else:
        add(
            findings,
            "fail" if composer_registered else "warn",
            "package.upstream-license",
            "retain the exact installed Bagisto license and an upstream notice before distribution",
            upstream_license,
        )

    providers = list((package_root / "src/Providers").glob("*ServiceProvider.php"))
    provider_text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in providers)
    active_provider_text = strip_template_comments(provider_text)
    published_views = resolve_project_path(root, config.get("views_path"))
    views_namespace = config.get("views_namespace")
    if isinstance(views_namespace, str) and views_namespace:
        namespace_roots = registered_namespace_roots(root, views_namespace, package_root)
        if len(namespace_roots) > 1:
            add(
                findings,
                "fail",
                "package.views-namespace",
                "configured view namespace is registered by multiple packages: "
                + ", ".join(str(path) for path in sorted(namespace_roots)),
                root / "config/themes.php",
            )
    if not providers:
        add(findings, "fail", "package.provider", "theme service provider is missing", package_root / "src/Providers")
    elif views_namespace and re.search(
        rf"loadViewsFrom\s*\([^;]*['\"]{re.escape(views_namespace)}['\"]\s*\)",
        active_provider_text,
        flags=re.S,
    ):
        add(findings, "pass", "package.views", "provider registers the theme view namespace", providers[0])
    elif "publishes" in active_provider_text and published_views and published_views.is_dir():
        add(findings, "pass", "package.views", "provider publishing workflow has an available configured view path", providers[0])
    else:
        add(findings, "fail", "package.views", "provider neither registers a usable namespace nor supplies the configured published views", providers[0])

    translations_root = package_root / "src/Resources/lang"
    if translations_root.is_dir():
        translation_namespaces = re.findall(
            r"loadTranslationsFrom\s*\(\s*[^,]+,\s*['\"]([^'\"]+)['\"]\s*\)",
            active_provider_text,
            flags=re.S,
        )
        unsafe_namespaces = {"shop", "theme", "messages", "validation"}
        if not translation_namespaces:
            add(
                findings,
                "fail",
                "package.translations",
                "package language files exist but the provider does not call loadTranslationsFrom",
                translations_root,
            )
        elif any(namespace in unsafe_namespaces for namespace in translation_namespaces):
            add(
                findings,
                "fail",
                "package.translations",
                "translation namespace is generic or collides with a core namespace",
                providers[0],
            )
        else:
            add(
                findings,
                "pass",
                "package.translations",
                "package-owned translations use a registered package-specific namespace",
                translations_root,
            )

    package_json_path = package_root / "package.json"
    if not package_json_path.is_file():
        add(findings, "fail", "assets.package-json", "package.json is missing", package_json_path)
    else:
        try:
            package_json = json.loads(package_json_path.read_text(encoding="utf-8"))
            declared: set[str] = set()
            for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                values = package_json.get(field, {})
                if isinstance(values, dict):
                    declared.update(values)
            imported: set[str] = set()
            for source_path in javascript_contract_files(
                package_root,
                str(config.get("package_assets_directory") or ""),
            ):
                imported |= bare_imports(
                    source_path.read_text(encoding="utf-8", errors="ignore"),
                    source_path.suffix,
                )
            missing = imported - declared
            shop_package = json.loads((shop_root / "package.json").read_text(encoding="utf-8"))
            shop_declared: set[str] = set()
            for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                values = shop_package.get(field, {})
                if isinstance(values, dict):
                    shop_declared.update(values)
            shop_imported: set[str] = set()
            discovered_shop_assets = shop_assets_root(shop_root).relative_to(shop_root).as_posix()
            for source_path in javascript_contract_files(shop_root, discovered_shop_assets):
                shop_imported |= bare_imports(
                    source_path.read_text(encoding="utf-8", errors="ignore"),
                    source_path.suffix,
                )
            inherited_missing = shop_imported - shop_declared
            theme_only_missing = sorted(missing - inherited_missing)
            baseline_missing = sorted(missing & inherited_missing)
            if theme_only_missing:
                add(
                    findings,
                    "fail",
                    "assets.dependencies",
                    "theme-only undeclared runtime/build imports: " + ", ".join(theme_only_missing),
                    package_json_path,
                )
            else:
                add(findings, "pass", "assets.dependencies", "runtime and build-config imports are declared", package_json_path)
            if baseline_missing:
                add(
                    findings,
                    "warn",
                    "assets.upstream-dependencies",
                    "installed Shop itself relies on transitive imports: " + ", ".join(baseline_missing),
                    shop_root / "package.json",
                )
        except json.JSONDecodeError as error:
            add(findings, "fail", "assets.package-json", f"invalid JSON: {error}", package_json_path)

    vite_path = vite_config_path(package_root)
    shop_vite_path = vite_config_path(shop_root)
    if not vite_path:
        add(findings, "fail", "assets.vite", "Vite configuration is missing", package_root)
    elif not shop_vite_path:
        add(findings, "fail", "assets.vite-baseline", "installed Shop Vite configuration was not found", shop_root)
    else:
        vite = vite_path.read_text(encoding="utf-8", errors="ignore")
        shop_vite = shop_vite_path.read_text(encoding="utf-8", errors="ignore")
        theme_vite_contract = vite_contract(vite)
        shop_vite_contract = vite_contract(shop_vite)
        if not shop_vite_contract or not shop_vite_contract["input"] or not shop_vite_contract["plugins"]:
            add(findings, "fail", "assets.vite-baseline", "could not structurally derive the installed Shop Vite contract", shop_vite_path)
        elif not theme_vite_contract:
            add(findings, "fail", "assets.vite", "could not structurally derive the theme Vite contract", vite_path)
        else:
            vite_issues: list[str] = []
            missing_entries = [entry for entry in shop_vite_contract["input"] if entry not in theme_vite_contract["input"]]
            if missing_entries:
                vite_issues.append("entry points (" + ", ".join(missing_entries) + ")")
            if ordered_contract_missing(shop_vite_contract["plugins"], theme_vite_contract["plugins"]):
                vite_issues.append("installed plugin pipeline/order")

            hot_file = theme_vite_contract["hot_file"]
            expected_hot_file = root / "public" / str(config.get("hot_file") or "")
            if not hot_file or (package_root / hot_file).resolve() != expected_hot_file.resolve():
                vite_issues.append("hotFile path")
            public_directory = theme_vite_contract["public_directory"]
            if not public_directory or (package_root / public_directory).resolve() != (root / "public").resolve():
                vite_issues.append("publicDirectory path")
            if theme_vite_contract["build_directory"] != config.get("build_directory"):
                vite_issues.append("buildDirectory value")

            configured_assets = config.get("package_assets_directory")
            assets_root = (package_root / str(configured_assets or "")).resolve()
            for entry in theme_vite_contract["input"]:
                entry_path = (package_root / entry).resolve()
                try:
                    entry_path.relative_to(assets_root)
                except ValueError:
                    vite_issues.append(f"entry outside package_assets_directory ({entry})")
                    continue
                if not entry_path.is_file():
                    vite_issues.append(f"missing entry source ({entry})")

            if vite_issues:
                add(findings, "fail", "assets.vite", "Vite contract mismatch: " + "; ".join(vite_issues), vite_path)
            else:
                add(findings, "pass", "assets.vite", "Vite paths, inputs, and plugin order match the target-derived contract", vite_path)

    tailwind_candidates = [
        package_root / "tailwind.config.js",
        package_root / "tailwind.config.cjs",
        package_root / "tailwind.config.mjs",
        package_root / "tailwind.config.ts",
        package_root / "tailwind.config.mts",
        package_root / "tailwind.config.cts",
    ]
    tailwind_path = next((path for path in tailwind_candidates if path.is_file()), None)
    shop_tailwind_path = next(
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
    if not shop_tailwind_path:
        add(findings, "warn", "assets.tailwind-baseline", "installed Shop has no Tailwind contract to compare", shop_root)
    elif not tailwind_path:
        add(findings, "fail", "assets.tailwind", "theme omits the Tailwind config used by the installed Shop", package_root)
    else:
        tailwind = tailwind_contract(tailwind_path.read_text(encoding="utf-8", errors="ignore"))
        shop_tailwind = tailwind_contract(shop_tailwind_path.read_text(encoding="utf-8", errors="ignore"))
        if not shop_tailwind:
            add(findings, "fail", "assets.tailwind-baseline", "could not structurally derive the installed Shop Tailwind contract", shop_tailwind_path)
        elif not tailwind:
            add(findings, "fail", "assets.tailwind", "could not structurally derive the theme Tailwind contract", tailwind_path)
        else:
            tailwind_issues = tailwind_contract_issues(shop_tailwind, tailwind)
            theme_views = package_root / "src/Resources/views"
            shop_views = shop_views_root(shop_root)
            theme_relatives = {
                path.relative_to(theme_views)
                for path in theme_views.rglob("*.blade.php")
                if path.is_file() and not path.is_symlink()
            } if theme_views.is_dir() else set()
            shop_relatives = {
                path.relative_to(shop_views)
                for path in shop_views.rglob("*.blade.php")
                if path.is_file() and not path.is_symlink()
            }
            if shop_relatives - theme_relatives and not any(
                glob_references_root(pattern, package_root, shop_root)
                for pattern in tailwind["content"]
            ):
                tailwind_issues.append("content glob for inherited Shop templates")
            if tailwind_issues:
                add(findings, "fail", "assets.tailwind", "Tailwind contract mismatch: " + "; ".join(tailwind_issues), tailwind_path)
            else:
                add(findings, "pass", "assets.tailwind", "Tailwind preserves installed content, token keys, responsive values, plugins, and safelist", tailwind_path)

    return package_root / "src/Resources/views"


def check_layout(findings: list[Finding], views_root: Path, shop_root: Path) -> None:
    shop_views = shop_views_root(shop_root)
    shop_layout = discover_master_layout(shop_views)
    if not shop_layout:
        add(findings, "fail", "layout.baseline", "could not uniquely derive the installed Shop master layout", shop_views)
        return
    layout = views_root / shop_layout.relative_to(shop_views)
    if not layout.is_file():
        add(findings, "pass", "layout.inheritance", "master layout is inherited from Shop", views_root)
        return

    expected = layout_contract(shop_layout.read_text(encoding="utf-8", errors="ignore"))
    actual = layout_contract(layout.read_text(encoding="utf-8", errors="ignore"))
    issues = layout_contract_issues(expected, actual)
    if issues:
        add(findings, "fail", "layout.runtime-contract", "custom layout drops or reorders installed contracts: " + "; ".join(issues), layout)
    else:
        add(findings, "pass", "layout.runtime-contract", "custom layout preserves target-derived document, Blade, asset, and Vue contracts", layout)


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []
    try:
        if not THEME_CODE_RE.fullmatch(args.theme_code):
            raise ValidationError("--theme-code must match [a-z][a-z0-9-]*")
        root = find_project_root(Path(args.project_root))
        shop_root = find_shop_root(root)
        add(findings, "pass", "project.root", "Bagisto project and installed Shop package found", root)

        try:
            config = theme_config(root, args.theme_code)
            missing_keys = [
                key
                for key in ("name", "assets_path", "views_path", "hot_file", "build_directory", "package_assets_directory")
                if not config.get(key)
            ]
            if missing_keys:
                add(findings, "fail", "theme.config", "theme config misses: " + ", ".join(missing_keys), root / "config/themes.php")
            else:
                add(findings, "pass", "theme.config", "theme and Vite configuration keys exist", root / "config/themes.php")
            if config.get("parent"):
                themes_source = (root / "config/themes.php").read_text(encoding="utf-8")
                shop_source = php_array_block(themes_source, "shop")
                parent_pattern = rf"['\"]{re.escape(str(config['parent']))}['\"]\s*=>\s*\["
                if re.search(parent_pattern, shop_source):
                    add(findings, "pass", "theme.parent", "configured parent theme exists", root / "config/themes.php")
                else:
                    add(findings, "fail", "theme.parent", f"configured parent theme does not exist: {config['parent']}", root / "config/themes.php")
        except ValidationError as error:
            config = {}
            add(findings, "fail", "theme.config", str(error), root / "config/themes.php")

        package_root = find_package_root(root, args.package_dir, args.theme_code, config.get("build_directory"))
        views_path = resolve_project_path(root, config.get("views_path"))
        if package_root:
            if not package_root.is_dir():
                add(findings, "fail", "package.path", "package directory does not exist", package_root)
            else:
                add(findings, "pass", "package.path", "theme package found", package_root)
                views_path = check_package(findings, root, package_root, args.theme_code, config, shop_root)
                check_upgrade_baseline(
                    findings,
                    package_root,
                    views_path,
                    shop_root,
                    args.theme_code,
                )
        elif views_path and views_path.is_dir():
            add(findings, "pass", "overlay.path", "resource theme view directory exists", views_path)
            check_upgrade_baseline(
                findings,
                None,
                views_path,
                shop_root,
                args.theme_code,
            )
            if config.get("views_namespace"):
                add(
                    findings,
                    "fail",
                    "theme.namespace",
                    "views_namespace is configured but no registering package was discovered; pass --package-dir or fix registration",
                    root / "config/themes.php",
                )
        else:
            add(findings, "warn", "theme.source", "no package or published view directory was discovered")

        build_directory = config.get("build_directory")
        if build_directory:
            build_root = root / "public" / build_directory
            manifest = build_root / "manifest.json"
            entry_vite_path = vite_config_path(package_root) if package_root else vite_config_path(shop_root)
            entry_contract = (
                vite_contract(entry_vite_path.read_text(encoding="utf-8", errors="ignore"))
                if entry_vite_path
                else None
            )
            required_entries = entry_contract["input"] if entry_contract else []
            if not required_entries:
                add(findings, "fail", "assets.manifest-baseline", "could not derive configured theme manifest entries", entry_vite_path or package_root or shop_root)
            if manifest.is_file():
                try:
                    manifest_json = json.loads(manifest.read_text(encoding="utf-8"))
                    manifest_issues = manifest_contract_issues(manifest_json, build_root, required_entries)
                    if manifest_issues:
                        add(findings, "fail", "assets.manifest", "invalid production manifest: " + "; ".join(manifest_issues), manifest)
                    elif required_entries:
                        add(findings, "pass", "assets.manifest", "production manifest entries and emitted files are complete", manifest)
                except json.JSONDecodeError as error:
                    add(findings, "fail", "assets.manifest", f"invalid JSON: {error}", manifest)
            else:
                add(findings, "fail", "assets.manifest", "production manifest is absent; build before activation", manifest)

        if views_path and views_path.is_dir():
            check_layout(findings, views_path, shop_root)
            shop_views = shop_views_root(shop_root)
            identical, modified, theme_only, upstream_only = compare_views(views_path, shop_views)
            total_theme = identical + modified + theme_only
            if total_theme and identical / total_theme >= 0.8:
                baseline_note = (
                    "accepted baseline exists; reconcile this large ownership surface after every Shop upgrade"
                    if theme_baseline_path(package_root, views_path)
                    else "prefer sparse overrides or create an accepted upstream baseline after review"
                )
                add(
                    findings,
                    "warn",
                    "views.upgrade-drift",
                    f"{identical}/{total_theme} theme views are unchanged Shop copies; {baseline_note}",
                    views_path,
                )
            else:
                add(
                    findings,
                    "pass",
                    "views.override-scope",
                    f"views: {modified} modified, {identical} identical, {theme_only} theme-only, {upstream_only} inherited",
                    views_path,
                )

        hot_file = config.get("hot_file")
        if hot_file and (root / "public" / hot_file).exists():
            add(findings, "warn", "assets.hot-file", "Vite hot marker exists; remove it from production deployments", root / "public" / hot_file)

        bagisto_vite = root / "config/bagisto-vite.php"
        registry_source = bagisto_vite.read_text(encoding="utf-8", errors="ignore") if bagisto_vite.is_file() else ""
        registry_pattern = rf"['\"]{re.escape(args.theme_code)}['\"]\s*=>\s*\["
        if re.search(registry_pattern, registry_source):
            registry_block = php_array_block(php_array_block(registry_source, "viters"), args.theme_code)
            mismatched = [
                key
                for key in ("hot_file", "build_directory", "package_assets_directory")
                if config.get(key) != php_string(registry_block, key)
            ]
            if mismatched:
                add(findings, "fail", "assets.named-registry", "named Vite registry differs for: " + ", ".join(mismatched), bagisto_vite)
            else:
                add(findings, "pass", "assets.named-registry", "named Vite registry matches active-theme settings", bagisto_vite)
        elif package_root:
            add(
                findings,
                "warn",
                "assets.named-registry",
                "no named Vite registry found; add one only if templates call namespaced asset helpers",
                bagisto_vite,
            )

        add(
            findings,
            "warn",
            "runtime.external-state",
            "channel activation, localized theme_customizations, browser console/network health, checkout, accessibility, and performance require runtime tests",
        )

        summary = {
            level: sum(finding.level == level for finding in findings)
            for level in ("pass", "warn", "fail")
        }
        payload = {
            "project_root": str(root),
            "theme_code": args.theme_code,
            "summary": summary,
            "findings": [asdict(finding) for finding in findings],
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for finding in findings:
                location = f" [{finding.path}]" if finding.path else ""
                print(f"{finding.level.upper():4} {finding.check}: {finding.message}{location}")
            print(f"\n{summary['pass']} passed, {summary['warn']} warnings, {summary['fail']} failed")

        if summary["fail"]:
            return 2
        if args.strict and summary["warn"]:
            return 1
        return 0
    except (ValidationError, OSError, json.JSONDecodeError) as error:
        if args.json:
            print(json.dumps({"schema_version": 1, "error": str(error)}, indent=2))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
