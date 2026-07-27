from __future__ import annotations

import importlib.util
import sys
import unittest
from argparse import Namespace
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scaffold_theme.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("scaffold_theme", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def scaffold_args(theme_code: str = "aurora") -> Namespace:
    return Namespace(
        vendor="Acme",
        package="AuroraTheme",
        theme_code=theme_code,
        display_name="Aurora's Atelier",
        mode="package",
        registration="local",
        bagisto_constraint=None,
        theme_license=None,
        theme_license_file=None,
        package_dir=None,
        override=[],
    )


class ScaffoldThemeInstallCommandTest(unittest.TestCase):
    def test_install_command_is_parameterized_and_collision_safe(self) -> None:
        source = MODULE.install_command_source(scaffold_args())

        self.assertIn("namespace Acme\\AuroraTheme\\Console\\Commands;", source)
        self.assertIn("protected $signature = 'aurora-theme:install';", source)
        self.assertIn("config('themes.shop.aurora')", source)
        self.assertIn("'--tag' => 'aurora-theme-views'", source)
        self.assertIn("vendor:publish", source)
        self.assertIn("optimize:clear", source)
        self.assertIn("manifest.json", source)
        self.assertNotIn("'--force'", source)

        for forbidden in ("Webkul", "PerfumeTheme", "Velora", "Seeder", "indexer:index"):
            self.assertNotIn(forbidden, source)

    def test_theme_suffix_is_not_duplicated_in_command_name(self) -> None:
        self.assertEqual(
            "aurora-theme:install",
            MODULE.installation_command_name("aurora-theme"),
        )

    def test_provider_registers_installer_only_for_console_runtime(self) -> None:
        source = MODULE.provider_source(
            scaffold_args(),
            "resources/themes/aurora/views",
        )

        self.assertIn(
            "use Acme\\AuroraTheme\\Console\\Commands\\InstallCommand;",
            source,
        )
        self.assertIn("$this->app->runningInConsole()", source)
        self.assertIn("InstallCommand::class", source)
        self.assertIn("realpath($publishedViewsPath) !== realpath($viewsPath)", source)
        self.assertIn("'aurora-theme-views'", source)


if __name__ == "__main__":
    unittest.main()
