#!/usr/bin/env python3
"""
Quick category commands for advanced users.
Copy and paste these functions into a Python REPL for quick category management.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.models import Transaction, SessionLocal
from collections import Counter

# Quick category overview
def quick_overview():
    """Get a quick category overview."""
    db = SessionLocal()
    try:
        categories = Counter(t.category for t in db.query(Transaction).all())
        print(f"{'Category':<20} {'Count':<8}")
        print("-" * 30)
        for cat, count in categories.most_common():
            print(f"{cat:<20} {count:<8}")
    finally:
        db.close()

# Find transactions by pattern
def find_transactions(pattern, category=None, limit=10):
    """Find transactions matching a description pattern."""
    db = SessionLocal()
    try:
        query = db.query(Transaction).filter(
            Transaction.description.ilike(f'%{pattern}%')
        )
        if category:
            query = query.filter(Transaction.category == category)
        
        transactions = query.limit(limit).all()
        print(f"Found {len(transactions)} transactions matching '{pattern}':")
        for t in transactions:
            print(f"  {t.transaction_date} | ${t.amount:>8.2f} | {t.category:<15} | {t.description}")
    finally:
        db.close()

# Quick category update
def update_category(transaction_id_partial, new_category):
    """Update transaction category by partial ID."""
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(
            Transaction.id.like(f'{transaction_id_partial}%')
        ).first()
        
        if txn:
            old_cat = txn.category
            txn.category = new_category
            db.commit()
            print(f"✅ Updated {txn.id[:8]}: '{old_cat}' → '{new_category}'")
            print(f"   {txn.description}")
        else:
            print(f"❌ Transaction not found: {transaction_id_partial}")
    finally:
        db.close()

# Bulk update by pattern
def bulk_update(pattern, new_category, old_category=None):
    """Bulk update transactions matching pattern."""
    db = SessionLocal()
    try:
        query = db.query(Transaction).filter(
            Transaction.description.ilike(f'%{pattern}%')
        )
        if old_category:
            query = query.filter(Transaction.category == old_category)
        
        transactions = query.all()
        count = len(transactions)
        
        for txn in transactions:
            txn.category = new_category
        
        db.commit()
        print(f"✅ Updated {count} transactions to '{new_category}'")
    finally:
        db.close()

# Show problem categories
def show_problem_categories():
    """Show categories that likely need review."""
    db = SessionLocal()
    try:
        categories = Counter(t.category for t in db.query(Transaction).all())
        
        problems = {k: v for k, v in categories.items() 
                   if any(word in k.lower() for word in ['misc', 'pending', 'other', 'uncategorized'])}
        
        print("Categories needing review:")
        for cat, count in sorted(problems.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count} transactions")
    finally:
        db.close()

if __name__ == "__main__":
    print("Available functions:")
    print("  quick_overview() - Show category counts")
    print("  find_transactions('pattern', category=None, limit=10)")
    print("  update_category('partial_id', 'new_category')")
    print("  bulk_update('pattern', 'new_category', old_category=None)")
    print("  show_problem_categories()")
    print()
    print("Example usage:")
    print("  find_transactions('VERIZON')")
    print("  update_category('63ced0fc', 'utilities')")
    print("  bulk_update('AT&T', 'utilities', 'misc')")
