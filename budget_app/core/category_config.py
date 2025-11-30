"""
Category Configuration Manager

This module handles loading and managing category rules from configuration files.
It replaces hardcoded category keywords and mappings with flexible, configurable rules.
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
import re


class CategoryConfig:
    """Manages category configuration from YAML files."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize category configuration.
        
        Args:
            config_path: Path to the YAML configuration file.
                        If None, uses default config/categories.yaml
        """
        if config_path is None:
            # Default to config/categories.yaml in the project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "categories.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Category config file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
    
    def get_category_keywords(self) -> Dict[str, List[str]]:
        """Get all category keyword patterns."""
        return self._config_data.get('category_keywords', {})
    
    def get_external_mappings(self, source_type: str) -> Dict[str, str]:
        """
        Get external category mappings for a specific source type.
        
        Args:
            source_type: Type of external source (e.g., 'chase_united', 'capital_one', 'usaa')
        
        Returns:
            Dictionary mapping external categories to internal categories
        """
        mappings = self._config_data.get('external_category_mappings', {})
        return mappings.get(source_type, {})
    
    def get_default_category(self) -> str:
        """Get the default category for unmatched transactions."""
        return self._config_data.get('settings', {}).get('default_category', 'misc')
    
    def is_case_sensitive(self) -> bool:
        """Check if keyword matching should be case sensitive."""
        return self._config_data.get('settings', {}).get('case_sensitive', False)
    
    def get_category_priority(self) -> List[str]:
        """Get the priority order for category checking."""
        return self._config_data.get('settings', {}).get('category_priority', [])
    
    def categorize_by_keywords(self, description: str, current_category: Optional[str] = None) -> str:
        """
        Categorize a transaction based on description keywords.
        
        Args:
            description: Transaction description to analyze
            current_category: Current category (if any) to preserve with '+' prefix
        
        Returns:
            Category name based on keyword matching
        """
        # If description starts with '+', keep current category unchanged
        if description and description.startswith('+'):
            return current_category or self.get_default_category()
        
        # Clean description for keyword matching
        desc_clean = self._clean_description(description)
        
        # Get keywords and priority order
        keywords = self.get_category_keywords()
        priority = self.get_category_priority()
        
        # Check categories in priority order
        for category in priority:
            if category in keywords:
                category_keywords = keywords[category]
                if self._matches_keywords(desc_clean, category_keywords):
                    return category
        
        # Check remaining categories not in priority list
        for category, category_keywords in keywords.items():
            if category not in priority:
                if self._matches_keywords(desc_clean, category_keywords):
                    return category
        
        return self.get_default_category()
    
    def map_external_category(self, external_category: str, source_type: str) -> str:
        """
        Map an external category to an internal category.
        
        Args:
            external_category: Category from external source
            source_type: Type of external source
        
        Returns:
            Mapped internal category name
        """
        mappings = self.get_external_mappings(source_type)
        external_lower = external_category.lower() if not self.is_case_sensitive() else external_category
        
        # Try exact match first
        if external_lower in mappings:
            return mappings[external_lower]
        
        # Try case-insensitive match if case sensitivity is disabled
        if not self.is_case_sensitive():
            for ext_cat, int_cat in mappings.items():
                if ext_cat.lower() == external_lower:
                    return int_cat
        
        return self.get_default_category()
    
    def _clean_description(self, description: str) -> str:
        """Clean description for keyword matching."""
        if not self.is_case_sensitive():
            description = description.lower()
        
        # Remove punctuation but keep spaces and alphanumeric
        return re.sub(r'[^\w\s]', ' ', description)
    
    def _matches_keywords(self, description: str, keywords: List[str]) -> bool:
        """Check if description matches any of the keywords."""
        for keyword in keywords:
            if not self.is_case_sensitive():
                keyword = keyword.lower()
            
            if keyword in description:
                return True
        
        return False
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_all_categories(self) -> List[str]:
        """Get list of all defined categories."""
        keywords = self.get_category_keywords()
        return list(keywords.keys()) + [self.get_default_category()]
    
    def add_category_keyword(self, category: str, keyword: str, save: bool = True) -> None:
        """
        Add a keyword to a category (runtime modification).
        
        Args:
            category: Category name
            keyword: Keyword to add
            save: Whether to save changes to file
        """
        if 'category_keywords' not in self._config_data:
            self._config_data['category_keywords'] = {}
        
        if category not in self._config_data['category_keywords']:
            self._config_data['category_keywords'][category] = []
        
        if keyword not in self._config_data['category_keywords'][category]:
            self._config_data['category_keywords'][category].append(keyword)
            
            if save:
                self._save_config()
    
    def remove_category_keyword(self, category: str, keyword: str, save: bool = True) -> None:
        """
        Remove a keyword from a category (runtime modification).
        
        Args:
            category: Category name
            keyword: Keyword to remove
            save: Whether to save changes to file
        """
        if (category in self._config_data.get('category_keywords', {}) and 
            keyword in self._config_data['category_keywords'][category]):
            
            self._config_data['category_keywords'][category].remove(keyword)
            
            if save:
                self._save_config()
    
    def _save_config(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._config_data, f, default_flow_style=False, sort_keys=False)


# Global configuration instance
_config_instance = None

def get_category_config() -> CategoryConfig:
    """Get the global category configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = CategoryConfig()
    return _config_instance

def reload_category_config() -> None:
    """Reload the global category configuration."""
    global _config_instance
    if _config_instance is not None:
        _config_instance.reload_config()
    else:
        _config_instance = CategoryConfig()
