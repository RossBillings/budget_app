#!/usr/bin/env python3
"""
Budget Report Generator

Generates comprehensive budget analysis reports for specified date ranges.
This replaces the legacy 0-budget_app.py orchestrator functionality.
"""

import sys
import os
import argparse
from datetime import datetime, date
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# Add parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from budget_app.core.models import Transaction, SessionLocal
    from prettytable import PrettyTable
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the budget_app root directory")
    sys.exit(1)


def get_transactions_in_range(start_year: int, start_month: int, end_year: int, end_month: int) -> List[Transaction]:
    """Get all transactions within the specified date range."""
    db = SessionLocal()
    try:
        start_date = date(start_year, start_month, 1)
        
        # Calculate end date (last day of end month)
        if end_month == 12:
            end_date = date(end_year + 1, 1, 1)
        else:
            end_date = date(end_year, end_month + 1, 1)
        
        transactions = db.query(Transaction).filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < end_date
        ).order_by(Transaction.transaction_date).all()
        
        return transactions
    finally:
        db.close()


def analyze_expenses_by_category(transactions: List[Transaction]) -> Dict[str, float]:
    """Analyze expenses by category."""
    expenses_by_category = defaultdict(float)
    
    for transaction in transactions:
        # Only include positive amounts (expenses) in analysis
        if transaction.amount > 0:
            expenses_by_category[transaction.category] += transaction.amount
    
    return dict(expenses_by_category)


def analyze_monthly_breakdown(transactions: List[Transaction]) -> Dict[Tuple[int, int], float]:
    """Analyze expenses by month."""
    monthly_expenses = defaultdict(float)
    
    for transaction in transactions:
        if transaction.amount > 0:  # Only expenses
            month_key = (transaction.transaction_date.year, transaction.transaction_date.month)
            monthly_expenses[month_key] += transaction.amount
    
    return dict(monthly_expenses)


def print_summary_report(transactions: List[Transaction], start_year: int, start_month: int, 
                        end_year: int, end_month: int):
    """Print a comprehensive summary report."""
    print("=" * 80)
    print(f"📊 BUDGET ANALYSIS REPORT")
    print("=" * 80)
    print(f"📅 Period: {start_year}-{start_month:02d} to {end_year}-{end_month:02d}")
    print(f"📈 Total Transactions: {len(transactions)}")
    
    # Calculate totals
    total_expenses = sum(t.amount for t in transactions if t.amount > 0)
    total_refunds = sum(abs(t.amount) for t in transactions if t.amount < 0)
    net_spending = total_expenses - total_refunds
    
    print(f"💰 Total Expenses: ${total_expenses:,.2f}")
    print(f"↩️  Total Refunds: ${total_refunds:,.2f}")
    print(f"📊 Net Spending: ${net_spending:,.2f}")
    print()
    
    # Category breakdown
    expenses_by_category = analyze_expenses_by_category(transactions)
    
    print("📂 EXPENSES BY CATEGORY")
    print("-" * 50)
    
    table = PrettyTable(['Category', 'Amount', 'Percentage'])
    table.align['Category'] = 'l'
    table.align['Amount'] = 'r'
    table.align['Percentage'] = 'r'
    
    sorted_categories = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
    
    for category, amount in sorted_categories:
        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
        table.add_row([category.title(), f"${amount:,.2f}", f"{percentage:.1f}%"])
    
    print(table)
    print()
    
    # Monthly breakdown if spanning multiple months
    monthly_expenses = analyze_monthly_breakdown(transactions)
    if len(monthly_expenses) > 1:
        print("📅 MONTHLY BREAKDOWN")
        print("-" * 30)
        
        monthly_table = PrettyTable(['Month', 'Expenses'])
        monthly_table.align['Month'] = 'l'
        monthly_table.align['Expenses'] = 'r'
        
        sorted_months = sorted(monthly_expenses.items())
        for (year, month), amount in sorted_months:
            month_str = f"{year}-{month:02d}"
            monthly_table.add_row([month_str, f"${amount:,.2f}"])
        
        print(monthly_table)
        print()
    
    # Top transactions
    print("💳 TOP 10 LARGEST TRANSACTIONS")
    print("-" * 50)
    
    expense_transactions = [t for t in transactions if t.amount > 0]
    top_transactions = sorted(expense_transactions, key=lambda x: x.amount, reverse=True)[:10]
    
    trans_table = PrettyTable(['Date', 'Description', 'Amount', 'Category'])
    trans_table.align['Description'] = 'l'
    trans_table.align['Amount'] = 'r'
    
    for transaction in top_transactions:
        desc = transaction.description[:30] + "..." if len(transaction.description) > 33 else transaction.description
        trans_table.add_row([
            transaction.transaction_date.strftime('%Y-%m-%d'),
            desc,
            f"${transaction.amount:.2f}",
            transaction.category
        ])
    
    print(trans_table)


