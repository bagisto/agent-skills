from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_theme_brief.py"
SPEC = importlib.util.spec_from_file_location("validate_theme_brief", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid_brief() -> str:
    headings = "\n".join(f"## {heading.title()}" for heading in sorted(MODULE.REQUIRED_HEADINGS))
    values = {
        field: "Defined decision with evidence"
        for field in MODULE.CRITICAL_FIELDS | MODULE.RECOMMENDED_FIELDS
    }
    values["theme code"] = "atelier-store"
    for field in MODULE.DIAL_FIELDS:
        values[field] = "6 — balanced for the primary journey"
    fields = "\n".join(f"- {field.title()}: {value}" for field, value in sorted(values.items()))
    return f"# Theme brief\n\n{headings}\n\n{fields}\n"


class ValidateThemeBriefTest(unittest.TestCase):
    def test_complete_brief_passes_strict_validation(self) -> None:
        findings = MODULE.validate(valid_brief())
        self.assertEqual([], findings)

    def test_template_placeholders_and_empty_fields_fail(self) -> None:
        findings = MODULE.validate(
            "## Identity\n- Theme code: `{{THEME_CODE}}`\n- Display name:\n"
        )
        self.assertTrue(any(item.check == "field.incomplete" for item in findings))
        self.assertTrue(any(item.check == "heading.required" for item in findings))

    def test_invalid_theme_code_and_dial_are_rejected(self) -> None:
        source = valid_brief().replace("atelier-store", "Atelier/Store", 1)
        source = source.replace("6 — balanced for the primary journey", "very high", 1)
        findings = MODULE.validate(source)
        self.assertTrue(any(item.check == "identity.theme-code" for item in findings))
        self.assertTrue(any(item.check == "dial.range" for item in findings))

    def test_html_elements_are_not_mistaken_for_placeholders(self) -> None:
        findings = MODULE.validate(valid_brief() + "\n- Markup requirement: Preserve <main>.\n")
        self.assertFalse(any(item.check == "brief.placeholders" for item in findings))

    def test_cli_returns_expected_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid_path = Path(directory) / "valid.md"
            valid_path.write_text(valid_brief(), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, MODULE.main(["--brief", str(valid_path), "--strict", "--json"]))

            invalid_path = Path(directory) / "invalid.md"
            invalid_path.write_text("# Theme brief\n", encoding="utf-8")
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, MODULE.main(["--brief", str(invalid_path), "--json"]))


if __name__ == "__main__":
    unittest.main()
