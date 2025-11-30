#!/usr/bin/env python3
"""
Transaction Recategorization Script

This script uses the new YAML configuration to reassess and update categories for all
existing transactions in the database. It compares current categories with what the
new configuration rules would assign, and allows you to apply updates selectively.
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from budget_app.core.models import Transaction, SessionLocal
from budget_app.core.category_config import get_category_config


class RecategorizationAnalyzer:
    """Analyzes and manages transaction recategorization."""
    
    def __init__(self):
        self.config = get_category_config()
        self.db = SessionLocal()
        self.changes = []  # List of (transaction, old_category, new_category)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def analyze_all_transactions(self) -> Dict[str, any]:
        """Analyze all transactions and identify categorization changes."""
        print("🔍 ANALYZING ALL TRANSACTIONS FOR RECATEGORIZATION")
        print("=" * 60)
        
        all_transactions = self.db.query(Transaction).all()
        print(f"📊 Total transactions to analyze: {len(all_transactions)}")
        
        # Track statistics
        stats = {
            'total': len(all_transactions),
            'no_change': 0,
            'changes': 0,
            'by_old_category': Counter(),
            'by_new_category': Counter(),
            'change_patterns': Counter()
        }
        
        print("🔄 Processing transactions...")
        
        for i, txn in enumerate(all_transactions):
            if i % 500 == 0 and i > 0:
                print(f"   Processed {i}/{len(all_transactions)} transactions...")
            
            # Get new category based on current config
            new_category = self.config.categorize_by_keywords(txn.description)
            old_category = txn.category
            
            # Track statistics
            stats['by_old_category'][old_category] += 1
            
            if old_category != new_category:
                stats['changes'] += 1
                stats['by_new_category'][new_category] += 1
                stats['change_patterns'][f"{old_category} → {new_category}"] += 1
                
                self.changes.append((txn, old_category, new_category))
            else:
                stats['no_change'] += 1
        
        print(f"✅ Analysis complete!")
        print(f"   📈 No changes needed: {stats['no_change']}")
        print(f"   🔄 Changes identified: {stats['changes']}")
        
        return stats
    
    def show_summary_report(self, stats: Dict[str, any]) -> None:
        """Display a comprehensive summary of proposed changes."""
        print("\n" + "=" * 60)
        print("📋 RECATEGORIZATION SUMMARY REPORT")
        print("=" * 60)
        
        print(f"📊 Total Transactions: {stats['total']}")
        print(f"✅ No Change Needed: {stats['no_change']} ({stats['no_change']/stats['total']*100:.1f}%)")
        print(f"🔄 Changes Proposed: {stats['changes']} ({stats['changes']/stats['total']*100:.1f}%)")
        
        if stats['changes'] == 0:
            print("\n🎉 All transactions are already correctly categorized!")
            return
        
        print(f"\n🔍 TOP 15 CHANGE PATTERNS:")
        for pattern, count in stats['change_patterns'].most_common(15):
            print(f"   {count:4d} × {pattern}")
        
        print(f"\n📂 CATEGORIES GAINING TRANSACTIONS:")
        for category, count in stats['by_new_category'].most_common(10):
            print(f"   +{count:3d} → {category}")
        
        # Show transactions that would change FROM problem categories
        problem_categories = ['misc', 'category pending', 'other', 'uncategorized']
        problem_changes = [
            (txn, old, new) for txn, old, new in self.changes 
            if any(prob in old.lower() for prob in ['misc', 'pending', 'other', 'uncategorized'])
        ]
        
        if problem_changes:
            print(f"\n🎯 IMPROVEMENTS TO PROBLEM CATEGORIES ({len(problem_changes)} transactions):")
            problem_patterns = Counter()
            for _, old, new in problem_changes:
                problem_patterns[f"{old} → {new}"] += 1
            
            for pattern, count in problem_patterns.most_common(10):
                print(f"   {count:4d} × {pattern}")
    
    def show_detailed_changes(self, limit: int = 50, category_filter: str = None) -> None:
        """Show detailed list of proposed changes."""
        changes_to_show = self.changes
        
        if category_filter:
            changes_to_show = [
                (txn, old, new) for txn, old, new in self.changes
                if category_filter.lower() in old.lower() or category_filter.lower() in new.lower()
            ]
        
        if not changes_to_show:
            print(f"\n❌ No changes found for filter: {category_filter}")
            return
        
        print(f"\n📝 DETAILED CHANGES (showing first {min(limit, len(changes_to_show))} of {len(changes_to_show)}):")
        if category_filter:
            print(f"🔍 Filter: '{category_filter}'")
        
        print(f"{'Date':<12} {'Amount':<10} {'Old Category':<15} {'New Category':<15} {'Description'[:30]:<30}")
        print("-" * 87)
        
        for txn, old_cat, new_cat in changes_to_show[:limit]:
            desc_short = txn.description[:27] + "..." if len(txn.description) > 30 else txn.description
            amount_str = f"${txn.amount:.2f}"
            print(f"{str(txn.transaction_date):<12} {amount_str:>9} {old_cat:<15} {new_cat:<15} {desc_short:<30}")
    
    def apply_changes(self, 
                     category_filter: str = None, 
                     dry_run: bool = True,
                     auto_approve: bool = False) -> int:
        """Apply the categorization changes to the database."""
        
        changes_to_apply = self.changes
        
        if category_filter:
            changes_to_apply = [
                (txn, old, new) for txn, old, new in self.changes
                if category_filter.lower() in old.lower() or category_filter.lower() in new.lower()
            ]
        
        if not changes_to_apply:
            print(f"\n❌ No changes to apply for filter: {category_filter}")
            return 0
        
        print(f"\n🔧 {'DRY RUN: ' if dry_run else ''}APPLYING CHANGES")
        print("=" * 60)
        print(f"📊 Changes to apply: {len(changes_to_apply)}")
        
        if category_filter:
            print(f"🔍 Filter: '{category_filter}'")
        
        # Group changes by pattern for summary
        patterns = Counter()
        for _, old, new in changes_to_apply:
            patterns[f"{old} → {new}"] += 1
        
        print(f"\n📋 Change Summary:")
        for pattern, count in patterns.most_common():
            print(f"   {count:4d} × {pattern}")
        
        if not auto_approve and not dry_run:
            confirm = input(f"\n⚠️  Apply {len(changes_to_apply)} changes to database? (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Changes cancelled.")
                return 0
        
        if dry_run:
            print("\n✅ Dry run complete - no changes applied to database.")
            return len(changes_to_apply)
        
        # Apply changes to database
        applied_count = 0
        try:
            for txn, old_cat, new_cat in changes_to_apply:
                txn.category = new_cat
                applied_count += 1
            
            self.db.commit()
            print(f"\n✅ Successfully applied {applied_count} categorization changes!")
            
            # Clear the changes list since they've been applied
            if not category_filter:  # Only clear all if no filter was used
                self.changes = []
            
            return applied_count
            
        except Exception as e:
            self.db.rollback()
            print(f"\n❌ Error applying changes: {e}")
            return 0
    
    def export_changes_report(self, filename: str = None) -> str:
        """Export detailed changes to a CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recategorization_report_{timestamp}.csv"
        
        filepath = os.path.join("data", "outputs", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Transaction_ID', 'Date', 'Amount', 'Description', 
                           'Old_Category', 'New_Category', 'Source'])
            
            for txn, old_cat, new_cat in self.changes:
                writer.writerow([
                    txn.id, txn.transaction_date, txn.amount, txn.description,
                    old_cat, new_cat, txn.source
                ])
        
        print(f"📁 Changes report exported to: {filepath}")
        return filepath


