#!/usr/bin/env python3
"""
Budget App - A command-line tool for tracking and analyzing expenses.

This module provides a CLI interface to the budget application,
allowing users to import transactions, view expenses, and generate reports.
"""
import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional, Tuple

from prettytable import PrettyTable
import matplotlib.pyplot as plt

from ..core.database import (
    get_aggregated_expenses,
    get_transactions,
    delete_transaction,
    import_transactions_from_csv,
    get_categories,
    DatabaseError,
    DuplicateEntryError,
    ValidationError,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Budget App - Track and analyze expenses")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import transactions from CSV')
    import_parser.add_argument(
        'file',
        type=str,
        help='Path to the CSV file to import'
    )
    import_parser.add_argument(
        '--category',
        type=str,
        default='misc',
        help='Default category for transactions (default: misc)'
    )
    import_parser.add_argument(
        '--source',
        type=str,
        default='csv',
        help='Source identifier for the transactions (default: csv)'
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate expense reports')
    report_parser.add_argument(
        '--category',
        type=str,
        default='misc',
        help='Category to filter by (default: misc)'
    )
    report_parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD)'
    )
    report_parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD)'
    )
    report_parser.add_argument(
        '--keyword',
        type=str,
        help='Filter transactions by keyword in description'
    )
    report_parser.add_argument(
        '--sort-by',
        type=str,
        choices=['date', 'amount', 'description'],
        default='date',
        help='Field to sort by (default: date)'
    )
    report_parser.add_argument(
        '--order',
        type=str,
        choices=['asc', 'desc'],
        default='asc',
        help='Sort order (default: asc)'
    )
    report_parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of transactions to show'
    )
    report_parser.add_argument(
        '--output',
        type=str,
        help='Output file for the chart (if not specified, shows interactive plot)'
    )
    
    # Categories command
    subparsers.add_parser('categories', help='List all categories with totals')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a transaction')
    delete_parser.add_argument('transaction_id', help='ID of the transaction to delete')
    
    # Set default command to report if no subcommand is provided
    if len(sys.argv) == 1:
        sys.argv.append('--help')
    
    return parser.parse_args(args)


def print_aggregated_table(aggregated: List[dict]) -> None:
    """Print aggregated expense data in a formatted table."""
    if not aggregated:
        print("No expense data found.")
        return
    
    table = PrettyTable()
    table.field_names = ["Month", "Total"]
    table.align["Total"] = "r"
    
    for row in aggregated:
        table.add_row([row['month'], f"${row['total']:.2f}"])
    
    print("\nAggregated Expenses by Month:")
    print(table)


def print_transactions(transactions: List[dict], total: int, limit: int = None) -> None:
    """Print transaction data in a formatted table."""
    if not transactions:
        print("No transactions found.")
        return
    
    table = PrettyTable()
    table.field_names = ["Date", "Description", "Amount", "Category", "ID"]
    table.align["Amount"] = "r"
    
    for txn in transactions:
        table.add_row([
            txn.transaction_date.strftime("%Y-%m-%d"),
            txn.description[:50] + ('...' if len(txn.description) > 50 else ''),
            f"${txn.amount:.2f}",
            txn.category,
            txn.id[:8]  # Show first 8 chars of UUID
        ])
    
    print(f"\nTransactions (showing {len(transactions)} of {total}):")
    print(table)


def plot_expenses(aggregated: List[dict], output_file: str = None) -> None:
    """Generate a bar chart of aggregated expenses."""
    if not aggregated:
        print("No data to plot.")
        return
    
    months = [row['month'] for row in aggregated]
    amounts = [row['total'] for row in aggregated]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(months, amounts, color='skyblue')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f'${height:.2f}',
            ha='center',
            va='bottom',
            fontsize=9
        )
    
    plt.title('Monthly Expenses')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"Chart saved to {output_file}")
    else:
        plt.show()


def print_categories() -> None:
    """Print all categories with their total amounts."""
    categories = get_categories()
    
    if not categories:
        print("No categories found.")
        return
    
    table = PrettyTable()
    table.field_names = ["Category", "Total"]
    table.align["Total"] = "r"
    
    for cat in categories:
        table.add_row([cat['category'], f"${cat['total']:.2f}"])
    
    print("\nCategories by Total Expense:")
    print(table)


def main() -> None:
    """Main entry point for the budget app CLI."""
    args = parse_args()
    
    try:
        if args.command == 'import':
            print(f"Importing transactions from {args.file}...")
            result = import_transactions_from_csv(
                file_path=args.file,
                default_category=args.category,
                source=args.source
            )
            print(f"\nImport complete:")
            print(f"  - Inserted: {result['inserted']}")
            print(f"  - Duplicates skipped: {result['duplicates']}")
            print(f"  - Errors: {result['errors']}")
            
        elif args.command == 'report':
            # Get aggregated data
            aggregated = get_aggregated_expenses(
                category=args.category,
                start_date=args.start_date,
                end_date=args.end_date
            )
            
            # Get transactions
            transactions, total = get_transactions(
                category=args.category,
                keyword=args.keyword,
                start_date=args.start_date,
                end_date=args.end_date,
                sort_by=args.sort_by,
                order=args.order,
                limit=args.limit
            )
            
            # Display results
            print_aggregated_table(aggregated)
            print_transactions(transactions, total, limit=args.limit)
            
            # Generate plot if requested
            if args.output or not args.keyword:
                plot_expenses(aggregated, output_file=args.output)
                
        elif args.command == 'categories':
            print_categories()
            
        elif args.command == 'delete':
            if delete_transaction(args.transaction_id):
                print(f"Transaction {args.transaction_id} deleted successfully.")
            else:
                print(f"Transaction {args.transaction_id} not found.")
                
        else:
            print("No command specified. Use --help for usage information.")
            
    except (DatabaseError, FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred")
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
