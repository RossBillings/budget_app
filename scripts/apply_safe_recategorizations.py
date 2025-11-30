#!/usr/bin/env python3
"""
Apply Safe Recategorizations

This script applies only the safest, most obvious recategorization improvements
to avoid accidentally miscategorizing transactions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.recategorize_all_transactions import RecategorizationAnalyzer


def apply_safe_improvements():
    """Apply only the safest category improvements."""
    
    print("🎯 APPLYING SAFE CATEGORY IMPROVEMENTS")
    print("=" * 50)
    
    with RecategorizationAnalyzer() as analyzer:
        # Analyze all transactions first
        print("📊 Analyzing transactions...")
        stats = analyzer.analyze_all_transactions()
        
        if stats['changes'] == 0:
            print("✅ No improvements needed!")
            return
        
        print(f"🔄 Found {stats['changes']} potential improvements")
        
        # Define safe improvement patterns
        safe_patterns = [
            # Moving things OUT of problem categories
            ('misc', 'transfer', 'Transfer, Payment, Zelle'),
            ('misc', 'shopping', 'Kohl\'s, Party City, Old Navy'),
            ('misc', 'health', 'Walgreens, CVS'),
            ('misc', 'utilities', 'Verizon, AT&T'),
            ('category pending', 'transfer', 'Transfer patterns'),
            ('category pending', 'utilities', 'Phone/Internet bills'),
            
            # Cleaning up external categories  
            ('merchandise', 'target', 'General merchandise to Target'),
            ('merchandise', 'groceries', 'Food merchandise to Groceries'),
            ('life insurance', 'insurance', 'Standardize insurance category'),
            ('financial', 'insurance', 'Financial services to Insurance'),
        ]
        
        applied_total = 0
        
        print("\n🔧 Applying safe improvements:")
        
        for old_cat, new_cat, description in safe_patterns:
            # Count how many would change
            relevant_changes = [
                (txn, old, new) for txn, old, new in analyzer.changes
                if old == old_cat and new == new_cat
            ]
            
            if relevant_changes:
                print(f"\n📋 {description}:")
                print(f"   {len(relevant_changes)} transactions: {old_cat} → {new_cat}")
                
                # Show a few examples
                for txn, old, new in relevant_changes[:3]:
                    print(f"   • {txn.description[:40]}")
                
                if len(relevant_changes) > 3:
                    print(f"   • ... and {len(relevant_changes) - 3} more")
                
                # Ask for confirmation
                confirm = input(f"   Apply these {len(relevant_changes)} changes? (y/N): ")
                
                if confirm.lower() == 'y':
                    # Apply just these changes
                    try:
                        for txn, old, new in relevant_changes:
                            txn.category = new
                        
                        analyzer.db.commit()
                        applied_total += len(relevant_changes)
                        print(f"   ✅ Applied {len(relevant_changes)} changes")
                        
                        # Remove applied changes from the list
                        analyzer.changes = [
                            (txn, old, new) for txn, old, new in analyzer.changes
                            if (txn, old, new) not in relevant_changes
                        ]
                        
                    except Exception as e:
                        analyzer.db.rollback()
                        print(f"   ❌ Error: {e}")
                else:
                    print(f"   ⏭️  Skipped")
        
        print(f"\n🎉 SUMMARY")
        print(f"✅ Applied {applied_total} categorization improvements")
        
        remaining_changes = len(analyzer.changes)
        if remaining_changes > 0:
            print(f"📋 {remaining_changes} other changes still available")
            print(f"💡 Run full analysis: python scripts/recategorize_all_transactions.py analyze")


if __name__ == "__main__":
    apply_safe_improvements()
