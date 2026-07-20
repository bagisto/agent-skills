#!/usr/bin/env python3
"""Inspect a Bagisto storefront-theme environment without booting the application.

The script deliberately reads files only.  It does not execute PHP, query the
database, inspect environment secrets, install dependencies, or use the network.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple


EXIT_OK = 0
EXIT_NOT_FOUND = 3


class PackageDiscoveryError(RuntimeError):
    """Raised when one Composer identity resolves to multiple package roots."""
EXIT_INVALID = 4

SKIP_INSTRUCTION_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "public",
    "storage",
    "vendor",
}
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules"}
FRONTEND_PACKAGES = (
    "vite",
    "laravel-vite-plugin",
    "@vitejs/plugin-vue",
    "vue",
    "tailwindcss",
    "postcss",
    "autoprefixer",
    "axios",
    "vee-validate",
    "@vee-validate/rules",
    "@vee-validate/i18n",
    "mitt",
    "vue-flatpickr",
)


class ConfigParseError(ValueError):
    """Raised when a PHP config is outside the supported literal-array subset."""


class JavaScriptScanError(ValueError):
    """Raised when a JavaScript build contract cannot be scanned completely."""


class PhpArrayParser:
    """Parse the literal arrays used by Bagisto's checked-in config files.

    This is intentionally not a PHP evaluator.  Calls, constants, interpolation,
    and executable expressions are rejected instead of being run.
    """

    TOKEN_RE = re.compile(
        r"""
        (?P<space>\s+)
      | (?P<comment>//[^\n]*|\#[^\n]*|/\*.*?\*/)
      | (?P<arrow>=>)
      | (?P<string>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")
      | (?P<number>-?(?:\d+\.\d+|\d+))
      | (?P<identifier>[A-Za-z_][A-Za-z0-9_\\]*)
      | (?P<punct>[\[\](),;])
      | (?P<other>.)
        """,
        re.VERBOSE | re.DOTALL,
    )

    def __init__(self, source: str) -> None:
        self.tokens: list[tuple[str, str]] = []
        for match in self.TOKEN_RE.finditer(source):
            kind = match.lastgroup or "other"
            if kind not in {"space", "comment"}:
                self.tokens.append((kind, match.group(0)))
        self.index = 0

    def parse_return_array(self) -> dict[Any, Any]:
        while self.index < len(self.tokens):
            if self.tokens[self.index] == ("identifier", "return"):
                self.index += 1
                value = self.parse_value()
                if not isinstance(value, dict):
                    raise ConfigParseError("the returned value is not an array")
                return value
            self.index += 1
        raise ConfigParseError("no return array was found")

    def parse_value(self) -> Any:
        if self.index >= len(self.tokens):
            raise ConfigParseError("unexpected end of config")

        kind, value = self.tokens[self.index]
        if (kind, value) == ("punct", "["):
            return self.parse_array()
        self.index += 1

        if kind == "string":
            return self.decode_string(value)
        if kind == "number":
            return float(value) if "." in value else int(value)
        if kind == "identifier" and value.lower() in {"true", "false", "null"}:
            return {"true": True, "false": False, "null": None}[value.lower()]

        raise ConfigParseError(
            f"unsupported executable or non-literal value {value!r} near token {self.index}"
        )

    def parse_array(self) -> dict[Any, Any]:
        self.expect("punct", "[")
        result: dict[Any, Any] = {}
        next_index = 0

        while not self.peek("punct", "]"):
            first = self.parse_value()
            if self.peek("arrow", "=>"):
                self.index += 1
                key = first
                value = self.parse_value()
            else:
                key = next_index
                value = first
                next_index += 1
            result[key] = value

            if self.peek("punct", ","):
                self.index += 1
                continue
            if not self.peek("punct", "]"):
                found = self.tokens[self.index][1] if self.index < len(self.tokens) else "EOF"
                raise ConfigParseError(f"expected ',' or ']', found {found!r}")

        self.expect("punct", "]")
        return result

    def peek(self, kind: str, value: str) -> bool:
        return self.index < len(self.tokens) and self.tokens[self.index] == (kind, value)

    def expect(self, kind: str, value: str) -> None:
        if not self.peek(kind, value):
            found = self.tokens[self.index] if self.index < len(self.tokens) else ("EOF", "EOF")
            raise ConfigParseError(f"expected {value!r}, found {found[1]!r}")
        self.index += 1

    @staticmethod
    def decode_string(token: str) -> str:
        quote = token[0]
        body = token[1:-1]
        if quote == "'":
            return body.replace("\\'", "'").replace("\\\\", "\\")

        replacements = {
            r"\n": "\n",
            r"\r": "\r",
            r"\t": "\t",
            r'\"': '"',
            r"\\": "\\",
        }
        for escaped, decoded in replacements.items():
            body = body.replace(escaped, decoded)
        return body


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, (dict, list)) else None


def parse_php_config(path: Path) -> dict[Any, Any]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigParseError(str(error)) from error
    return PhpArrayParser(source).parse_return_array()


def is_bagisto_root(path: Path) -> bool:
    return (
        (path / "composer.json").is_file()
        and (path / "artisan").is_file()
        and (path / "config/themes.php").is_file()
    )


def discover_root(start: Path, search_parents: bool = True) -> Path | None:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    candidates = [current, *current.parents] if search_parents else [current]
    return next((candidate for candidate in candidates if is_bagisto_root(candidate)), None)


def composer_package_name(path: Path) -> str | None:
    data = read_json(path / "composer.json")
    return str(data.get("name")) if isinstance(data, dict) and data.get("name") else None


def provider_classes(package_root: Path) -> set[str]:
    classes: set[str] = set()
    providers = package_root / "src/Providers"
    for path in sorted(providers.glob("*ServiceProvider.php")) if providers.is_dir() else []:
        source = strip_php_comments(path.read_text(encoding="utf-8", errors="ignore"))
        namespace = re.search(r"\bnamespace\s+([^;]+);", source)
        class_name = re.search(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\b", source)
        if namespace and class_name:
            classes.add(namespace.group(1).strip() + "\\" + class_name.group(1))
    return classes


def strip_php_comments(source: str) -> str:
    """Remove PHP comments without treating comment markers inside strings as code."""
    output: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if quote is not None:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            index += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
            output.append(character)
            index += 1
            continue
        if character == "/" and following == "*":
            index += 2
            while index < len(source):
                if source[index] == "\n":
                    output.append("\n")
                if source[index : index + 2] == "*/":
                    index += 2
                    break
                index += 1
            continue
        if character == "/" and following == "/":
            index += 2
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        if character == "#" and following != "[":
            index += 1
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        output.append(character)
        index += 1
    return "".join(output)


class JavaScriptToken(NamedTuple):
    """One significant JavaScript token with its source span."""

    kind: str
    value: str
    start: int
    end: int


def _javascript_quoted_string(source: str, start: int) -> tuple[str, int, bool]:
    """Read one single- or double-quoted JavaScript string without evaluating it."""
    quote = source[start]
    value: list[str] = []
    index = start + 1
    escapes = {
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "0": "\0",
    }
    while index < len(source):
        character = source[index]
        if character == quote:
            return "".join(value), index + 1, True
        if character in "\r\n":
            return "".join(value), index, False
        if character != "\\":
            value.append(character)
            index += 1
            continue

        index += 1
        if index >= len(source):
            break
        escaped = source[index]
        if escaped == "\r" and index + 1 < len(source) and source[index + 1] == "\n":
            index += 2
            continue
        if escaped in "\r\n":
            index += 1
            continue
        if escaped == "x" and re.fullmatch(r"[0-9A-Fa-f]{2}", source[index + 1 : index + 3]):
            value.append(chr(int(source[index + 1 : index + 3], 16)))
            index += 3
            continue
        if escaped == "u" and re.fullmatch(r"[0-9A-Fa-f]{4}", source[index + 1 : index + 5]):
            value.append(chr(int(source[index + 1 : index + 5], 16)))
            index += 5
            continue
        value.append(escapes.get(escaped, escaped))
        index += 1
    return "".join(value), index, False


def _javascript_regex_end(source: str, start: int) -> int | None:
    """Return the end of a regex literal, or None when '/' is an operator."""
    index = start + 1
    escaped = False
    character_class = False
    while index < len(source):
        character = source[index]
        if character in "\r\n":
            return None
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == "[":
            character_class = True
        elif character == "]" and character_class:
            character_class = False
        elif character == "/" and not character_class:
            index += 1
            while index < len(source) and (
                source[index].isalpha() or source[index].isdigit() or source[index] in "_$"
            ):
                index += 1
            return index
        index += 1
    return None


def _javascript_template_end(
    source: str,
    start: int,
    expression_ranges: list[tuple[int, int]] | None = None,
) -> tuple[int, bool]:
    """Skip a complete template literal, including balanced interpolation blocks."""

    def expression_end(index: int) -> int:
        depth = 1
        while index < len(source) and depth:
            character = source[index]
            following = source[index + 1] if index + 1 < len(source) else ""
            if character in {"'", '"'}:
                _, index, _ = _javascript_quoted_string(source, index)
                continue
            if character == "`":
                index, _ = _javascript_template_end(source, index)
                continue
            if character == "/" and following == "/":
                index += 2
                while index < len(source) and source[index] not in "\r\n":
                    index += 1
                continue
            if character == "/" and following == "*":
                closing = source.find("*/", index + 2)
                index = len(source) if closing < 0 else closing + 2
                continue
            if character == "/":
                regex_end = _javascript_regex_end(source, index)
                if regex_end is not None:
                    index = regex_end
                    continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
            index += 1
        return index

    index = start + 1
    while index < len(source):
        character = source[index]
        if character == "\\":
            index += 2
            continue
        if character == "`":
            return index + 1, True
        if character == "$" and index + 1 < len(source) and source[index + 1] == "{":
            expression_start = index + 2
            index = expression_end(expression_start)
            if expression_ranges is not None and index > expression_start:
                expression_ranges.append((expression_start, index - 1))
            continue
        index += 1
    return index, False


def _javascript_jsx_allowed(tokens: list[JavaScriptToken]) -> bool:
    if not tokens:
        return True
    previous = tokens[-1]
    if previous.kind == "identifier":
        return previous.value in {"case", "return", "throw", "yield"}
    return previous.value in {
        "(",
        "[",
        "{",
        ",",
        ":",
        "=",
        "?",
        "=>",
        "&",
        "&&",
        "|",
        "||",
        "??",
    }


def _javascript_jsx_end(
    source: str,
    start: int,
    expression_ranges: list[tuple[int, int]],
) -> int | None:
    """Skip a balanced JSX element while exposing only its `{...}` expressions."""

    def regex_allowed_at(index: int, floor: int) -> bool:
        previous = index - 1
        while previous >= floor and source[previous].isspace():
            previous -= 1
        if previous < floor:
            return True
        if source[previous] in ")]}" or source[previous].isalnum() or source[previous] in "_$":
            return False
        if source[previous] in "+-":
            before = previous - 1
            while before >= floor and source[before].isspace():
                before -= 1
            if before >= floor and source[before] == source[previous]:
                return False
        return True

    def braced_end(opening: int) -> int | None:
        depth = 1
        index = opening + 1
        while index < len(source):
            character = source[index]
            following = source[index + 1] if index + 1 < len(source) else ""
            if character in {"'", '"'}:
                _, index, complete = _javascript_quoted_string(source, index)
                if not complete:
                    return None
                continue
            if character == "`":
                index, complete = _javascript_template_end(source, index)
                if not complete:
                    return None
                continue
            if character == "/" and following == "/":
                index += 2
                while index < len(source) and source[index] not in "\r\n":
                    index += 1
                continue
            if character == "/" and following == "*":
                closing = source.find("*/", index + 2)
                if closing < 0:
                    return None
                index = closing + 2
                continue
            if character == "/" and regex_allowed_at(index, opening + 1):
                regex_end = _javascript_regex_end(source, index)
                if regex_end is not None:
                    index = regex_end
                    continue
            if character == "<" and (
                following in {">", "/"} or following.isalpha() or following in "_$"
            ):
                nested_ranges: list[tuple[int, int]] = []
                nested_end = _javascript_jsx_end(source, index, nested_ranges)
                if nested_end is not None:
                    expression_ranges.extend(nested_ranges)
                    index = nested_end
                    continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return index + 1
            index += 1
        return None

    def tag_end(opening: int) -> tuple[int, bool] | None:
        index = opening + 1
        while index < len(source):
            character = source[index]
            if character in {"'", '"'}:
                _, index, complete = _javascript_quoted_string(source, index)
                if not complete:
                    return None
                continue
            if character == "{":
                closing = braced_end(index)
                if closing is None:
                    return None
                expression_ranges.append((index + 1, closing - 1))
                index = closing
                continue
            if character == ">":
                previous = index - 1
                while previous > opening and source[previous].isspace():
                    previous -= 1
                return index + 1, source[previous] == "/"
            if character in "\r\n" and opening + 1 < len(source) and source[opening + 1] == "/":
                return None
            index += 1
        return None

    index = start
    depth = 0
    saw_tag = False
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if character == "<" and (
            following in {">", "/"} or following.isalpha() or following in "_$"
        ):
            closing_tag = following == "/"
            result = tag_end(index)
            if result is None:
                return None
            index, self_closing = result
            saw_tag = True
            if closing_tag:
                depth -= 1
                if depth == 0:
                    return index
                if depth < 0:
                    return None
            elif not self_closing:
                depth += 1
            elif depth == 0:
                return index
            continue
        if character == "{":
            closing = braced_end(index)
            if closing is None:
                return None
            expression_ranges.append((index + 1, closing - 1))
            index = closing
            continue
        index += 1
    return index if saw_tag and depth == 0 else None


def _javascript_regex_allowed(
    tokens: list[JavaScriptToken],
    after_control_parenthesis: bool,
) -> bool:
    if after_control_parenthesis or not tokens:
        return True
    previous = tokens[-1]
    if previous.kind == "block_close":
        return True
    if previous.kind == "postfix":
        return False
    if previous.kind == "identifier":
        return previous.value in {
            "await",
            "break",
            "case",
            "continue",
            "debugger",
            "delete",
            "do",
            "else",
            "in",
            "instanceof",
            "new",
            "of",
            "return",
            "throw",
            "typeof",
            "void",
            "yield",
        }
    return previous.value in {
        "(",
        "[",
        "{",
        ",",
        ";",
        ":",
        "=",
        "!",
        "?",
        "&",
        "|",
        "+",
        "-",
        "/",
        "*",
        "%",
        "^",
        "~",
        "<",
        ">",
    }


def javascript_tokens(source: str) -> list[JavaScriptToken]:
    """Tokenize the JavaScript subset needed for static build-contract discovery.

    Strings, templates, comments, and regex literals are consumed atomically so
    text inside them can never become a synthetic property or module import.
    The function performs no code execution and intentionally omits expression
    evaluation.
    """
    tokens: list[JavaScriptToken] = []
    parenthesis_context: list[bool] = []
    brace_context: list[bool] = []
    after_control_parenthesis = False
    control_keywords = {"catch", "for", "if", "switch", "while", "with"}
    index = 0
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if character.isspace():
            index += 1
            continue
        if character == "/" and following == "/":
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue
        if character == "/" and following == "*":
            closing = source.find("*/", index + 2)
            if closing < 0:
                tokens.append(JavaScriptToken("invalid", "unclosed-comment", index, len(source)))
                break
            index = closing + 2
            continue
        if character in {"'", '"'}:
            value, end, complete = _javascript_quoted_string(source, index)
            tokens.append(JavaScriptToken("string" if complete else "invalid", value, index, end))
            index = max(end, index + 1)
            after_control_parenthesis = False
            continue
        if character == "`":
            interpolation_ranges: list[tuple[int, int]] = []
            end, complete = _javascript_template_end(source, index, interpolation_ranges)
            tokens.append(JavaScriptToken("template" if complete else "invalid", "", index, end))
            if complete:
                for expression_start, expression_end in interpolation_ranges:
                    for token in javascript_tokens(source[expression_start:expression_end]):
                        tokens.append(
                            JavaScriptToken(
                                token.kind,
                                token.value,
                                token.start + expression_start,
                                token.end + expression_start,
                            )
                        )
            index = max(end, index + 1)
            after_control_parenthesis = False
            continue
        if character == "<" and (
            following in {">", "/"} or following.isalpha() or following in "_$"
        ) and _javascript_jsx_allowed(tokens):
            expression_ranges: list[tuple[int, int]] = []
            end = _javascript_jsx_end(source, index, expression_ranges)
            if end is not None:
                tokens.append(JavaScriptToken("jsx", "", index, end))
                for expression_start, expression_end in expression_ranges:
                    for token in javascript_tokens(source[expression_start:expression_end]):
                        tokens.append(
                            JavaScriptToken(
                                token.kind,
                                token.value,
                                token.start + expression_start,
                                token.end + expression_start,
                            )
                        )
                index = end
                after_control_parenthesis = False
                continue
        if character == "/" and _javascript_regex_allowed(tokens, after_control_parenthesis):
            end = _javascript_regex_end(source, index)
            if end is not None:
                tokens.append(JavaScriptToken("regex", "", index, end))
                index = end
                after_control_parenthesis = False
                continue
            line_end = index
            while line_end < len(source) and source[line_end] not in "\r\n":
                line_end += 1
            tokens.append(JavaScriptToken("invalid", "unclosed-regex", index, line_end))
            index = max(line_end, index + 1)
            after_control_parenthesis = False
            continue
        if character.isalpha() or character in "_$":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] in "_$"):
                end += 1
            tokens.append(JavaScriptToken("identifier", source[index:end], index, end))
            index = end
            after_control_parenthesis = False
            continue
        if character.isdigit():
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] in "._"):
                end += 1
            tokens.append(JavaScriptToken("number", source[index:end], index, end))
            index = end
            after_control_parenthesis = False
            continue

        operator = source[index : index + 2]
        if operator in {"++", "--", "=>", "&&", "||", "??", "?."}:
            tokens.append(JavaScriptToken("operator", operator, index, index + 2))
            index += 2
            after_control_parenthesis = False
            continue
        if character == "!" and following != "=" and tokens and (
            tokens[-1].kind in {"identifier", "number", "string", "template", "regex", "jsx", "object_close"}
            or tokens[-1].value in {")", "]", "++", "--"}
        ):
            tokens.append(JavaScriptToken("postfix", "!", index, index + 1))
            index += 1
            after_control_parenthesis = False
            continue

        if character == "(":
            parenthesis_context.append(
                bool(
                    tokens
                    and (
                        (tokens[-1].kind == "identifier" and tokens[-1].value in control_keywords)
                        or (
                            tokens[-1].kind == "identifier"
                            and tokens[-1].value == "await"
                            and len(tokens) > 1
                            and tokens[-2].kind == "identifier"
                            and tokens[-2].value == "for"
                        )
                    )
                )
            )
        closing_control = False
        if character == ")" and parenthesis_context:
            closing_control = parenthesis_context.pop()
        token_kind = "punctuation"
        if character == "{":
            previous = tokens[-1] if tokens else None
            is_block = bool(
                after_control_parenthesis
                or previous is None
                or previous.value in {")", "=>"}
                or (
                    previous.kind == "identifier"
                    and previous.value
                    in {"catch", "class", "do", "else", "finally", "function", "switch", "try"}
                )
                or (
                    previous.kind == "identifier"
                    and len(tokens) > 1
                    and tokens[-2].kind == "identifier"
                    and tokens[-2].value in {"class", "enum", "interface", "namespace"}
                )
            )
            brace_context.append(is_block)
            token_kind = "block_open" if is_block else "object_open"
        elif character == "}" and brace_context:
            token_kind = "block_close" if brace_context.pop() else "object_close"
        tokens.append(JavaScriptToken(token_kind, character, index, index + 1))
        index += 1
        after_control_parenthesis = closing_control
    return tokens


def javascript_module_specifiers(source: str) -> list[str]:
    """Return literal static/dynamic import and CommonJS module specifiers."""
    tokens = javascript_tokens(source)
    invalid = next((token for token in tokens if token.kind == "invalid"), None)
    if invalid is not None:
        raise JavaScriptScanError(
            f"incomplete JavaScript lexical state ({invalid.value}) at byte {invalid.start}"
        )
    specifiers: set[str] = set()
    for index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        if token.value in {"import", "export"}:
            previous = tokens[index - 1] if index else None
            line_start = max(source.rfind("\n", 0, token.start), source.rfind("\r", 0, token.start)) + 1
            line_prefix = source[line_start : token.start].strip()
            static_statement = (
                not line_prefix
                or previous is None
                or previous.value in {";", "{", "}"}
            )
            if index + 1 < len(tokens) and tokens[index + 1].value == ":":
                continue
            if (
                static_statement
                and index + 1 < len(tokens)
                and tokens[index + 1].kind == "string"
            ):
                specifiers.add(tokens[index + 1].value)
                continue
            if (
                token.value == "import"
                and index + 3 < len(tokens)
                and (previous is None or previous.value not in {".", "#"})
                and tokens[index + 1].value == "("
                and tokens[index + 2].kind == "string"
                and tokens[index + 3].value in {")", ","}
            ):
                specifiers.add(tokens[index + 2].value)
                continue
            if not static_statement:
                continue
            for candidate_index in range(index + 1, min(index + 96, len(tokens))):
                candidate = tokens[candidate_index]
                if candidate.value == ";" or (
                    candidate_index > index + 1
                    and candidate.kind == "identifier"
                    and candidate.value in {"import", "export"}
                ):
                    break
                if (
                    candidate.kind == "identifier"
                    and candidate.value == "from"
                    and candidate_index + 1 < len(tokens)
                    and tokens[candidate_index + 1].kind == "string"
                ):
                    specifiers.add(tokens[candidate_index + 1].value)
                    break
        elif token.value == "require":
            if index and tokens[index - 1].value in {".", "#"}:
                continue
            cursor = index + 1
            resolving = False
            if (
                cursor + 1 < len(tokens)
                and tokens[cursor].value == "."
                and tokens[cursor + 1].kind == "identifier"
                and tokens[cursor + 1].value == "resolve"
            ):
                cursor += 2
                resolving = True
            if (
                cursor + 2 < len(tokens)
                and tokens[cursor].value == "("
                and tokens[cursor + 1].kind == "string"
                and (
                    tokens[cursor + 2].value == ")"
                    or (resolving and tokens[cursor + 2].value == ",")
                )
            ):
                specifiers.add(tokens[cursor + 1].value)
    return sorted(specifiers)


def _javascript_matching_token(tokens: list[JavaScriptToken], opening: int) -> int | None:
    pairs = {"(": ")", "[": "]", "{": "}"}
    if opening >= len(tokens) or tokens[opening].value not in pairs:
        return None
    stack = [pairs[tokens[opening].value]]
    for index in range(opening + 1, len(tokens)):
        value = tokens[index].value
        if value in pairs:
            stack.append(pairs[value])
        elif value in pairs.values():
            if not stack or value != stack.pop():
                return None
            if not stack:
                return index
    return None


def _javascript_default_import_bindings(
    tokens: list[JavaScriptToken],
    module_name: str,
) -> set[str]:
    bindings: set[str] = set()
    for index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        if token.value == "import":
            statement_end = index + 1
            while statement_end < len(tokens) and tokens[statement_end].value != ";":
                statement_end += 1
            statement = tokens[index + 1 : statement_end]
            if not any(item.kind == "string" and item.value == module_name for item in statement):
                continue
            if statement and statement[0].kind == "identifier" and statement[0].value != "type":
                bindings.add(statement[0].value)
            for offset, item in enumerate(statement[:-2]):
                if (
                    item.kind == "identifier"
                    and item.value == "default"
                    and statement[offset + 1].kind == "identifier"
                    and statement[offset + 1].value == "as"
                    and statement[offset + 2].kind == "identifier"
                ):
                    bindings.add(statement[offset + 2].value)
        elif token.value == "require" and index >= 2:
            if tokens[index - 1].value != "=" or tokens[index - 2].kind != "identifier":
                continue
            if (
                index + 3 < len(tokens)
                and tokens[index + 1].value == "("
                and tokens[index + 2].kind == "string"
                and tokens[index + 2].value == module_name
                and tokens[index + 3].value == ")"
            ):
                bindings.add(tokens[index - 2].value)
    return bindings


def _javascript_object_property_values(
    tokens: list[JavaScriptToken],
    opening: int,
) -> dict[str, list[int]] | None:
    closing = _javascript_matching_token(tokens, opening)
    if closing is None:
        return None
    properties: dict[str, list[int]] = {}
    cursor = opening + 1
    while cursor < closing:
        if tokens[cursor].value == ",":
            cursor += 1
            continue
        key: str | None = None
        after_key = cursor + 1
        if tokens[cursor].kind in {"identifier", "number", "string"}:
            key = tokens[cursor].value
        elif (
            tokens[cursor].value == "["
            and cursor + 2 < closing
            and tokens[cursor + 1].kind == "string"
            and tokens[cursor + 2].value == "]"
        ):
            key = tokens[cursor + 1].value
            after_key = cursor + 3

        if key is not None and after_key < closing and tokens[after_key].value == ":":
            value_index = after_key + 1
            if value_index >= closing:
                return None
            properties.setdefault(key, []).append(value_index)
            cursor = value_index
        else:
            cursor += 1

        depth: list[str] = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        while cursor < closing:
            value = tokens[cursor].value
            if value in pairs:
                depth.append(pairs[value])
            elif value in pairs.values():
                if depth and value == depth[-1]:
                    depth.pop()
                elif not depth:
                    break
            elif value == "," and not depth:
                break
            cursor += 1
        if cursor < closing and tokens[cursor].value == ",":
            cursor += 1
    return properties


def _javascript_literal_input_values(
    tokens: list[JavaScriptToken],
    value_index: int,
) -> list[str] | None:
    if value_index >= len(tokens):
        return None
    value_token = tokens[value_index]
    if value_token.kind == "string":
        return [value_token.value]
    values: list[str] = []
    cursor = value_index + 1
    if value_token.value == "[":
        closing = _javascript_matching_token(tokens, value_index)
        if closing is None:
            return None
        while cursor < closing:
            if tokens[cursor].value == ",":
                cursor += 1
                continue
            if tokens[cursor].kind != "string":
                return None
            values.append(tokens[cursor].value)
            cursor += 1
        return values
    if value_token.value == "{":
        closing = _javascript_matching_token(tokens, value_index)
        if closing is None:
            return None
        while cursor < closing:
            if tokens[cursor].value == ",":
                cursor += 1
                continue
            if tokens[cursor].kind not in {"identifier", "number", "string"}:
                return None
            cursor += 1
            if cursor >= closing or tokens[cursor].value != ":":
                return None
            cursor += 1
            if cursor >= closing or tokens[cursor].kind != "string":
                return None
            values.append(tokens[cursor].value)
            cursor += 1
        return values
    return None


def literal_vite_input_files(package_root: Path) -> list[Path]:
    """Return package-local inputs owned by a literal Laravel Vite plugin call."""
    package = package_root.resolve()
    suffixes = {".css", ".less", ".sass", ".scss", ".js", ".jsx", ".ts", ".tsx", ".vue"}
    config_suffixes = {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts"}
    entries: set[Path] = set()
    for config in sorted(package.glob("vite.config.*")):
        if (
            not config.is_file()
            or config.is_symlink()
            or config.suffix.lower() not in config_suffixes
        ):
            continue
        tokens = javascript_tokens(config.read_text(encoding="utf-8", errors="ignore"))
        if any(token.kind == "invalid" for token in tokens):
            return []
        bindings = _javascript_default_import_bindings(tokens, "laravel-vite-plugin")
        if not bindings:
            return []
        input_values: list[str] = []
        for index, token in enumerate(tokens):
            if token.kind != "identifier" or token.value not in bindings:
                continue
            if index and tokens[index - 1].value in {".", "#"}:
                continue
            if (
                index + 2 >= len(tokens)
                or tokens[index + 1].value != "("
                or tokens[index + 2].value != "{"
            ):
                continue
            properties = _javascript_object_property_values(tokens, index + 2)
            if properties is None:
                return []
            inputs = properties.get("input", [])
            if len(inputs) > 1:
                return []
            if not inputs:
                continue
            values = _javascript_literal_input_values(tokens, inputs[0])
            if values is None:
                return []
            input_values.extend(values)

        for input_value in input_values:
            value = input_value.split("?", 1)[0].split("#", 1)[0]
            if not value or any(
                ord(character) < 32
                or ord(character) == 127
                or 0xD800 <= ord(character) <= 0xDFFF
                for character in value
            ):
                return []
            relative = Path(value)
            if (
                relative.is_absolute()
                or not relative.parts
                or ".." in relative.parts
                or relative.parts[0] == "node_modules"
                or relative.suffix.lower() not in suffixes
            ):
                return []
            try:
                unresolved = package
                for part in relative.parts:
                    unresolved /= part
                    if unresolved.is_symlink():
                        return []
                candidate = unresolved.resolve(strict=False)
                candidate.relative_to(package)
                if not candidate.is_file() or candidate.is_symlink():
                    return []
                entries.add(candidate)
            except (OSError, UnicodeError, ValueError):
                return []
    return sorted(entries)


def literal_vite_assets_root(package_root: Path) -> Path | None:
    entries = literal_vite_input_files(package_root)
    if not entries:
        return None
    package = package_root.resolve()
    common = Path(os.path.commonpath([str(path.parent) for path in entries])).resolve()
    return common if common != package and common.is_dir() else None


def discovered_view_root(package_root: Path) -> Path | None:
    candidates: set[Path] = set()
    for blade in package_root.rglob("*.blade.php"):
        if blade.is_symlink() or not blade.is_file():
            continue
        for parent in blade.parents:
            if parent == package_root:
                break
            if parent.name.casefold() == "views":
                candidates.add(parent.resolve())
                break
    return next(iter(candidates)) if len(candidates) == 1 else None


def discovered_language_root(package_root: Path) -> Path | None:
    candidates: list[Path] = []
    for directory in package_root.rglob("*"):
        if (
            directory.is_dir()
            and not directory.is_symlink()
            and directory.name.casefold() in {"lang", "langs", "locales"}
            and any(path.is_file() for path in directory.glob("*/*.php"))
        ):
            candidates.append(directory.resolve())
    unique = sorted(set(candidates))
    return unique[0] if len(unique) == 1 else None


def discovered_routes_root(package_root: Path) -> Path | None:
    candidates = sorted(
        {
            directory.resolve()
            for directory in package_root.rglob("*")
            if directory.is_dir()
            and not directory.is_symlink()
            and directory.name.casefold() == "routes"
            and any(path.is_file() for path in directory.glob("*.php"))
        }
    )
    return candidates[0] if len(candidates) == 1 else None


def package_is_registered(root: Path, package_root: Path) -> bool:
    """Accept only host-local wiring or an exact Composer-installed package root."""
    package_root = package_root.resolve()
    package_composer = read_json(package_root / "composer.json")
    package_composer = package_composer if isinstance(package_composer, dict) else {}
    root_composer = read_json(root / "composer.json")
    root_composer = root_composer if isinstance(root_composer, dict) else {}
    providers = provider_classes(package_root)
    bootstrap_path = root / "bootstrap/providers.php"
    bootstrap = (
        strip_php_comments(bootstrap_path.read_text(encoding="utf-8", errors="ignore"))
        if bootstrap_path.is_file()
        else ""
    )

    def provider_in_bootstrap(provider: str) -> bool:
        short_name = provider.rsplit("\\", 1)[-1]
        return bool(
            re.search(rf"\b{re.escape(provider)}\s*::\s*class\b", bootstrap)
            or (
                re.search(rf"\buse\s+{re.escape(provider)}\s*;", bootstrap)
                and re.search(rf"\b{re.escape(short_name)}\s*::\s*class\b", bootstrap)
            )
        )

    try:
        expected_source = (package_root / "src").relative_to(root.resolve()).as_posix().rstrip("/")
    except ValueError:
        expected_source = ""
    autoload_values = {
        str(value).replace("\\", "/").rstrip("/")
        for value in root_composer.get("autoload", {}).get("psr-4", {}).values()
        if isinstance(value, str)
    }
    locally_wired = bool(
        expected_source
        and expected_source in autoload_values
        and any(provider_in_bootstrap(provider) for provider in providers)
    )
    if locally_wired:
        return True

    package_name = package_composer.get("name")
    if not isinstance(package_name, str):
        return False
    installed_here = False
    for record in installed_package_records(root):
        if record.get("name") != package_name or not isinstance(record.get("install_path"), str):
            continue
        installed_root = (root / "vendor/composer" / record["install_path"]).resolve()
        if installed_root == package_root:
            installed_here = True
            break
    if not installed_here:
        return False
    discovered = package_composer.get("extra", {}).get("laravel", {}).get("providers", [])
    return bool(
        providers
        and (
            any(provider in discovered for provider in providers)
            or any(provider_in_bootstrap(provider) for provider in providers)
        )
    )


def installed_package_records(root: Path) -> list[dict[str, Any]]:
    installed_path = root / "vendor" / "composer" / "installed.json"
    data = read_json(installed_path)
    if isinstance(data, dict):
        packages = data.get("packages", [])
    elif isinstance(data, list):
        packages = data
    else:
        packages = []
    return [item for item in packages if isinstance(item, dict)]


def package_candidates(root: Path) -> Iterable[tuple[Path, str]]:
    packages_root = root / "packages"
    if packages_root.is_dir():
        for composer_file in sorted(packages_root.glob("*/*/composer.json")):
            yield composer_file.parent, "packages"

    seen: set[Path] = set()
    for record in installed_package_records(root):
        if not str(record.get("name", "")).startswith("bagisto/"):
            continue
        install_path = record.get("install_path")
        if isinstance(install_path, str):
            candidate = (root / "vendor" / "composer" / install_path).resolve()
            if candidate not in seen:
                seen.add(candidate)
                yield candidate, "vendor"

    vendor = root / "vendor"
    if vendor.is_dir():
        for pattern in ("bagisto/*/composer.json", "webkul/*/composer.json"):
            for composer_file in sorted(vendor.glob(pattern)):
                candidate = composer_file.parent
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield candidate, "vendor"


def find_package(root: Path, composer_name: str) -> tuple[Path, str] | None:
    conventional = {
        "bagisto/laravel-shop": root / "packages" / "Webkul" / "Shop",
        "bagisto/laravel-core": root / "packages" / "Webkul" / "Core",
        "bagisto/laravel-theme": root / "packages" / "Webkul" / "Theme",
    }.get(composer_name)
    matches: dict[Path, str] = {}
    for candidate, source in package_candidates(root):
        if composer_package_name(candidate) == composer_name:
            matches[candidate.resolve()] = source
    if conventional and composer_package_name(conventional) == composer_name:
        matches[conventional.resolve()] = "packages"
    if len(matches) > 1:
        rendered = ", ".join(str(path) for path in sorted(matches))
        raise PackageDiscoveryError(
            f"duplicate Composer identity {composer_name!r} resolves to: {rendered}"
        )
    return next(iter(matches.items())) if matches else None


def installed_version(root: Path, package_name: str) -> str | None:
    for record in installed_package_records(root):
        if record.get("name") == package_name:
            version = record.get("pretty_version") or record.get("version")
            return str(version) if version else None

    lock = read_json(root / "composer.lock")
    if isinstance(lock, dict):
        for section in ("packages", "packages-dev"):
            records = lock.get(section, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if isinstance(record, dict) and record.get("name") == package_name:
                    version = record.get("pretty_version") or record.get("version")
                    return str(version) if version else None
    return None


def declared_package_version(package_path: Path | None) -> str | None:
    if package_path is None:
        return None
    composer = read_json(package_path / "composer.json")
    if isinstance(composer, dict) and composer.get("version"):
        return str(composer["version"])
    return None


def bagisto_version(core_path: Path | None) -> str | None:
    if core_path is None:
        return None
    core_file = core_path / "src" / "Core.php"
    try:
        source = core_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = re.search(r"\bBAGISTO_VERSION\s*=\s*['\"]([^'\"]+)['\"]", source)
    return match.group(1) if match else None


def path_info(root: Path, configured: Any) -> dict[str, Any] | None:
    if not isinstance(configured, str) or not configured:
        return None
    path = Path(configured).expanduser()
    absolute = path if path.is_absolute() else root / path
    info: dict[str, Any] = {
        "configured": configured,
        "absolute": str(absolute),
        "exists": absolute.exists(),
        "is_symlink": absolute.is_symlink(),
    }
    if absolute.exists() or absolute.is_symlink():
        info["resolved"] = str(absolute.resolve(strict=False))
    return info


def discover_themes(root: Path, selected: str | None, warnings: list[str]) -> tuple[list[dict[str, Any]], str | None]:
    config_path = root / "config" / "themes.php"
    if not config_path.is_file():
        warnings.append("config/themes.php was not found")
        return [], None
    try:
        config = parse_php_config(config_path)
    except ConfigParseError as error:
        warnings.append(f"could not parse config/themes.php safely: {error}")
        return [], None

    fallback = config.get("shop-default")
    fallback = str(fallback) if fallback is not None else None
    shop = config.get("shop", {})
    if not isinstance(shop, dict):
        warnings.append("config/themes.php does not contain a literal 'shop' theme map")
        return [], fallback

    themes: list[dict[str, Any]] = []
    for raw_code, raw_theme in sorted(shop.items(), key=lambda item: str(item[0])):
        code = str(raw_code)
        if selected is not None and code != selected:
            continue
        if not isinstance(raw_theme, dict):
            warnings.append(f"theme {code!r} is not a literal configuration array")
            continue
        views = path_info(root, raw_theme.get("views_path"))
        assets = path_info(root, raw_theme.get("assets_path"))
        vite = raw_theme.get("vite") if isinstance(raw_theme.get("vite"), dict) else {}
        theme = {
            "code": code,
            "name": str(raw_theme.get("name", code)),
            "is_fallback": code == fallback,
            "parent": raw_theme.get("parent"),
            "views_namespace": raw_theme.get("views_namespace"),
            "views_path": views,
            "assets_path": assets,
            "vite": {
                "hot_file": vite.get("hot_file"),
                "build_directory": vite.get("build_directory"),
                "package_assets_directory": vite.get("package_assets_directory"),
            },
        }
        themes.append(theme)
        if views and not views["exists"]:
            warnings.append(f"theme {code!r} views path does not exist: {views['configured']}")

    return themes, fallback


def discover_vite_registry(root: Path, warnings: list[str]) -> dict[str, Any]:
    path = root / "config" / "bagisto-vite.php"
    if not path.is_file():
        warnings.append("config/bagisto-vite.php was not found")
        return {"path": None, "keys": []}
    try:
        config = parse_php_config(path)
    except ConfigParseError as error:
        warnings.append(f"could not parse config/bagisto-vite.php safely: {error}")
        return {"path": str(path), "keys": []}
    viters = config.get("viters", {})
    keys = sorted(str(key) for key in viters) if isinstance(viters, dict) else []
    return {"path": str(path), "keys": keys}


def discover_instructions(root: Path) -> list[str]:
    found: set[str] = set()
    for directory, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(item for item in directories if item not in SKIP_INSTRUCTION_DIRS)
        base = Path(directory)
        for filename in files:
            path = base / filename
            relative = path.relative_to(root).as_posix()
            if filename in INSTRUCTION_NAMES or relative == ".github/copilot-instructions.md":
                found.add(relative)
    return sorted(found)


def frontend_info(shop_path: Path | None) -> dict[str, Any]:
    if shop_path is None:
        return {
            "package_json": None,
            "vite_config": None,
            "tailwind_config": None,
            "postcss_config": None,
            "entry_file": None,
            "entry_files": [],
            "lockfiles": [],
            "versions": {},
            "scripts": {},
        }
    package_json = shop_path / "package.json"
    data = read_json(package_json)
    if not isinstance(data, dict):
        return {
            "package_json": str(package_json),
            "vite_config": None,
            "tailwind_config": None,
            "postcss_config": None,
            "entry_file": None,
            "entry_files": [],
            "lockfiles": [],
            "versions": {},
            "scripts": {},
        }

    dependencies: dict[str, Any] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = data.get(section, {})
        if isinstance(values, dict):
            dependencies.update(values)
    versions = {name: str(dependencies[name]) for name in FRONTEND_PACKAGES if name in dependencies}
    lockfiles = [
        candidate.name
        for candidate in (shop_path / "package-lock.json", shop_path / "pnpm-lock.yaml", shop_path / "yarn.lock")
        if candidate.is_file()
    ]
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    vite_config = next(
        (
            path
            for path in (
                shop_path / "vite.config.js",
                shop_path / "vite.config.cjs",
                shop_path / "vite.config.mjs",
                shop_path / "vite.config.ts",
                shop_path / "vite.config.mts",
                shop_path / "vite.config.cts",
            )
            if path.is_file()
        ),
        None,
    )
    ordered_entries = literal_vite_input_files(shop_path)
    return {
        "package_json": str(package_json),
        "vite_config": str(vite_config) if vite_config else None,
        "tailwind_config": next(
            (
                str(path)
                for path in (
                    shop_path / "tailwind.config.js",
                    shop_path / "tailwind.config.cjs",
                    shop_path / "tailwind.config.mjs",
                    shop_path / "tailwind.config.ts",
                    shop_path / "tailwind.config.mts",
                    shop_path / "tailwind.config.cts",
                )
                if path.is_file()
            ),
            None,
        ),
        "postcss_config": next(
            (
                str(path)
                for path in (
                    shop_path / "postcss.config.cjs",
                    shop_path / "postcss.config.js",
                    shop_path / "postcss.config.mjs",
                    shop_path / "postcss.config.ts",
                    shop_path / "postcss.config.mts",
                    shop_path / "postcss.config.cts",
                )
                if path.is_file()
            ),
            None,
        ),
        "entry_file": str(ordered_entries[0]) if ordered_entries else None,
        "entry_files": [str(path) for path in ordered_entries],
        "lockfiles": lockfiles,
        "versions": versions,
        "scripts": {str(key): str(value) for key, value in scripts.items()},
    }


def inspect(root: Path, selected_theme: str | None) -> tuple[dict[str, Any], int]:
    warnings: list[str] = []
    discovery_ambiguous = False
    composer = read_json(root / "composer.json")
    composer = composer if isinstance(composer, dict) else {}

    def safely_find_package(name: str) -> tuple[Path, str] | None:
        nonlocal discovery_ambiguous
        try:
            return find_package(root, name)
        except PackageDiscoveryError as error:
            warnings.append(str(error))
            discovery_ambiguous = True
            return None

    shop = safely_find_package("bagisto/laravel-shop")
    core = safely_find_package("bagisto/laravel-core")
    theme = safely_find_package("bagisto/laravel-theme")
    shop_path, shop_source = shop if shop else (None, None)
    core_path, core_source = core if core else (None, None)
    theme_path, theme_source = theme if theme else (None, None)
    for identity, path in (
        ("bagisto/laravel-shop", shop_path),
        ("bagisto/laravel-core", core_path),
        ("bagisto/laravel-theme", theme_path),
    ):
        if path is None:
            warnings.append(f"the {identity} package could not be located unambiguously")

    shop_views = discovered_view_root(shop_path) if shop_path else None
    shop_assets = literal_vite_assets_root(shop_path) if shop_path else None
    shop_languages = discovered_language_root(shop_path) if shop_path else None
    shop_routes = discovered_routes_root(shop_path) if shop_path else None
    if shop_path and shop_views is None:
        warnings.append("the installed Shop package has no unique discovered Blade view root")
    if shop_path and shop_assets is None:
        warnings.append("the installed Shop package has no safe asset root derived from literal Vite inputs")
    if shop_path and shop_languages is None:
        warnings.append("the installed Shop package has no unique discovered language root")

    themes, fallback = discover_themes(root, selected_theme, warnings)
    status = EXIT_OK
    critical_theme_config = any(
        warning.startswith(
            (
                "config/themes.php was not found",
                "could not parse config/themes.php safely",
                "config/themes.php does not contain a literal 'shop' theme map",
            )
        )
        for warning in warnings
    )
    if (
        discovery_ambiguous
        or shop_path is None
        or core_path is None
        or theme_path is None
        or shop_views is None
        or shop_assets is None
        or shop_languages is None
        or not themes
        or fallback is None
        or critical_theme_config
    ):
        status = EXIT_INVALID
    if selected_theme is not None and not any(theme["code"] == selected_theme for theme in themes):
        warnings.append(f"shop theme {selected_theme!r} is not configured")
        status = EXIT_INVALID

    result = {
        "schema_version": 1,
        "root": str(root),
        "project": {
            "composer_name": composer.get("name"),
            "bagisto_version": bagisto_version(core_path),
            "laravel_constraint": (
                composer.get("require", {}).get("laravel/framework")
                if isinstance(composer.get("require"), dict)
                else None
            ),
        },
        "shop_package": {
            "composer_name": "bagisto/laravel-shop",
            "version": installed_version(root, "bagisto/laravel-shop")
            or declared_package_version(shop_path),
            "source": shop_source,
            "path": str(shop_path) if shop_path else None,
            "views_path": str(shop_views) if shop_views else None,
            "components_path": str(shop_views / "components") if shop_views and (shop_views / "components").is_dir() else None,
            "assets_path": str(shop_assets) if shop_assets else None,
            "routes_path": str(shop_routes) if shop_routes else None,
            "tests_path": str(shop_path / "tests") if shop_path and (shop_path / "tests").is_dir() else None,
            "locales": (
                sorted(path.name for path in shop_languages.iterdir() if path.is_dir())
                if shop_languages
                else []
            ),
        },
        "core_package": {
            "composer_name": "bagisto/laravel-core",
            "version": installed_version(root, "bagisto/laravel-core")
            or declared_package_version(core_path),
            "source": core_source,
            "path": str(core_path) if core_path else None,
        },
        "theme_package": {
            "composer_name": "bagisto/laravel-theme",
            "version": installed_version(root, "bagisto/laravel-theme")
            or declared_package_version(theme_path),
            "source": theme_source,
            "path": str(theme_path) if theme_path else None,
        },
        "frontend": frontend_info(shop_path),
        "theme_config": {
            "path": str(root / "config" / "themes.php"),
            "fallback": fallback,
            "selected": selected_theme,
            "themes": themes,
        },
        "vite_registry": discover_vite_registry(root, warnings),
        "instructions": discover_instructions(root),
        "warnings": warnings,
    }
    return result, status


def printable(value: Any) -> str:
    if value is None:
        return "not detected"
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return str(value)


def print_human(result: dict[str, Any]) -> None:
    print(f"Bagisto theme environment: {result['root']}")
    project = result["project"]
    print("\nProject")
    print(f"  Composer name:    {printable(project['composer_name'])}")
    print(f"  Bagisto version:  {printable(project['bagisto_version'])}")
    print(f"  Laravel:          {printable(project['laravel_constraint'])}")

    shop = result["shop_package"]
    print("\nStorefront package")
    print(f"  Source:           {printable(shop['source'])}")
    print(f"  Path:             {printable(shop['path'])}")
    print(f"  Installed version: {printable(shop['version'])}")
    print(f"  Upstream views:   {printable(shop['views_path'])}")
    print(f"  Components:       {printable(shop['components_path'])}")
    print(f"  Assets:           {printable(shop['assets_path'])}")
    print(f"  Routes:           {printable(shop['routes_path'])}")
    print(f"  Tests:            {printable(shop['tests_path'])}")
    print(f"  Locales:          {', '.join(shop['locales']) if shop['locales'] else 'none detected'}")
    theme = result["theme_package"]
    print(f"  Theme engine:     {printable(theme['path'])}")

    frontend = result["frontend"]
    print("\nFrontend toolchain")
    print(f"  package.json:     {printable(frontend['package_json'])}")
    print(f"  Vite config:      {printable(frontend['vite_config'])}")
    print(f"  Tailwind config:  {printable(frontend['tailwind_config'])}")
    print(f"  PostCSS config:   {printable(frontend['postcss_config'])}")
    print(f"  App entry:        {printable(frontend['entry_file'])}")
    if frontend["versions"]:
        for name, version in frontend["versions"].items():
            print(f"  {name:<19}{version}")
    else:
        print("  No known storefront frontend dependencies detected")
    if frontend["lockfiles"]:
        print(f"  Lockfiles:        {', '.join(frontend['lockfiles'])}")

    config = result["theme_config"]
    print(f"\nShop themes (fallback: {printable(config['fallback'])})")
    if not config["themes"]:
        print("  None detected")
    for theme in config["themes"]:
        marker = " [fallback]" if theme["is_fallback"] else ""
        print(f"  {theme['code']}: {theme['name']}{marker}")
        print(f"    parent: {printable(theme['parent'])}")
        print(f"    namespace: {printable(theme['views_namespace'])}")
        views = theme["views_path"]
        assets = theme["assets_path"]
        print(f"    views:  {printable(views['configured'] if views else None)} "
              f"(exists: {printable(views['exists'] if views else False)})")
        print(f"    assets: {printable(assets['configured'] if assets else None)} "
              f"(exists: {printable(assets['exists'] if assets else False)})")
        print(f"    build:  {printable(theme['vite']['build_directory'])}")

    registry = result["vite_registry"]
    print("\nVite registry")
    print(f"  Path:             {printable(registry['path'])}")
    print(f"  Keys:             {', '.join(registry['keys']) if registry['keys'] else 'none detected'}")

    print("\nRepository instructions")
    if result["instructions"]:
        for path in result["instructions"]:
            print(f"  {path}")
    else:
        print("  None detected")

    if result["warnings"]:
        print("\nWarnings")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inspection of a Bagisto storefront theme environment. "
            "Discovers the project root, package source, frontend versions, configured "
            "themes, Vite registry, and repository instruction files without booting Laravel."
        )
    )
    parser.add_argument(
        "--root",
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Bagisto root or a path below it (default: current directory)",
    )
    parser.add_argument(
        "--theme",
        "--theme-code",
        help="show one configured shop theme by code; no theme name is assumed",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit stable machine-readable JSON",
    )
    parser.add_argument(
        "--no-parent-search",
        action="store_true",
        help="require --root itself to be the Bagisto root",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = discover_root(args.root, search_parents=not args.no_parent_search)
    if root is None:
        message = f"no Bagisto project root found from {args.root.expanduser()}"
        if args.as_json:
            print(json.dumps({"schema_version": 1, "error": message}, indent=2))
        else:
            print(f"error: {message}", file=sys.stderr)
        return EXIT_NOT_FOUND

    result, status = inspect(root, args.theme)
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
