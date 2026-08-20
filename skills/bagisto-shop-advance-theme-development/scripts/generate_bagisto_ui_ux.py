#!/usr/bin/env python3
"""Generate a self-contained Bagisto storefront design direction."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "data" / "bagisto-ui-ux.json"

MANUAL_ACCEPTANCE = [
    "Explain why the selected archetype fits the brand, catalog, price position, audience, and primary journey.",
    "Turn the generated direction into a brand-specific concept; do not ship the candidate names as customer-facing copy.",
    "Approve every literal token, font asset, image, icon source, and motion behavior before implementation.",
    "Verify home, listing, product, cart, checkout, account, CMS, extension, empty, error, RTL, and reduced-motion states.",
    "Preserve installed Bagisto Blade, Vue, API, form, product-type, render-event, channel, and extension contracts.",
    "Review the finished storefront with real content at mobile, tablet, desktop, zoom, keyboard, and assistive-technology states.",
]

PROHIBITED_AUTO_ACTIONS = [
    "Do not install a package, framework, font, icon set, script, or design dependency automatically.",
    "Do not copy generic component-library markup over installed Bagisto components automatically.",
    "Do not hardcode catalog, price, inventory, cart, customer, checkout, channel, or merchant-managed content.",
    "Do not activate a channel, seed live content, or persist a generated brief unless the user authorizes it.",
]


class BagistoUiUxError(RuntimeError):
    """Raised when the bundled design engine cannot produce trustworthy output."""


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Bagisto-native storefront UI/UX candidates from bundled knowledge."
    )
    parser.add_argument("--project-root", default=".", type=Path, help="Bagisto project root")
    parser.add_argument("--project-name", required=True, help="storefront or brand display name")
    parser.add_argument("--product-type", default="e-commerce storefront", help="product/application type")
    parser.add_argument("--industry", required=True, help="retail industry or merchandise family")
    parser.add_argument("--audience", required=True, help="primary customer audience and context")
    parser.add_argument("--tone", required=True, help="desired emotional and visual tone")
    parser.add_argument("--catalog", required=True, help="catalog size, complexity, and buying behavior")
    parser.add_argument("--price-position", required=True, help="value, mid-market, premium, luxury, or equivalent")
    parser.add_argument("--keyword", action="append", default=[], help="additional direction term; repeat as needed")
    parser.add_argument("--variance", required=True, type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--motion", required=True, type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--density", required=True, type=int, choices=range(1, 11), metavar="1-10")
    parser.add_argument("--theme-code", help="existing configured theme to scope environment inspection")
    parser.add_argument("--package-dir", type=Path, help="optional theme package directory for dependency discovery")
    parser.add_argument("--max-results", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the complete machine-readable report")
    return parser.parse_args(argv)


def resolve_project_root(value: Path) -> Path:
    root = value.resolve()
    if not (root / "composer.json").is_file():
        raise BagistoUiUxError(f"Bagisto project composer.json not found: {root}")
    return root


def load_knowledge(path: Path = KNOWLEDGE_PATH) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BagistoUiUxError(f"cannot read bundled Bagisto UI/UX knowledge: {error}") from error

    if not isinstance(document, dict) or document.get("engine") != "bagisto-ui-ux":
        raise BagistoUiUxError("bundled Bagisto UI/UX knowledge has an invalid engine identity")
    for key in ("archetypes", "palettes", "typography", "page_blueprints", "stack_guidance"):
        if not document.get(key):
            raise BagistoUiUxError(f"bundled Bagisto UI/UX knowledge is missing {key}")
    return document


def inspect_environment(project_root: Path, theme_code: str | None) -> dict[str, Any]:
    inspector = Path(__file__).resolve().with_name("inspect_theme_environment.py")
    command = [sys.executable, "-B", str(inspector), "--project-root", str(project_root), "--json"]
    if theme_code:
        command[5:5] = ["--theme-code", theme_code]

    process = subprocess.run(
        command,
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=30,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or "unknown inspection failure"
        raise BagistoUiUxError(f"Bagisto environment inspection failed: {detail}")

    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise BagistoUiUxError(f"Bagisto inspector returned invalid JSON: {error}") from error
    if not isinstance(result, dict):
        raise BagistoUiUxError("Bagisto inspector returned a non-object result")
    return result


def package_dependencies(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BagistoUiUxError(f"cannot read package metadata {path}: {error}") from error
    if not isinstance(document, dict):
        return {}

    dependencies: dict[str, str] = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        values = document.get(section, {})
        if isinstance(values, dict):
            dependencies.update({str(name).casefold(): str(version) for name, version in values.items()})
    return dependencies


def installed_dependencies(
    project_root: Path,
    environment: dict[str, Any],
    package_dir: Path | None,
) -> dict[str, str]:
    paths = [project_root / "package.json"]
    frontend = environment.get("frontend", {})
    if isinstance(frontend, dict) and frontend.get("package_json"):
        paths.append(Path(str(frontend["package_json"])))
    if package_dir is not None:
        resolved = package_dir if package_dir.is_absolute() else project_root / package_dir
        paths.append(resolved / "package.json" if resolved.is_dir() else resolved)

    dependencies: dict[str, str] = {}
    for path in paths:
        dependencies.update(package_dependencies(path.resolve()))
    return dict(sorted(dependencies.items()))


def detected_stacks(environment: dict[str, Any]) -> list[str]:
    stacks: list[str] = []
    project = environment.get("project", {})
    frontend = environment.get("frontend", {})
    versions = frontend.get("versions", {}) if isinstance(frontend, dict) else {}
    keys = {str(key).casefold() for key in versions} if isinstance(versions, dict) else set()

    if isinstance(project, dict) and project.get("laravel_constraint"):
        stacks.append("laravel")
    if "vue" in keys:
        stacks.append("vue")
    if "tailwindcss" in keys:
        stacks.append("html-tailwind")
    return stacks


def design_query(args: argparse.Namespace) -> str:
    parts = [
        args.product_type,
        args.industry,
        args.audience,
        args.tone,
        args.catalog,
        args.price_position,
        *args.keyword,
    ]
    return " ".join(re.sub(r"\s+", " ", part).strip() for part in parts if part.strip())


def token_set(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def dial_score(value: int, limits: Any) -> float:
    if not isinstance(limits, list) or len(limits) != 2:
        return 0.0
    low, high = int(limits[0]), int(limits[1])
    if low <= value <= high:
        return 2.0
    distance = low - value if value < low else value - high
    return max(-3.0, 1.0 - distance)


def score_item(
    item: dict[str, Any],
    query: str,
    dials: dict[str, int] | None = None,
) -> tuple[float, list[str]]:
    normalized = query.casefold()
    query_tokens = token_set(query)
    matches: list[str] = []
    score = 0.0
    for raw in item.get("tags", []):
        tag = str(raw).casefold().strip()
        if not tag:
            continue
        if tag in normalized:
            score += 6.0 if " " in tag else 4.0
            matches.append(tag)
        elif token_set(tag).intersection(query_tokens):
            score += 1.0

    if dials:
        fit = item.get("dial_fit", {})
        if isinstance(fit, dict):
            score += sum(dial_score(value, fit.get(name)) for name, value in dials.items())
    return score, sorted(set(matches))


def rank_items(
    items: Any,
    query: str,
    limit: int,
    dials: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise BagistoUiUxError("bundled candidate collection must be a list")
    ranked: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        score, matches = score_item(raw, query, dials)
        ranked.append({"score": round(score, 2), "matched_terms": matches, **raw})
    ranked.sort(key=lambda item: (-float(item["score"]), str(item.get("id", ""))))
    return ranked[:limit]


def hex_rgb(value: str) -> tuple[float, float, float] | None:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return None
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))  # type: ignore[return-value]


def relative_luminance(value: str) -> float | None:
    rgb = hex_rgb(value)
    if rgb is None:
        return None
    channels = [
        channel / 12.92 if channel <= 0.04045 else math.pow((channel + 0.055) / 1.055, 2.4)
        for channel in rgb
    ]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first: str, second: str) -> float | None:
    left = relative_luminance(first)
    right = relative_luminance(second)
    if left is None or right is None:
        return None
    lighter, darker = max(left, right), min(left, right)
    return (lighter + 0.05) / (darker + 0.05)


def spacing_tokens(density: int) -> dict[str, str]:
    if density <= 3:
        return {"control_gap": "0.75rem", "cluster": "1.5rem", "section": "clamp(4rem, 9vw, 8rem)", "gutter": "clamp(1rem, 4vw, 4rem)", "measure": "68ch"}
    if density <= 7:
        return {"control_gap": "0.5rem", "cluster": "1rem", "section": "clamp(3rem, 7vw, 6rem)", "gutter": "clamp(1rem, 3vw, 3rem)", "measure": "70ch"}
    return {"control_gap": "0.375rem", "cluster": "0.75rem", "section": "clamp(2rem, 5vw, 4rem)", "gutter": "clamp(0.75rem, 2vw, 2rem)", "measure": "72ch"}


def shape_tokens(archetype_id: str) -> dict[str, str]:
    if archetype_id == "playful-guided-discovery":
        return {"control": "0.75rem", "card": "1rem", "media": "1.25rem", "modal": "1rem", "badge": "999px"}
    if archetype_id in {"precision-minimal-commerce", "technical-confidence-retail"}:
        return {"control": "0.375rem", "card": "0.5rem", "media": "0.5rem", "modal": "0.625rem", "badge": "0.25rem"}
    return {"control": "0.5rem", "card": "0.75rem", "media": "0.75rem", "modal": "0.75rem", "badge": "999px"}


def motion_tokens(motion: int) -> dict[str, str]:
    if motion <= 2:
        return {"fast": "100ms", "standard": "160ms", "deliberate": "220ms", "enter": "cubic-bezier(0.23, 1, 0.32, 1)", "exit": "cubic-bezier(0.4, 0, 1, 1)", "distance": "4px"}
    if motion <= 6:
        return {"fast": "120ms", "standard": "200ms", "deliberate": "280ms", "enter": "cubic-bezier(0.23, 1, 0.32, 1)", "exit": "cubic-bezier(0.4, 0, 1, 1)", "distance": "8px"}
    return {"fast": "140ms", "standard": "240ms", "deliberate": "360ms campaign-only", "enter": "cubic-bezier(0.23, 1, 0.32, 1)", "exit": "cubic-bezier(0.4, 0, 1, 1)", "distance": "12px campaign-only"}


def page_dials(variance: int, motion: int, density: int) -> dict[str, dict[str, int]]:
    return {
        "home": {"variance": variance, "motion": motion, "density": density},
        "listing": {"variance": min(variance, 6), "motion": min(motion, 4), "density": max(density, 5)},
        "product": {"variance": min(variance, 6), "motion": min(motion, 4), "density": min(max(density, 4), 7)},
        "cart": {"variance": min(variance, 4), "motion": min(motion, 3), "density": min(max(density, 4), 7)},
        "checkout": {"variance": min(variance, 3), "motion": min(motion, 2), "density": min(max(density, 4), 6)},
        "account": {"variance": min(variance, 4), "motion": min(motion, 3), "density": min(max(density, 5), 7)},
    }


def review_findings(
    palette: dict[str, Any],
    stacks: list[str],
    variance: int,
    motion: int,
    density: int,
) -> list[Finding]:
    findings: list[Finding] = []
    roles = palette.get("roles", {})
    pairs = [
        ("text", "canvas", 4.5),
        ("muted", "canvas", 4.5),
        ("on_brand", "brand", 4.5),
        ("on_accent", "accent", 4.5),
        ("control_border", "canvas", 3.0),
        ("focus", "canvas", 3.0),
    ]
    if isinstance(roles, dict):
        for foreground, background, minimum in pairs:
            first, second = roles.get(foreground), roles.get(background)
            if not isinstance(first, str) or not isinstance(second, str):
                findings.append(Finding("fail", "color.role-missing", f"palette is missing {foreground} or {background}"))
                continue
            ratio = contrast_ratio(first, second)
            if ratio is None or ratio < minimum:
                evidence = f"{first} on {second}: {ratio:.2f}:1" if ratio is not None else f"{first} on {second}"
                findings.append(Finding("fail", "color.contrast", f"{foreground}/{background} must reach {minimum:.1f}:1", evidence))

    if "laravel" not in stacks:
        findings.append(Finding("warning", "stack.laravel-unresolved", "Laravel was not resolved from the checkout; verify this is the intended Bagisto root."))
    if "vue" not in stacks:
        findings.append(Finding("warning", "stack.vue-unresolved", "Vue was not resolved; inspect the installed Shop asset runtime before implementing interactive components."))
    if "html-tailwind" not in stacks:
        findings.append(Finding("warning", "stack.tailwind-unresolved", "Tailwind was not resolved; use the installed asset contract rather than assuming utility support."))
    if variance >= 8:
        findings.append(Finding("warning", "dial.variance-high", "High variance needs a simpler listing, product, cart, checkout, and account composition."))
    if motion >= 7:
        findings.append(Finding("warning", "dial.motion-high", "High motion is campaign-only; frequent commerce interactions must remain fast, interruptible, and reduced-motion safe."))
    if density >= 8:
        findings.append(Finding("warning", "dial.density-high", "High density requires explicit mobile reflow, 44px targets, 16px inputs, and content-extreme testing."))
    findings.append(Finding("review", "assets.approval-required", "Typography, icons, photography, and illustration directions are strategies only; approve actual files, licenses, and budgets before bundling."))
    return findings


def synthesize(
    args: argparse.Namespace,
    knowledge: dict[str, Any],
    environment: dict[str, Any],
    dependencies: dict[str, str],
) -> dict[str, Any]:
    query = design_query(args)
    dials = {"variance": args.variance, "motion": args.motion, "density": args.density}
    archetypes = rank_items(knowledge["archetypes"], query, args.max_results, dials)
    palettes = rank_items(knowledge["palettes"], query, args.max_results)
    typography = rank_items(knowledge["typography"], query, args.max_results)
    if not archetypes or not palettes or not typography:
        raise BagistoUiUxError("bundled knowledge returned an incomplete design direction")

    primary = archetypes[0]
    supporting = archetypes[1] if len(archetypes) > 1 and archetypes[1]["score"] > 0 else None
    palette = palettes[0]
    type_strategy = typography[0]
    stacks = detected_stacks(environment)
    project = environment.get("project", {})
    bagisto_version = project.get("bagisto_version") if isinstance(project, dict) else None
    stack_source = knowledge["stack_guidance"]
    stack_guidance = {stack: stack_source[stack] for stack in stacks if stack in stack_source}
    findings = review_findings(palette, stacks, args.variance, args.motion, args.density)

    concept_body = str(primary["concept"]).strip().rstrip(".")
    if concept_body.casefold().startswith("use "):
        concept_body = concept_body[4:]
    concept_body = concept_body[:1].casefold() + concept_body[1:]
    concept = (
        f"{args.project_name} applies {str(primary['name']).casefold()} to {concept_body}, "
        f"serving {args.audience} across its {args.price_position} {args.industry} offer."
    )
    knowledge_bytes = KNOWLEDGE_PATH.read_bytes()
    return {
        "schema_version": 2,
        "source": {
            "engine": "bagisto-ui-ux",
            "knowledge": str(KNOWLEDGE_PATH),
            "knowledge_sha256": hashlib.sha256(knowledge_bytes).hexdigest(),
            "external_dependency_used": False,
            "network_used": False,
            "persistence_used": False,
            "query": query,
        },
        "project": {
            "root": str(args.project_root.resolve()),
            "bagisto_version": bagisto_version,
            "detected_stacks": stacks,
            "frontend_dependencies": dependencies,
        },
        "inputs": {
            "project_name": args.project_name,
            "industry": args.industry,
            "audience": args.audience,
            "tone": args.tone,
            "catalog": args.catalog,
            "price_position": args.price_position,
            **dials,
        },
        "design_system": {
            "status": "candidate-requires-approval",
            "concept": concept,
            "archetype": primary,
            "supporting_influence": supporting,
            "palette": palette,
            "typography": type_strategy,
            "semantic_tokens": {
                "colors": palette["roles"],
                "spacing": spacing_tokens(args.density),
                "shape": shape_tokens(str(primary["id"])),
                "motion": motion_tokens(args.motion),
                "layering": {"content": 0, "sticky": 20, "dropdown": 40, "drawer": 60, "modal": 80, "toast": 100},
            },
            "page_dials": page_dials(args.variance, args.motion, args.density),
            "page_blueprints": knowledge["page_blueprints"],
            "responsive_policy": [
                "Start from customer-task priority and content fit, then add breakpoints.",
                "Define explicit mobile order, drawer behavior, sticky offsets, media ratios, and action placement.",
                "Use logical properties and test translated, RTL, zoomed, long, missing, and unavailable content.",
            ],
            "interaction_policy": [
                "Animate only to explain spatial change, state, feedback, or continuity.",
                "Use exact transition properties; prefer transform and opacity and keep frequent actions nearly instant.",
                "Gate hover effects to fine pointers, keep keyboard actions immediate, and provide reduced-motion alternatives.",
                "Return focus after overlays, synchronize ARIA state, and never delay authoritative commerce feedback.",
            ],
            "content_ownership": {
                "catalog": "products, categories, price, stock, attributes, reviews, relations",
                "theme_customization": "ordered campaigns, merchandising sections, services, and theme-scoped media",
                "cms": "localized editorial pages and managed long-form content",
                "channel": "logo, favicon, locale, currency, root category, home SEO",
                "theme_package": "tokens, presentation, stable labels, interface assets, and fallbacks",
                "extension": "payment, shipping, product-type, account, event, and extension-owned output",
            },
            "anti_generic_checks": [
                "Remove the logo mentally; at least three repeated visual signatures must still identify the brand.",
                "Do not use the same composition for hero, product rail, story, evidence, and testimonial sections.",
                "Avoid decorative gradients, glass, pills, shadows, animation, or oversized type without a named role.",
                "Ensure listing, product, cart, checkout, account, and system pages share the brand without copying the homepage layout.",
            ],
        },
        "alternatives": {
            "archetypes": archetypes,
            "palettes": palettes,
            "typography": typography,
        },
        "stack_guidance": stack_guidance,
        "bagisto_review": {
            "status": "candidate-only",
            "findings": [asdict(item) for item in findings],
            "manual_acceptance": MANUAL_ACCEPTANCE,
            "prohibited_auto_actions": PROHIBITED_AUTO_ACTIONS,
        },
        "summary": {
            "findings": len(findings),
            "failures": sum(item.severity == "fail" for item in findings),
            "candidate_archetypes": len(archetypes),
            "candidate_palettes": len(palettes),
            "candidate_typography": len(typography),
        },
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    project_root = resolve_project_root(args.project_root)
    args.project_root = project_root
    knowledge = load_knowledge()
    environment = inspect_environment(project_root, args.theme_code)
    dependencies = installed_dependencies(project_root, environment, args.package_dir)
    return synthesize(args, knowledge, environment, dependencies)


def print_human(document: dict[str, Any]) -> None:
    system = document["design_system"]
    source = document["source"]
    print(f"Design engine: {source['engine']} (self-contained)")
    print(f"Query: {source['query']}")
    print(f"Concept: {system['concept']}")
    print(f"Archetype: {system['archetype']['name']}")
    print(f"Palette: {system['palette']['name']}")
    print(f"Typography: {system['typography']['name']}")
    print(f"Stacks: {', '.join(document['project']['detected_stacks']) or 'unresolved'}")
    findings = document["bagisto_review"]["findings"]
    print(f"Bagisto review findings: {len(findings)}")
    for finding in findings:
        print(f"- {finding['severity'].upper()} {finding['code']}: {finding['message']}")
    print("Use --json to inspect alternatives, tokens, page blueprints, and acceptance gates.")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        document = collect(args)
    except (BagistoUiUxError, OSError, subprocess.SubprocessError) as error:
        if args.as_json:
            print(json.dumps({"error": str(error)}, indent=2))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(document, indent=2, ensure_ascii=False))
    else:
        print_human(document)
    return 1 if document["summary"]["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
