#!/usr/bin/env python3
"""
Category Manager - Review, verify, and update transaction categories.

This script provides tools to:
1. Review transactions by category with samples
2. Find transactions that might be miscategorized
3. Bulk update categories based on description patterns
4. Interactive category updates
"""

import sys
import os
from typing import List, Dict, Optional
from collections import Counter
import re

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.models import Transaction, SessionLocal
from budget_app.core.database import get_db


def review_categories(limit_per_category: int = 5) -> None:
    """Review all categories with sample transactions."""
    print("=" * 60)
    print("CATEGORY REVIEW SUMMARY")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get category counts
        all_transactions = db.query(Transaction).all()
        categories = Counter(t.category for t in all_transactions)
        
        print(f"Total categories: {len(categories)}")
        print(f"Total transactions: {len(all_transactions)}")
        print()
        
        # Show each category with samples
        for category, count in categories.most_common():
            print(f"📁 {category.upper()}: {count} transactions")
            
            # Get sample transactions
            samples = db.query(Transaction).filter_by(category=category).limit(limit_per_category).all()
            for sample in samples:
                amount_str = f"${sample.amount:.2f}".rjust(10)
                print(f"   {sample.transaction_date} | {amount_str} | {sample.description[:45]}")
            
            if count > limit_per_category:
                print(f"   ... and {count - limit_per_category} more")
            print()
            
    finally:
        db.close()


def find_miscategorized_transactions(category: str = "misc", keyword_patterns: Dict[str, str] = None) -> None:
    """Find transactions that might be miscategorized based on description patterns."""
    if keyword_patterns is None:
        # Load patterns from configuration file
        from budget_app.core.category_config import get_category_config
        config = get_category_config()
        keyword_patterns = config.get_category_keywords()
    
    print("=" * 60)
    print(f"ANALYZING '{category.upper()}' TRANSACTIONS FOR RECATEGORIZATION")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).filter_by(category=category).all()
        suggestions = {}
        
        for txn in transactions:
            desc_lower = txn.description.lower()
            for suggested_category, keywords in keyword_patterns.items():
                if any(keyword in desc_lower for keyword in keywords):
                    if suggested_category not in suggestions:
                        suggestions[suggested_category] = []
                    suggestions[suggested_category].append(txn)
        
        if not suggestions:
            print(f"✅ No obvious recategorization suggestions found for '{category}' transactions.")
            return
        
        print(f"Found {sum(len(txns) for txns in suggestions.values())} transactions that might need recategorization:\n")
        
        for suggested_category, txns in suggestions.items():
            print(f"🔄 Suggest '{suggested_category.upper()}' ({len(txns)} transactions):")
            for txn in txns[:10]:  # Show first 10
                print(f"   {txn.transaction_date} | ${txn.amount:>8.2f} | {txn.description[:45]} | ID: {txn.id[:8]}")
            if len(txns) > 10:
                print(f"   ... and {len(txns) - 10} more")
            print()
            
    finally:
        db.close()


def bulk_update_category(old_category: str, new_category: str, description_pattern: str = None) -> int:
    """Bulk update categories based on description patterns or category name."""
    db = SessionLocal()
    updated_count = 0
    
    try:
        query = db.query(Transaction)
        
        if description_pattern:
            # Update based on description pattern
            query = query.filter(
                Transaction.category == old_category,
                Transaction.description.ilike(f'%{description_pattern}%')
            )
            print(f"Updating transactions in '{old_category}' containing '{description_pattern}' to '{new_category}'...")
        else:
            # Update all transactions in the category
            query = query.filter(Transaction.category == old_category)
            print(f"Updating ALL transactions from '{old_category}' to '{new_category}'...")
        
        transactions = query.all()
        
        for txn in transactions:
            txn.category = new_category
            updated_count += 1
        
        db.commit()
        print(f"✅ Successfully updated {updated_count} transactions.")
        
        if updated_count > 0:
            print("\nSample updated transactions:")
            for i, txn in enumerate(transactions[:5]):
                print(f"   {txn.transaction_date} | ${txn.amount:>8.2f} | {txn.description[:45]}")
            if len(transactions) > 5:
                print(f"   ... and {len(transactions) - 5} more")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating categories: {e}")
    finally:
        db.close()
    
    return updated_count