def print_category_detail(transactions: List[Transaction], category: str):
    """Print detailed analysis for a specific category."""
    category_transactions = [t for t in transactions if t.category.lower() == category.lower()]
    
    if not category_transactions:
        print(f"❌ No transactions found for category: {category}")
        return
    
    print("=" * 80)
    print(f"📊 DETAILED ANALYSIS: {category.upper()}")
    print("=" * 80)
    
    # Category totals
    expenses = [t for t in category_transactions if t.amount > 0]
    refunds = [t for t in category_transactions if t.amount < 0]
    
    total_spent = sum(t.amount for t in expenses)
    total_refunded = sum(abs(t.amount) for t in refunds)
    
    print(f"💰 Total Spent: ${total_spent:.2f}")
    print(f"↩️  Total Refunded: ${total_refunded:.2f}")
    print(f"📊 Net Spending: ${total_spent - total_refunded:.2f}")
    print(f"📈 Transaction Count: {len(category_transactions)}")
    print()
    
    # Most frequent merchants/descriptions
    descriptions = Counter(t.description for t in expenses)
    
    print("🏪 TOP MERCHANTS/DESCRIPTIONS")
    print("-" * 40)
    
    desc_table = PrettyTable(['Description', 'Count', 'Total'])
    desc_table.align['Description'] = 'l'
    
    for desc, count in descriptions.most_common(10):
        desc_total = sum(t.amount for t in expenses if t.description == desc)
        desc_table.add_row([desc[:35], count, f"${desc_total:.2f}"])
    
    print(desc_table)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive budget analysis reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze full year 2025
  python scripts/budget_report.py --start_year 2025 --start_month 1 --end_year 2025 --end_month 12
  
  # Analyze specific months
  python scripts/budget_report.py --start_year 2025 --start_month 8 --end_year 2025 --end_month 11
  
  # Focus on specific category
  python scripts/budget_report.py --start_year 2025 --start_month 1 --end_year 2025 --end_month 11 --category groceries
        """
    )
    
    parser.add_argument('--start_year', type=int, required=True, help='Starting year')
    parser.add_argument('--start_month', type=int, required=True, help='Starting month (1-12)')
    parser.add_argument('--end_year', type=int, required=True, help='Ending year')
    parser.add_argument('--end_month', type=int, required=True, help='Ending month (1-12)')
    parser.add_argument('--category', type=str, help='Focus on specific category')
    
    args = parser.parse_args()
    
    # Validate date inputs
    if not (1 <= args.start_month <= 12):
        print("❌ Error: start_month must be between 1 and 12")
        sys.exit(1)
    
    if not (1 <= args.end_month <= 12):
        print("❌ Error: end_month must be between 1 and 12")
        sys.exit(1)
    
    if (args.end_year, args.end_month) < (args.start_year, args.start_month):
        print("❌ Error: End date must be after start date")
        sys.exit(1)
    
    # Get transactions
    print(f"📊 Loading transactions from {args.start_year}-{args.start_month:02d} to {args.end_year}-{args.end_month:02d}...")
    
    transactions = get_transactions_in_range(
        args.start_year, args.start_month,
        args.end_year, args.end_month
    )
    
    if not transactions:
        print("❌ No transactions found for the specified date range")
        sys.exit(1)
    
    # Generate report
    if args.category:
        print_category_detail(transactions, args.category)
    else:
        print_summary_report(transactions, args.start_year, args.start_month, 
                           args.end_year, args.end_month)


if __name__ == "__main__":
    main()
