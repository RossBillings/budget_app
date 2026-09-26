"""Tests for YAML-driven category rules."""
import tempfile
import unittest
from pathlib import Path

from budget_app.core.categorizer import CategoryRules


class TestCategoryRules(unittest.TestCase):
    def test_groceries_keyword(self):
        rules = CategoryRules.from_yaml(Path(__file__).resolve().parents[2] / "categories.yaml")
        self.assertEqual(
            rules.categorize("WEGMANS OWINGS MILLS #125", "merchandise"),
            "groceries",
        )

    def test_exclude_capital_one_payment(self):
        rules = CategoryRules.from_yaml(Path(__file__).resolve().parents[2] / "categories.yaml")
        self.assertTrue(rules.should_exclude("CAPITAL ONE MOBILE PYMT"))

    def test_amount_rule_preschool(self):
        rules = CategoryRules.from_yaml(Path(__file__).resolve().parents[2] / "categories.yaml")
        # unnamed check for exactly $290 → preschool
        self.assertEqual(rules.categorize("Check #0532", amount=290.00), "preschool")
        # keyword match still wins over amount rule
        self.assertEqual(rules.categorize("Wegmans", amount=290.00), "groceries")
        # different amount → misc
        self.assertEqual(rules.categorize("Check #0531", amount=350.00), "misc")

    def test_tithe_check_number_series(self):
        rules = CategoryRules.from_yaml(Path(__file__).resolve().parents[2] / "categories.yaml")
        self.assertEqual(rules.categorize("Check #995518", "check"), "tithe")
        self.assertEqual(rules.categorize("Check #995525", "check"), "tithe")
        self.assertEqual(rules.categorize("Check #0531", "check"), "misc")

    def test_custom_yaml(self):
        yaml_text = """
settings:
  default_category: misc
exclude_keywords: []
groups:
  - name: pets
    keywords: [chewy]
  - name: misc
    keywords: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_text)
            path = Path(f.name)

        rules = CategoryRules.from_yaml(path)
        self.assertEqual(rules.categorize("CHEWY.COM ORDER"), "pets")
        path.unlink()


if __name__ == "__main__":
    unittest.main()
