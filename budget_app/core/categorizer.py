"""Load and apply keyword-based category rules from categories.yaml."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "categories.yaml"


@dataclass(frozen=True)
class CategoryGroup:
    name: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class AmountRule:
    """Map a specific positive amount (absolute value) to a category."""
    category: str
    amount: float
    tolerance: float = 0.01  # cents-level rounding tolerance


@dataclass(frozen=True)
class CategoryRules:
    default_category: str
    exclude_keywords: tuple[str, ...]
    groups: tuple[CategoryGroup, ...]
    amount_rules: tuple[AmountRule, ...] = field(default_factory=tuple)

    @classmethod
    def from_yaml(cls, path: Path) -> "CategoryRules":
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        settings = data.get("settings") or {}
        default_category = str(settings.get("default_category", "misc")).strip().lower()

        exclude_keywords = tuple(
            kw.strip().lower()
            for kw in (data.get("exclude_keywords") or [])
            if str(kw).strip()
        )

        groups: List[CategoryGroup] = []
        for entry in data.get("groups") or []:
            name = str(entry.get("name", "")).strip().lower()
            if not name:
                continue
            keywords = tuple(
                str(kw).strip().lower()
                for kw in (entry.get("keywords") or [])
                if str(kw).strip()
            )
            groups.append(CategoryGroup(name=name, keywords=keywords))

        if not groups or groups[-1].name != default_category:
            groups.append(CategoryGroup(name=default_category, keywords=()))

        amount_rules: List[AmountRule] = []
        for entry in data.get("amount_rules") or []:
            name = str(entry.get("category", "")).strip().lower()
            raw_amount = entry.get("amount")
            if not name or raw_amount is None:
                continue
            tolerance = float(entry.get("tolerance", 0.01))
            amount_rules.append(
                AmountRule(category=name, amount=float(raw_amount), tolerance=tolerance)
            )

        return cls(
            default_category=default_category,
            exclude_keywords=exclude_keywords,
            groups=tuple(groups),
            amount_rules=tuple(amount_rules),
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^\w\s]", "", text.lower())

    def should_exclude(self, description: str) -> bool:
        normalized = self._normalize(description)
        return any(
            self._normalize(keyword) in normalized
            for keyword in self.exclude_keywords
        )

    def categorize(
        self,
        description: str,
        bank_category: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> str:
        """
        Return the mapped category for a transaction.

        Resolution order:
          1. keyword rules (description match)
          2. amount rules (exact amount match within tolerance)
          3. default category
        """
        if description.startswith("+"):
            return (bank_category or self.default_category).lower()

        normalized = self._normalize(description)
        for group in self.groups:
            if not group.keywords:
                # reached catch-all group — fall through to amount rules before defaulting
                break
            if any(self._normalize(kw) in normalized for kw in group.keywords):
                return group.name

        if amount is not None:
            abs_amount = abs(amount)
            for rule in self.amount_rules:
                if abs(abs_amount - rule.amount) <= rule.tolerance:
                    return rule.category

        return self.default_category


def get_categories_config_path() -> Path:
    env_path = os.getenv("CATEGORIES_CONFIG")
    if env_path:
        return Path(env_path)
    return _DEFAULT_CONFIG


def load_category_rules(path: Optional[Union[str, Path]] = None) -> CategoryRules:
    config_path = Path(path) if path else get_categories_config_path()
    if not config_path.is_file():
        raise FileNotFoundError(f"Category config not found: {config_path}")
    return CategoryRules.from_yaml(config_path)