def main():
    """Main function with command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Recategorize transactions using new config")
    parser.add_argument('action', 
                       choices=['analyze', 'show', 'apply', 'export'],
                       help='Action to perform')
    parser.add_argument('--filter', help='Filter by category (old or new)')
    parser.add_argument('--limit', type=int, default=50, help='Limit for detailed view')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    parser.add_argument('--auto-approve', action='store_true', help='Apply without confirmation')
    parser.add_argument('--output', help='Output filename for export')
    
    args = parser.parse_args()
    
    with RecategorizationAnalyzer() as analyzer:
        
        if args.action == 'analyze':
            stats = analyzer.analyze_all_transactions()
            analyzer.show_summary_report(stats)
            
            if stats['changes'] > 0:
                print(f"\n💡 Next steps:")
                print(f"   👀 View details: python {__file__} show --filter misc")
                print(f"   🧪 Test changes: python {__file__} apply --dry-run")
                print(f"   ✅ Apply changes: python {__file__} apply")
        
        elif args.action == 'show':
            if not analyzer.changes:
                # Need to analyze first
                analyzer.analyze_all_transactions()
            
            analyzer.show_detailed_changes(args.limit, args.filter)
        
        elif args.action == 'apply':
            if not analyzer.changes:
                # Need to analyze first
                analyzer.analyze_all_transactions()
            
            applied = analyzer.apply_changes(
                category_filter=args.filter,
                dry_run=args.dry_run,
                auto_approve=args.auto_approve
            )
            
            if applied > 0 and not args.dry_run:
                print(f"\n🎉 Recategorization complete!")
                print(f"📊 Applied {applied} changes")
        
        elif args.action == 'export':
            if not analyzer.changes:
                analyzer.analyze_all_transactions()
            
            analyzer.export_changes_report(args.output)


def interactive_mode():
    """Interactive mode for recategorization."""
    print("🎯 INTERACTIVE TRANSACTION RECATEGORIZATION")
    print("Available commands:")
    print("  analyze - Analyze all transactions for changes")
    print("  show [category] - Show detailed changes (optional filter)")
    print("  apply [category] - Apply changes (optional filter)")
    print("  test - Dry run application")
    print("  export - Export changes report")
    print("  quit - Exit")
    print()
    
    with RecategorizationAnalyzer() as analyzer:
        analyzed = False
        
        while True:
            try:
                command = input("📝 Enter command: ").strip().split()
                if not command:
                    continue
                
                if command[0] == 'quit':
                    break
                elif command[0] == 'analyze':
                    stats = analyzer.analyze_all_transactions()
                    analyzer.show_summary_report(stats)
                    analyzed = True
                elif command[0] == 'show':
                    if not analyzed:
                        print("❌ Run 'analyze' first")
                        continue
                    filter_cat = command[1] if len(command) > 1 else None
                    analyzer.show_detailed_changes(50, filter_cat)
                elif command[0] == 'apply':
                    if not analyzed:
                        print("❌ Run 'analyze' first")
                        continue
                    filter_cat = command[1] if len(command) > 1 else None
                    analyzer.apply_changes(filter_cat, dry_run=False)
                elif command[0] == 'test':
                    if not analyzed:
                        print("❌ Run 'analyze' first")
                        continue
                    analyzer.apply_changes(dry_run=True)
                elif command[0] == 'export':
                    if not analyzed:
                        print("❌ Run 'analyze' first")
                        continue
                    analyzer.export_changes_report()
                else:
                    print("❌ Unknown command")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break


if __name__ == "__main__":
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        main()
