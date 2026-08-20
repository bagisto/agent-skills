from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


inspector = load_script("inspect_bagisto_test_surface")
validator = load_script("validate_ownership_manifest")


class TestingToolTests(unittest.TestCase):
    def test_harness_and_checkout_scenario_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            harness = root / "packages/Webkul/Shop/tests/e2e-pw"
            (harness / "tests/checkout").mkdir(parents=True)
            (harness / "playwright.config.ts").write_text("export default {};", encoding="utf-8")
            (harness / "tests/search.spec.ts").write_text("test('search', () => {});", encoding="utf-8")
            (harness / "tests/checkout/simple-checkout.spec.ts").write_text("test('checkout', () => {});", encoding="utf-8")

            harnesses = inspector.discover_harnesses(root)

            self.assertEqual(len(harnesses), 1)
            self.assertEqual(harnesses[0]["spec_count"], 2)
            self.assertIn("search", harnesses[0]["feature_specs"])
            self.assertEqual(inspector.discover_checkout_scenarios(root), ["simple"])

    def test_registered_product_types_come_from_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "packages/Webkul/Product/src/Config/product_types.php"
            config.parent.mkdir(parents=True)
            config.write_text(
                "<?php return ['grouped' => ['key' => 'grouped'], 'simple' => ['key' => 'simple']];",
                encoding="utf-8",
            )

            self.assertEqual(inspector.discover_registered_product_types(root), ["grouped", "simple"])

    def test_payment_and_shipping_codes_are_inventory_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payment = root / "custom/Config/payment-methods.php"
            shipping = root / "custom/Config/carriers.php"
            payment.parent.mkdir(parents=True)
            payment.write_text("<?php return [['code' => 'sandbox_pay']];", encoding="utf-8")
            shipping.write_text("<?php return [['code' => 'test_ship']];", encoding="utf-8")

            self.assertEqual(inspector.discover_configured_codes(root, {"payment-methods.php"}), ["sandbox_pay"])
            self.assertEqual(inspector.discover_configured_codes(root, {"carriers.php"}), ["test_ship"])

    def test_complete_manifest_passes(self) -> None:
        journeys = [
            {
                "id": journey,
                "applicable": True,
                "result": "pass",
                "spec": "tests/theme.spec.ts",
                "test": f"proves {journey}",
            }
            for journey in sorted(validator.CORE_JOURNEYS)
        ]
        data = {
            "schema_version": 1,
            "theme_code": "test-theme",
            "environment": "isolated-e2e",
            "surfaces": [
                {
                    "id": "home.hero",
                    "kind": "editorial",
                    "route": "/",
                    "selector": "[data-testid=home-hero]",
                    "merchant_editable": True,
                    "owner": {
                        "type": "theme_customization",
                        "scope": ["theme", "channel", "locale"],
                    },
                    "evidence": {
                        "source_binding": "views/home/hero.blade.php",
                        "spec": "tests/theme-propagation.spec.ts",
                        "test": "updates and restores hero",
                        "propagation": {
                            "save": True,
                            "storefront": True,
                            "scope_isolation": True,
                            "restore": True,
                        },
                        "result": "pass",
                    },
                }
            ],
            "journeys": journeys,
            "cleanup": {"result": "pass", "evidence": "test teardown restored the original record"},
        }

        self.assertEqual(validator.validate_manifest(data, True, validator.CORE_JOURNEYS), [])

    def test_strict_manifest_rejects_hardcoded_editorial_content(self) -> None:
        data = {
            "schema_version": 1,
            "theme_code": "test-theme",
            "environment": "isolated-e2e",
            "surfaces": [
                {
                    "id": "home.hero",
                    "kind": "editorial",
                    "route": "/",
                    "selector": "h1",
                    "merchant_editable": False,
                    "owner": {"type": "code_structure", "scope": []},
                    "evidence": {"source_binding": "hero.blade.php", "result": "pass"},
                }
            ],
            "journeys": [],
            "cleanup": {"result": "pass", "evidence": "no mutations"},
        }

        errors = validator.validate_manifest(data, True, set())

        self.assertTrue(any("code_structure" in error for error in errors))
        self.assertTrue(any("merchant editable" in error for error in errors))

    def test_inventory_adds_registered_product_journeys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(
                json.dumps(
                    {
                        "required_journeys": [
                            {"id": "product-simple"},
                            {"id": "product-grouped"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                validator.required_journeys_from_inventory(path),
                {"product-simple", "product-grouped"},
            )


if __name__ == "__main__":
    unittest.main()
