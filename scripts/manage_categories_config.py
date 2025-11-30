#!/usr/bin/env python3
"""
Configuration Manager for Category Keywords

This tool allows you to manage category keywords and mappings through the command line,
making it easy to modify categorization rules without editing code.
"""

import sys
import os
import argparse
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.category_config import get_category_config


def list_categories():
    """List all categories and their keywords."""
    config = get_category_config()
    keywords = config.get_category_keywords()
    
    print("📋 CATEGORY CONFIGURATION")
    print("=" * 60)
    print(f"Total categories: {len(keywords)}")
    print(f"Default category: {config.get_default_category()}")
    print(f"Case sensitive: {config.is_case_sensitive()}")
    print()
    
    priority = config.get_category_priority()
    print("🎯 Category Priority Order:")
    for i, category in enumerate(priority, 1):
        keyword_count = len(keywords.get(category, []))
        print(f"  {i:2d}. {category} ({keyword_count} keywords)")
    print()
    
    print("📝 Categories and Keywords:")
    for category in sorted(keywords.keys()):
        keyword_list = keywords[category]
        print(f"\n🏷️  {category.upper()} ({len(keyword_list)} keywords):")
        
        # Show keywords in rows of 5
        for i in range(0, len(keyword_list), 5):
            row_keywords = keyword_list[i:i+5]
            print(f"    {', '.join(row_keywords)}")


def list_external_mappings():
    """List external category mappings."""
    config = get_category_config()
    
    print("🏦 EXTERNAL CATEGORY MAPPINGS")
    print("=" * 60)
    
    for source_type in ['chase_united', 'capital_one', 'usaa']:
        mappings = config.get_external_mappings(source_type)
        if mappings:
            print(f"\n📊 {source_type.replace('_', ' ').title()} Mappings:")
            for ext_cat, int_cat in mappings.items():
                print(f"    \"{ext_cat}\" → \"{int_cat}\"")


def add_keyword(category: str, keyword: str):
    """Add a keyword to a category."""
    config = get_category_config()
    
    try:
        config.add_category_keyword(category, keyword, save=True)
        print(f"✅ Added keyword '{keyword}' to category '{category}'")
        
        # Show updated keyword list
        keywords = config.get_category_keywords()
        if category in keywords:
            print(f"📋 {category} now has {len(keywords[category])} keywords:")
            print(f"    {', '.join(keywords[category])}")
    except Exception as e:
        print(f"❌ Error adding keyword: {e}")


def remove_keyword(category: str, keyword: str):
    """Remove a keyword from a category."""
    config = get_category_config()
    
    try:
        config.remove_category_keyword(category, keyword, save=True)
        print(f"✅ Removed keyword '{keyword}' from category '{category}'")
        
        # Show updated keyword list
        keywords = config.get_category_keywords()
        if category in keywords:
            print(f"📋 {category} now has {len(keywords[category])} keywords:")
            if keywords[category]:
                print(f"    {', '.join(keywords[category])}")
            else:
                print("    (no keywords)")
    except Exception as e:
        print(f"❌ Error removing keyword: {e}")


def test_categorization(descriptions: List[str]):
    """Test categorization on given descriptions."""
    config = get_category_config()
    
    print("🎯 CATEGORIZATION TEST")
    print("=" * 60)
    
    for desc in descriptions:
        category = config.categorize_by_keywords(desc)
        print(f"📝 \"{desc}\" → \"{category}\"")


def search_keywords(search_term: str):
    """Search for keywords containing the search term."""
    config = get_category_config()
    keywords = config.get_category_keywords()
    
    print(f"🔍 SEARCHING FOR KEYWORDS CONTAINING '{search_term}'")
    print("=" * 60)
    
    found = False
    search_lower = search_term.lower()
    
    for category, keyword_list in keywords.items():
        matching_keywords = [kw for kw in keyword_list if search_lower in kw.lower()]
        
        if matching_keywords:
            found = True
            print(f"📂 {category}:")
            for kw in matching_keywords:
                print(f"    ✓ {kw}")
    
    if not found:
        print(f"❌ No keywords found containing '{search_term}'")


def interactive_mode():
    """Interactive configuration management."""
    print("🎛️  INTERACTIVE CATEGORY CONFIGURATION")
    print("Available commands:")
    print("  list - Show all categories and keywords")
    print("  mappings - Show external category mappings") 
    print("  add <category> <keyword> - Add keyword to category")
    print("  remove <category> <keyword> - Remove keyword from category")
    print("  test <description> - Test categorization")
    print("  search <term> - Search for keywords")
    print("  reload - Reload configuration from file")
    print("  quit - Exit")
    print()
    
    config = get_category_config()
    
    while True:
        try:
            command = input("📝 Enter command: ").strip().split()
            if not command:
                continue
            
            if command[0] == 'quit':
                break
            elif command[0] == 'list':
                list_categories()
            elif command[0] == 'mappings':
                list_external_mappings()
            elif command[0] == 'add' and len(command) >= 3:
                add_keyword(command[1], ' '.join(command[2:]))
            elif command[0] == 'remove' and len(command) >= 3:
                remove_keyword(command[1], ' '.join(command[2:]))
            elif command[0] == 'test' and len(command) >= 2:
                test_categorization([' '.join(command[1:])])
            elif command[0] == 'search' and len(command) >= 2:
                search_keywords(' '.join(command[1:]))
            elif command[0] == 'reload':
                config.reload_config()
                print("✅ Configuration reloaded")
            else:
                print("❌ Invalid command. Type 'quit' to exit.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage category configuration")
    parser.add_argument('action', 
                       choices=['list', 'mappings', 'add', 'remove', 'test', 'search', 'interactive'],
                       help='Action to perform')
    parser.add_argument('--category', help='Category name')
    parser.add_argument('--keyword', help='Keyword to add/remove')
    parser.add_argument('--description', help='Description to test categorization')
    parser.add_argument('--search-term', help='Search term for keywords')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_categories()
    elif args.action == 'mappings':
        list_external_mappings()
    elif args.action == 'add':
        if not args.category or not args.keyword:
            print("❌ --category and --keyword required for add action")
            sys.exit(1)
        add_keyword(args.category, args.keyword)
    elif args.action == 'remove':
        if not args.category or not args.keyword:
            print("❌ --category and --keyword required for remove action")
            sys.exit(1)
        remove_keyword(args.category, args.keyword)
    elif args.action == 'test':
        if not args.description:
            print("❌ --description required for test action")
            sys.exit(1)
        test_categorization([args.description])
    elif args.action == 'search':
        if not args.search_term:
            print("❌ --search-term required for search action")
            sys.exit(1)
        search_keywords(args.search_term)
    elif args.action == 'interactive':
        interactive_mode()
