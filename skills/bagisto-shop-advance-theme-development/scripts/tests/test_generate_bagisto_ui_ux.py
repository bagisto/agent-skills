from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "generate_bagisto_ui_ux.py"
SPEC = importlib.util.spec_from_file_location("generate_bagisto_ui_ux", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def args_for(
    industry: str,
    audience: str,
    tone: str,
    catalog: str,
    price_position: str,
) -> Namespace:
    return Namespace(
        project_root=Path.cwd(),
        project_name="Example Store",
        product_type="e-commerce storefront",
        industry=industry,
        audience=audience,
        tone=tone,
        catalog=catalog,
        price_position=price_position,
        keyword=[],
        variance=6,
        motion=4,
        density=5,
        max_results=3,
    )


class GenerateBagistoUiUxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.knowledge = MODULE.load_knowledge()

    def test_builds_multidimensional_query(self) -> None:
        args = args_for("fragrance", "gift buyers", "editorial restrained", "curated catalog", "premium")
        args.keyword = ["ingredient-led", "mobile-first"]
        self.assertEqual(
            "e-commerce storefront fragrance gift buyers editorial restrained curated catalog premium ingredient-led mobile-first",
            MODULE.design_query(args),
        )

    def test_toy_store_selects_playful_guided_direction(self) -> None:
        args = args_for(
            "educational toys and STEM toys",
            "parents children families and gift buyers",
            "playful colorful trustworthy friendly",
            "broad age-led catalog",
            "mid-market",
        )
        ranked = MODULE.rank_items(
            self.knowledge["archetypes"],
            MODULE.design_query(args),
            3,
            {"variance": 7, "motion": 4, "density": 5},
        )
        self.assertEqual("playful-guided-discovery", ranked[0]["id"])

    def test_fragrance_store_selects_editorial_direction(self) -> None:
        args = args_for(
            "premium perfume and fragrance",
            "modern fragrance shoppers",
            "editorial sensory restrained luxury",
            "curated fragrance families",
            "premium",
        )
        ranked = MODULE.rank_items(
            self.knowledge["archetypes"],
            MODULE.design_query(args),
            3,
            {"variance": 6, "motion": 3, "density": 5},
        )
        self.assertEqual("editorial-story-commerce", ranked[0]["id"])

    def test_all_bundled_palette_pairs_meet_targets(self) -> None:
        pairs = [
            ("text", "canvas", 4.5),
            ("muted", "canvas", 4.5),
            ("on_brand", "brand", 4.5),
            ("on_accent", "accent", 4.5),
            ("control_border", "canvas", 3.0),
            ("focus", "canvas", 3.0),
        ]
        for palette in self.knowledge["palettes"]:
            roles = palette["roles"]
            for foreground, background, minimum in pairs:
                ratio = MODULE.contrast_ratio(roles[foreground], roles[background])
                self.assertIsNotNone(ratio)
                self.assertGreaterEqual(
                    ratio,
                    minimum,
                    f"{palette['id']} {foreground}/{background} is {ratio}",
                )

    def test_synthesis_is_self_contained_and_reduces_checkout_dials(self) -> None:
        args = args_for(
            "educational toys",
            "parents and gift buyers",
            "playful trustworthy",
            "broad age-led catalog",
            "mid-market",
        )
        args.variance = 8
        args.motion = 7
        environment = {
            "project": {"bagisto_version": "2.4.8", "laravel_constraint": "^11.0"},
            "frontend": {"versions": {"vue": "^3.5", "tailwindcss": "^3.4"}},
        }
        document = MODULE.synthesize(args, self.knowledge, environment, {"vue": "^3.5"})
        self.assertEqual("bagisto-ui-ux", document["source"]["engine"])
        self.assertFalse(document["source"]["external_dependency_used"])
        self.assertFalse(document["source"]["network_used"])
        self.assertEqual("playful-guided-discovery", document["design_system"]["archetype"]["id"])
        self.assertNotIn("into turn", document["design_system"]["concept"])
        self.assertLessEqual(document["design_system"]["page_dials"]["checkout"]["variance"], 3)
        self.assertLessEqual(document["design_system"]["page_dials"]["checkout"]["motion"], 2)
        self.assertEqual({"laravel", "vue", "html-tailwind"}, set(document["stack_guidance"]))

    def test_invalid_knowledge_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge.json"
            path.write_text('{"engine":"wrong"}', encoding="utf-8")
            with self.assertRaises(MODULE.BagistoUiUxError):
                MODULE.load_knowledge(path)

    def test_target_skill_contains_no_external_design_skill_dependency(self) -> None:
        root = SCRIPT.parents[1]
        forbidden = "ui-ux-" + "pro-max"
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            self.assertNotIn(forbidden, source.casefold(), str(path))


if __name__ == "__main__":
    unittest.main()
