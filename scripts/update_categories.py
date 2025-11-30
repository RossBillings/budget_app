#!/usr/bin/env python3
"""
Simple Category Updater - Quick manual category updates by transaction ID or pattern.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.models import Transaction, SessionLocal


def update_single_transaction(transaction_id: str, new_category: str) -> bool:
    """Update a single transaction's category by ID."""
    db = SessionLocal()
    try:
        # Find transaction (support partial ID matching)
        if len(transaction_id) < 36:  # Partial ID
            transaction = db.query(Transaction).filter(
                Transaction.id.like(f'{transaction_id}%')
            ).first()
        else:  # Full ID
            transaction = db.query(Transaction).filter_by(id=transaction_id).first()
        
        if not transaction:
            print(f"❌ Transaction not found: {transaction_id}")
            return False
        
        old_category = transaction.category
        transaction.category = new_category
        db.commit()
        
        print(f"✅ Updated transaction {transaction.id[:8]}:")
        print(f"   {transaction.transaction_date} | {transaction.description}")
        print(f"   Category: '{old_category}' → '{new_category}'")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating transaction: {e}")
        return False
    finally:
        db.close()


def batch_update_by_description(pattern: str, new_category: str, old_category: str = None) -> int:
    """Update multiple transactions by description pattern."""
    db = SessionLocal()
    try:
        query = db.query(Transaction).filter(
            Transaction.description.ilike(f'%{pattern}%')
        )
        
        if old_category:
            query = query.filter(Transaction.category == old_category)
        
        transactions = query.all()
        
        if not transactions:
            print(f"❌ No transactions found matching pattern: {pattern}")
            return 0
        
        print(f"Found {len(transactions)} transactions matching '{pattern}':")
        for i, txn in enumerate(transactions[:5]):
            print(f"  {i+1}. {txn.transaction_date} | {txn.description[:50]} | {txn.category}")
        
        if len(transactions) > 5:
            print(f"  ... and {len(transactions) - 5} more")
        
        confirm = input(f"\\nUpdate all {len(transactions)} transactions to '{new_category}'? (y/N): ")
        
        if confirm.lower() != 'y':
            print("❌ Update cancelled.")
            return 0
        
        updated = 0
        for txn in transactions:
            txn.category = new_category
            updated += 1
        
        db.commit()
        print(f"✅ Updated {updated} transactions to '{new_category}'")
        return updated
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error updating transactions: {e}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update transaction categories")
    parser.add_argument('action', choices=['single', 'batch'], help='Update type')
    parser.add_argument('--id', help='Transaction ID (for single updates)')
    parser.add_argument('--pattern', help='Description pattern to match (for batch updates)')
    parser.add_argument('--category', required=True, help='New category name')
    parser.add_argument('--old-category', help='Only update transactions in this category')
    
    args = parser.parse_args()
    
    if args.action == 'single':
        if not args.id:
            print("❌ --id required for single updates")
            sys.exit(1)
        update_single_transaction(args.id, args.category)
    
    elif args.action == 'batch':
        if not args.pattern:
            print("❌ --pattern required for batch updates")
            sys.exit(1)
        batch_update_by_description(args.pattern, args.category, args.old_category)
