#!/usr/bin/env python3
"""
Fix Transaction Signs

This script corrects the signs of all transactions in the database to ensure:
- Normal expenses are positive
- Refunds/returns are negative

It analyzes transactions by source and applies the appropriate sign corrections.
"""

import sys
import os
from typing import Dict, List
from collections import Counter

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.models import Transaction, SessionLocal


def analyze_current_signs():
    """Analyze current transaction signs by source."""
    print("🔍 ANALYZING CURRENT TRANSACTION SIGNS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get statistics by source
        sources = db.query(Transaction.source).distinct().all()
        
        for source_tuple in sources:
            source = source_tuple[0]
            transactions = db.query(Transaction).filter_by(source=source).all()
            
            positive_count = sum(1 for t in transactions if t.amount > 0)
            negative_count = sum(1 for t in transactions if t.amount < 0)
            
            print(f"\n📊 {source}:")
            print(f"  Total: {len(transactions)}")
            print(f"  Positive: {positive_count}")
            print(f"  Negative: {negative_count}")
            
            # Show some examples
            if negative_count > 0:
                negative_examples = [t for t in transactions if t.amount < 0][:3]
                print(f"  Negative examples:")
                for t in negative_examples:
                    print(f"    {t.transaction_date} | ${t.amount:8.2f} | {t.description[:30]}")
            
            # Check for returns in descriptions
            returns = [t for t in transactions if 'return' in t.description.lower()]
            if returns:
                print(f"  Found {len(returns)} transactions with 'return' in description")
    finally:
        db.close()


def fix_capital_one_signs(dry_run=True):
    """Fix Capital One transactions - make expenses positive."""
    print("\n🔧 FIXING CAPITAL ONE SIGNS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Find Capital One transactions with negative amounts (these should be positive expenses)
        capone_transactions = db.query(Transaction).filter(
            Transaction.source.ilike('%capone%'),
            Transaction.amount < 0
        ).all()
        
        print(f"Found {len(capone_transactions)} Capital One transactions with negative amounts")
        
        if not capone_transactions:
            print("✅ No Capital One transactions need sign correction")
            return 0
        
        # Show examples
        print("\nExamples of transactions to fix:")
        for t in capone_transactions[:5]:
            print(f"  {t.transaction_date} | ${t.amount:8.2f} → ${abs(t.amount):8.2f} | {t.description[:30]}")
        
        if len(capone_transactions) > 5:
            print(f"  ... and {len(capone_transactions) - 5} more")
        
        if dry_run:
            print(f"\n🧪 DRY RUN: Would fix {len(capone_transactions)} Capital One transactions")
            return len(capone_transactions)
        
        # Apply fixes (auto-confirm in non-interactive mode)
        print(f"\n✅ Auto-confirming fix for {len(capone_transactions)} Capital One transactions")
        
        fixed_count = 0
        for transaction in capone_transactions:
            # Make negative amounts positive (expenses)
            transaction.amount = abs(transaction.amount)
            fixed_count += 1
        
        db.commit()
        print(f"✅ Fixed {fixed_count} Capital One transactions")
        return fixed_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return 0
    finally:
        db.close()


def fix_chase_united_signs(dry_run=True):
    """Fix Chase United transactions - make expenses positive, returns negative."""
    print("\n🔧 FIXING CHASE UNITED SIGNS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Find Chase United transactions
        chase_transactions = db.query(Transaction).filter(
            Transaction.source.ilike('%chase%')
        ).all()
        
        print(f"Found {len(chase_transactions)} Chase United transactions")
        
        if not chase_transactions:
            print("✅ No Chase United transactions found")
            return 0
        
        # Analyze which ones need fixing
        expenses_to_fix = []  # negative amounts that should be positive
        returns_to_fix = []   # positive amounts that should be negative (if they're returns)
        
        for t in chase_transactions:
            if t.amount < 0 and 'return' not in t.description.lower():
                # Negative amount, not a return -> should be positive expense
                expenses_to_fix.append(t)
            elif t.amount > 0 and 'return' in t.description.lower():
                # Positive amount, is a return -> should be negative
                returns_to_fix.append(t)
        
        total_to_fix = len(expenses_to_fix) + len(returns_to_fix)
        
        if total_to_fix == 0:
            print("✅ No Chase United transactions need sign correction")
            return 0
        
        print(f"\nTransactions to fix:")
        print(f"  Expenses (negative→positive): {len(expenses_to_fix)}")
        print(f"  Returns (positive→negative): {len(returns_to_fix)}")
        
        # Show examples
        if expenses_to_fix:
            print(f"\n💰 Expense examples:")
            for t in expenses_to_fix[:3]:
                print(f"  {t.transaction_date} | ${t.amount:8.2f} → ${abs(t.amount):8.2f} | {t.description[:30]}")
        
        if returns_to_fix:
            print(f"\n↩️  Return examples:")
            for t in returns_to_fix[:3]:
                print(f"  {t.transaction_date} | ${t.amount:8.2f} → ${-abs(t.amount):8.2f} | {t.description[:30]}")
        
        if dry_run:
            print(f"\n🧪 DRY RUN: Would fix {total_to_fix} Chase United transactions")
            return total_to_fix
        
        # Apply fixes (auto-confirm in non-interactive mode)
        print(f"\n✅ Auto-confirming fix for {total_to_fix} Chase United transactions")
        
        fixed_count = 0
        
        # Fix expenses (make positive)
        for transaction in expenses_to_fix:
            transaction.amount = abs(transaction.amount)
            fixed_count += 1
        
        # Fix returns (make negative)
        for transaction in returns_to_fix:
            transaction.amount = -abs(transaction.amount)
            fixed_count += 1
        
        db.commit()
        print(f"✅ Fixed {fixed_count} Chase United transactions")
        return fixed_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return 0
    finally:
        db.close()


def verify_results():
    """Verify the results after fixing signs."""
    print("\n🔍 VERIFYING RESULTS")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Check each source
        sources = ['csv', 'capone_aug_nov_2025', 'chase_united']
        
        for source in sources:
            transactions = db.query(Transaction).filter(
                Transaction.source.ilike(f'%{source}%')
            ).all()
            
            if not transactions:
                continue
                
            positive_count = sum(1 for t in transactions if t.amount > 0)
            negative_count = sum(1 for t in transactions if t.amount < 0)
            
            print(f"\n📊 {source}:")
            print(f"  Positive: {positive_count} ({positive_count/len(transactions)*100:.1f}%)")
            print(f"  Negative: {negative_count} ({negative_count/len(transactions)*100:.1f}%)")
            
            # Show any remaining negatives that aren't returns
            if negative_count > 0:
                negatives = [t for t in transactions if t.amount < 0]
                non_returns = [t for t in negatives if 'return' not in t.description.lower()]
                
                if non_returns:
                    print(f"  ⚠️  {len(non_returns)} negative non-returns still exist")
                    for t in non_returns[:3]:
                        print(f"    {t.transaction_date} | ${t.amount:8.2f} | {t.description[:30]}")
                else:
                    print(f"  ✅ All negatives are returns (good)")
    finally:
        db.close()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix transaction signs in database")
    parser.add_argument('action', 
                       choices=['analyze', 'fix', 'verify'],
                       help='Action to perform')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be fixed without applying changes')
    
    args = parser.parse_args()
    
    if args.action == 'analyze':
        analyze_current_signs()
    
    elif args.action == 'fix':
        dry_run = args.dry_run
        
        if dry_run:
            print("🧪 DRY RUN MODE - No changes will be applied")
        
        analyze_current_signs()
        
        # Fix each source
        capone_fixed = fix_capital_one_signs(dry_run)
        chase_fixed = fix_chase_united_signs(dry_run)
        
        total_fixed = capone_fixed + chase_fixed
        
        if dry_run:
            print(f"\n📊 DRY RUN SUMMARY:")
            print(f"  Would fix {total_fixed} transactions total")
        else:
            print(f"\n🎉 SUMMARY:")
            print(f"  Fixed {total_fixed} transactions total")
            
            if total_fixed > 0:
                verify_results()
    
    elif args.action == 'verify':
        verify_results()


if __name__ == "__main__":
    main()