def show_category_suggestions(category: str = "misc") -> None:
    """Show suggested category updates for review before applying."""
    print("=" * 60)
    print(f"SUGGESTED UPDATES FOR '{category.upper()}' CATEGORY")
    print("=" * 60)
    
    suggestions = [
        ("Target", "target", "TARGET"),
        ("Walmart", "groceries", "WAL-MART"),
        ("Wegmans", "groceries", "WEGMANS"),
        ("Costco", "groceries", "COSTCO"),
        ("AT&T", "utilities", "AT&T"),
        ("Verizon", "utilities", "VERIZON"),
        ("Shell", "gas", "SHELL"),
        ("Royal Farms", "gas", "ROYAL"),
        ("Chick-fil-A", "dining", "CHICK-FIL-A"),
        ("Starbucks", "dining", "STARBUCKS"),
        ("Amazon", "shopping", "AMAZON"),
        ("Party City", "shopping", "PARTY CITY"),
        ("Walgreens", "health", "WALGREENS"),
        ("CVS", "health", "CVS"),
        ("Home Depot", "home_supplies", "HOME DEPOT"),
    ]
    
    db = SessionLocal()
    try:
        for store_name, suggested_cat, pattern in suggestions:
            count = db.query(Transaction).filter(
                Transaction.category == category,
                Transaction.description.ilike(f'%{pattern}%')
            ).count()
            
            if count > 0:
                print(f"📦 {store_name}: {count} transactions → suggest '{suggested_cat}'")
                print(f"   Command: bulk_update_category('{category}', '{suggested_cat}', '{pattern}')")
                
                # Show sample
                sample = db.query(Transaction).filter(
                    Transaction.category == category,
                    Transaction.description.ilike(f'%{pattern}%')
                ).first()
                if sample:
                    print(f"   Sample: {sample.description}")
                print()
                
    finally:
        db.close()


def interactive_mode():
    """Interactive category management."""
    print("🎯 INTERACTIVE CATEGORY MANAGER")
    print("Available commands:")
    print("  1. review - Review all categories")
    print("  2. analyze <category> - Analyze specific category for recategorization")
    print("  3. suggest <category> - Show suggested updates")
    print("  4. update <old_cat> <new_cat> [pattern] - Bulk update categories")
    print("  5. quit - Exit")
    print()
    
    while True:
        try:
            command = input("📝 Enter command: ").strip().split()
            if not command:
                continue
                
            if command[0] == 'quit':
                break
            elif command[0] == 'review':
                review_categories()
            elif command[0] == 'analyze' and len(command) > 1:
                find_miscategorized_transactions(command[1])
            elif command[0] == 'suggest' and len(command) > 1:
                show_category_suggestions(command[1])
            elif command[0] == 'update' and len(command) >= 3:
                old_cat, new_cat = command[1], command[2]
                pattern = command[3] if len(command) > 3 else None
                bulk_update_category(old_cat, new_cat, pattern)
            else:
                print("❌ Invalid command. Type 'quit' to exit.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Category Manager for Budget App")
    parser.add_argument('action', choices=['review', 'analyze', 'suggest', 'update', 'interactive'], 
                        help='Action to perform')
    parser.add_argument('--category', default='misc', help='Category to analyze/update')
    parser.add_argument('--new-category', help='New category name for updates')
    parser.add_argument('--pattern', help='Description pattern to match for updates')
    
    args = parser.parse_args()
    
    if args.action == 'review':
        review_categories()
    elif args.action == 'analyze':
        find_miscategorized_transactions(args.category)
    elif args.action == 'suggest':
        show_category_suggestions(args.category)
    elif args.action == 'update':
        if not args.new_category:
            print("❌ --new-category required for update action")
            sys.exit(1)
        bulk_update_category(args.category, args.new_category, args.pattern)
    elif args.action == 'interactive':
        interactive_mode()
