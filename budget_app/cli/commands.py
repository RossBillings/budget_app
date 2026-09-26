#!/usr/bin/env python3
"""
Budget App - A command-line tool for tracking and analyzing expenses.

This module provides a CLI interface to the budget application,
allowing users to import transactions, view expenses, and generate reports.
"""
import argparse
import calendar
import logging
import os
import sys
from datetime import date, datetime
from typing import List, Optional, Tuple

from prettytable import PrettyTable
import matplotlib.pyplot as plt

from ..core.categorizer import load_category_rules
from ..core.database import (
    INCOME_CATEGORY,
    get_aggregated_expenses,
    get_category_monthly_totals,
    get_transactions,
    delete_transaction,
    import_transactions_from_csv,
    recategorize_transactions,
    get_categories,
    get_transaction_years,
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
    import_parser.add_argument(
        '--config',
        type=str,
        help='Path to categories.yaml (default: ./categories.yaml or CATEGORIES_CONFIG)'
    )

    recategorize_parser = subparsers.add_parser(
        'recategorize',
        help='Re-apply categories.yaml rules to all transactions in the database',
    )
    recategorize_parser.add_argument(
        '--config',
        type=str,
        help='Path to categories.yaml (default: ./categories.yaml or CATEGORIES_CONFIG)',
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate expense reports')
    report_parser.add_argument(
        '--category',
        type=str,
        help='Category to filter by (omit for all categories)'
    )
    report_parser.add_argument(
        '--year',
        type=int,
        help='Filter to a calendar year (e.g. 2026)'
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
    
    # Summary command
    summary_parser = subparsers.add_parser(
        'summary',
        help='Category totals grouped by month',
    )
    summary_parser.add_argument(
        '--month',
        type=str,
        metavar='YYYY-MM',
        help='Single calendar month',
    )
    summary_parser.add_argument(
        '--start-month',
        type=str,
        metavar='YYYY-MM',
        help='First month in range (use with --end-month)',
    )
    summary_parser.add_argument(
        '--end-month',
        type=str,
        metavar='YYYY-MM',
        help='Last month in range (use with --start-month)',
    )
    summary_parser.add_argument(
        '--year',
        type=int,
        action='append',
        metavar='YEAR',
        help='Calendar year (repeat for multiple years)',
    )
    summary_parser.add_argument(
        '--start-date',
        type=str,
        help='Start date (YYYY-MM-DD)',
    )
    summary_parser.add_argument(
        '--end-date',
        type=str,
        help='End date (YYYY-MM-DD)',
    )
    summary_parser.add_argument(
        '--category',
        type=str,
        help='Filter to one category',
    )
    summary_parser.add_argument(
        '--pivot',
        action='store_true',
        help='Show categories as rows and months as columns',
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


def _parse_yyyy_mm(value: str) -> Tuple[int, int]:
    """Parse YYYY-MM into (year, month)."""
    try:
        year_str, month_str = value.strip().split('-', 1)
        year, month = int(year_str), int(month_str)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Expected YYYY-MM, got {value!r}") from exc
    if month < 1 or month > 12:
        raise ValueError(f"Month must be 1-12, got {value!r}")
    return year, month


def _month_date_bounds(year: int, month: int) -> Tuple[str, str]:
    """Return inclusive start/end dates for a calendar month."""
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    return start.isoformat(), end.isoformat()


def resolve_summary_date_range(args: argparse.Namespace) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve summary date filters to (start_date, end_date) strings.

    Mutually exclusive groups: --month | --start-month/--end-month |
    --year | --start-date/--end-date.
    """
    month = getattr(args, 'month', None)
    start_month = getattr(args, 'start_month', None)
    end_month = getattr(args, 'end_month', None)
    years = getattr(args, 'year', None) or []
    start_date = getattr(args, 'start_date', None)
    end_date = getattr(args, 'end_date', None)

    groups = [
        bool(month),
        bool(start_month or end_month),
        bool(years),
        bool(start_date or end_date),
    ]
    if sum(groups) > 1:
        raise ValueError(
            "Use only one of: --month, --start-month/--end-month, "
            "--year, or --start-date/--end-date"
        )

    if month:
        year, mon = _parse_yyyy_mm(month)
        return _month_date_bounds(year, mon)

    if start_month or end_month:
        if not start_month or not end_month:
            raise ValueError("--start-month and --end-month must be used together")
        sy, sm = _parse_yyyy_mm(start_month)
        ey, em = _parse_yyyy_mm(end_month)
        start, _ = _month_date_bounds(sy, sm)
        _, end = _month_date_bounds(ey, em)
        if (ey, em) < (sy, sm):
            raise ValueError("--end-month must not be before --start-month")
        return start, end

    if years:
        years_sorted = sorted(set(years))
        return f"{years_sorted[0]}-01-01", f"{years_sorted[-1]}-12-31"

    return start_date, end_date


def _format_category_total(category: str, total: float) -> str:
    """Format amount for display; income is shown as positive money in."""
    if category.lower() == INCOME_CATEGORY:
        return f"${abs(total):.2f}"
    return f"${total:.2f}"


def _month_money_flow(rows_for_month: List[dict]) -> Tuple[float, float, float]:
    """
    Compute money in, money out, and net for one month.

    Income is stored as negative amounts; spending is positive.
    """
    income_total = sum(
        r['total'] for r in rows_for_month
        if r['category'].lower() == INCOME_CATEGORY
    )
    money_in = abs(income_total)
    money_out = sum(
        r['total'] for r in rows_for_month
        if r['category'].lower() != INCOME_CATEGORY
    )
    return money_in, money_out, money_in - money_out


def _summary_row_sort_key(row: dict) -> Tuple[int, str]:
    """Income first, then other categories alphabetically."""
    if row['category'].lower() == INCOME_CATEGORY:
        return (0, row['category'])
    return (1, row['category'])


def print_category_monthly_table(rows: List[dict], pivot: bool = False) -> None:
    """Print category totals by month."""
    if not rows:
        print("No expense data found.")
        return

    if not pivot:
        print("\nCategory totals by month (transfers excluded):")
        months = sorted({row['month'] for row in rows})
        for month in months:
            month_rows = sorted(
                [r for r in rows if r['month'] == month],
                key=_summary_row_sort_key,
            )
            table = PrettyTable()
            table.field_names = ["Category", "Total"]
            table.align["Total"] = "r"
            print(month)
            for row in month_rows:
                table.add_row([
                    row['category'],
                    _format_category_total(row['category'], row['total']),
                ])
            money_in, money_out, net = _month_money_flow(month_rows)
            table.add_row(["Money in", f"${money_in:.2f}"])
            table.add_row(["Money out", f"${money_out:.2f}"])
            table.add_row(["Net", f"${net:.2f}"])
            print(table)
            print()
        return

    months = sorted({row['month'] for row in rows})
    categories = sorted(
        {row['category'] for row in rows},
        key=lambda c: (0, c) if c.lower() == INCOME_CATEGORY else (1, c),
    )
    lookup = {(r['month'], r['category']): r['total'] for r in rows}

    table = PrettyTable()
    table.field_names = ["Category"] + months + ["Total"]
    table.align.update({m: "r" for m in months})
    table.align["Total"] = "r"

    for category in categories:
        values = [lookup.get((m, category), 0.0) for m in months]
        if category.lower() == INCOME_CATEGORY:
            display_values = [abs(v) for v in values]
            row_total = sum(abs(v) for v in values)
        else:
            display_values = values
            row_total = sum(values)
        table.add_row(
            [category]
            + [f"${v:.2f}" for v in display_values]
            + [f"${row_total:.2f}"]
        )

    money_in_by_month = []
    money_out_by_month = []
    net_by_month = []
    for month in months:
        month_rows = [r for r in rows if r['month'] == month]
        money_in, money_out, net = _month_money_flow(month_rows)
        money_in_by_month.append(money_in)
        money_out_by_month.append(money_out)
        net_by_month.append(net)

    table.add_row(
        ["Money in"]
        + [f"${v:.2f}" for v in money_in_by_month]
        + [f"${sum(money_in_by_month):.2f}"]
    )
    table.add_row(
        ["Money out"]
        + [f"${v:.2f}" for v in money_out_by_month]
        + [f"${sum(money_out_by_month):.2f}"]
    )
    table.add_row(
        ["Net"]
        + [f"${v:.2f}" for v in net_by_month]
        + [f"${sum(net_by_month):.2f}"]
    )

    print("\nCategory totals by month (pivot, transfers excluded):")
    print(table)


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
            rules = load_category_rules(args.config) if args.config else None
            print(f"Importing transactions from {args.file}...")
            result = import_transactions_from_csv(
                file_path=args.file,
                default_category=args.category,
                source=args.source,
                rules=rules,
            )
            print(f"\nImport complete:")
            print(f"  - Inserted: {result['inserted']}")
            print(f"  - Duplicates skipped: {result['duplicates']}")
            print(f"  - Excluded by rules: {result.get('excluded', 0)}")
            print(f"  - Skipped (invalid): {result['skipped']}")
            print(f"  - Errors: {result['errors']}")

        elif args.command == 'recategorize':
            rules = load_category_rules(args.config) if args.config else None
            print("Recategorizing transactions using categories.yaml...")
            result = recategorize_transactions(rules=rules)
            print(f"\nRecategorize complete:")
            print(f"  - Updated: {result['updated']}")
            print(f"  - Removed (excluded/duplicate): {result['excluded']}")
            print(f"  - Errors: {result['errors']}")
            
        elif args.command == 'report':
            if args.year and (args.start_date or args.end_date):
                print("Error: use either --year or --start-date/--end-date, not both.")
                sys.exit(1)

            start_date = args.start_date
            end_date = args.end_date
            if args.year:
                start_date = f"{args.year}-01-01"
                end_date = f"{args.year}-12-31"

            years_in_db = get_transaction_years()
            if years_in_db:
                print(f"Database contains transactions for: {', '.join(str(y) for y in years_in_db)}")

            filters = []
            if args.category:
                filters.append(f"category={args.category}")
            if args.year:
                filters.append(f"year={args.year}")
            elif start_date or end_date:
                filters.append(f"dates={start_date or '...'} to {end_date or '...'}")
            if args.keyword:
                filters.append(f"keyword={args.keyword!r}")
            if filters:
                print(f"Report filters: {', '.join(filters)}")
            else:
                print("Report filters: none (all categories and dates)")

            aggregated = get_aggregated_expenses(
                category=args.category,
                start_date=start_date,
                end_date=end_date,
            )

            transactions, total = get_transactions(
                category=args.category,
                keyword=args.keyword,
                start_date=start_date,
                end_date=end_date,
                sort_by=args.sort_by,
                order=args.order,
                limit=args.limit,
            )

            print_aggregated_table(aggregated)
            print_transactions(transactions, total, limit=args.limit)
            
            # Generate plot if requested
            if args.output or not args.keyword:
                plot_expenses(aggregated, output_file=args.output)
                
        elif args.command == 'summary':
            try:
                start_date, end_date = resolve_summary_date_range(args)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

            years_in_db = get_transaction_years()
            if years_in_db:
                print(
                    f"Database contains transactions for: "
                    f"{', '.join(str(y) for y in years_in_db)}"
                )

            filters = []
            if args.category:
                filters.append(f"category={args.category}")
            if getattr(args, 'month', None):
                filters.append(f"month={args.month}")
            elif getattr(args, 'start_month', None):
                filters.append(
                    f"months={args.start_month} to {args.end_month}"
                )
            elif getattr(args, 'year', None):
                filters.append(f"years={','.join(str(y) for y in sorted(set(args.year)))}")
            elif start_date or end_date:
                filters.append(f"dates={start_date or '...'} to {end_date or '...'}")
            if filters:
                print(f"Summary filters: {', '.join(filters)}")
            else:
                print("Summary filters: none (all categories and dates)")

            rows = get_category_monthly_totals(
                category=args.category,
                start_date=start_date,
                end_date=end_date,
            )
            print_category_monthly_table(rows, pivot=args.pivot)

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
