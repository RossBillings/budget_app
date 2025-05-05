#!/usr/bin/env python3
import argparse
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from prettytable import PrettyTable

def parse_args():
    parser = argparse.ArgumentParser(description="Miscellaneous Expense Analysis")
    parser.add_argument("--input", type=str, default=os.path.join("Expense_Inputs", "cleaned_expenses2025.csv"),
                        help="Path to the input CSV file (default: Expense_Inputs/cleaned_expenses2025.csv)")
    parser.add_argument("--sort_by", type=str, choices=["date", "value"], default="date",
                        help="Sort the chart by 'date' (YYYY-MM) or by aggregated 'value' (default: date)")
    parser.add_argument("--order", type=str, choices=["asc", "desc"], default="asc",
                        help="Sorting order: ascending or descending (default: asc)")
    parser.add_argument("--output", type=str, default="",
                        help="If provided, the chart will be saved to this file instead of being shown")
    parser.add_argument("--list_transactions", action="store_true", help="Print all individual transactions sorted per input")
    parser.add_argument("--category", type=str, default="misc", help="The category to analyze (default: misc)")
    parser.add_argument("--keyword", type=str, default="", help="Filter transactions by keyword in description")
    parser.add_argument("--start_date", type=str, default="", help="Start date inclusive filter (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default="", help="End date inclusive filter (YYYY-MM-DD)")
    return parser.parse_args()

def aggregate_misc_expenses(input_file):
    """
    Reads the input CSV and aggregates the amounts for the specified category,
    grouping by month (formatted as 'YYYY-MM').
    """
    aggregated = {}
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Category"].strip().lower() == args_category:
                try:
                    dt = datetime.strptime(row["Transaction Date"].strip(), "%Y-%m-%d")
                except ValueError:
                    print(f"Skipping row with invalid date format: {row}")
                    continue
                try:
                    amount = float(row["Amount"].strip())
                except ValueError:
                    print(f"Skipping row with invalid amount: {row}")
                    continue
                key = f"{dt.year}-{dt.month:02d}"
                aggregated[key] = aggregated.get(key, 0) + amount
    return aggregated

def print_aggregated_table(aggregated, sort_by="date", order="asc"):
    """Prints the aggregated expense data in a PrettyTable."""
    items = list(aggregated.items())
    if sort_by == "date":
        items.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m"), reverse=(order=="desc"))
    elif sort_by == "value":
        items.sort(key=lambda x: x[1], reverse=(order=="desc"))

    table = PrettyTable()
    table.field_names = ["Month (YYYY-MM)", "Total Expense"]
    for month, total in items:
        table.add_row([month, f"${total:.2f}"])
    print(table)

def get_misc_transactions(input_file):
    """Reads the input CSV and returns a list of transactions (dicts) for the specified category."""
    transactions = []
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Category"].strip().lower() == args_category:
                try:
                    dt = datetime.strptime(row["Transaction Date"].strip(), "%Y-%m-%d")
                except ValueError:
                    print(f"Skipping row with invalid date format: {row}")
                    continue
                try:
                    amount = float(row["Amount"].strip())
                except ValueError:
                    print(f"Skipping row with invalid amount: {row}")
                    continue
                transaction = {
                    "Transaction Date": dt,
                    "Description": row["Description"].strip(),
                    "Amount": amount
                }
                transactions.append(transaction)
    return transactions

def print_misc_transactions(transactions, sort_by="date", order="asc"):
    """Prints individual transactions in a PrettyTable, sorted by the specified key (date or value)."""
    if sort_by == "date":
        transactions.sort(key=lambda x: x["Transaction Date"], reverse=(order=="desc"))
    elif sort_by == "value":
        transactions.sort(key=lambda x: x["Amount"], reverse=(order=="desc"))

    table = PrettyTable()
    table.field_names = ["Transaction Date", "Description", "Amount"]
    for txn in transactions:
        date_str = txn["Transaction Date"].strftime("%Y-%m-%d")
        table.add_row([date_str, txn["Description"], f"${txn['Amount']:.2f}"])
    print("\nIndividual Transactions:")
    print(table)

def plot_misc_expenses(aggregated, sort_by="date", order="asc", output_file=""):
    """
    Plots a bar chart of aggregated expenses.
    Allows sorting by date (natural order) or by aggregated value.
    """
    items = list(aggregated.items())
    if sort_by == "date":
        items.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m"), reverse=(order=="desc"))
    elif sort_by == "value":
        items.sort(key=lambda x: x[1], reverse=(order=="desc"))

    months = [item[0] for item in items]
    values = [item[1] for item in items]

    plt.figure(figsize=(10,6))
    bars = plt.bar(months, values, color='skyblue')
    plt.xlabel("Month (YYYY-MM)")
    plt.ylabel("Total Expense")
    plt.title("Expenses Per Month")
    plt.xticks(rotation=45)

    # Annotate bars with their values.
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.2f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), # 3 points vertical offset
                     textcoords="offset points",
                     ha='center', va='bottom')

    plt.tight_layout()
    if output_file:
        plt.savefig(output_file)
        print(f"Chart saved to {output_file}")
    else:
        plt.show()

def filter_transactions(input_file, keyword, start_date_str, end_date_str):
    """Returns list of transactions matching keyword and date range."""
    transactions = []
    # parse date bounds
    start = None
    end = None
    if start_date_str:
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid start_date: {start_date_str}"); return []
    if end_date_str:
        try:
            end = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Invalid end_date: {end_date_str}"); return []
    with open(input_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row.get("Description","").strip()
            if keyword.lower() not in desc.lower():
                continue
            # parse date
            try:
                dt = datetime.strptime(row.get("Transaction Date","").strip(), "%Y-%m-%d")
            except ValueError:
                continue
            if start and dt < start:
                continue
            if end and dt > end:
                continue
            # parse amount
            try:
                amt = float(row.get("Amount","").strip())
            except ValueError:
                continue
            transactions.append({"Transaction Date": dt, "Description": desc, "Amount": amt})
    return transactions

def main():
    global args_category
    args = parse_args()
    args_category = args.category.strip().lower()
    # filter by keyword or date range overrides category
    if args.keyword or args.start_date or args.end_date:
        txns = filter_transactions(args.input, args.keyword, args.start_date, args.end_date)
        if not txns:
            print(f"No transactions found for keyword '{args.keyword}' or date range.")
            return
        print("\nFiltered Transactions:")
        print_misc_transactions(txns, sort_by=args.sort_by, order=args.order)
        total = sum(t["Amount"] for t in txns)
        print(f"\nTotal for '{args.keyword}' or date range: ${total:.2f}")
        return
    aggregated = aggregate_misc_expenses(args.input)
    if not aggregated:
        print("No expense data found.")
        return
    # Print the aggregated data in a PrettyTable
    print("\nAggregated Expense Data:")
    print_aggregated_table(aggregated, sort_by=args.sort_by, order=args.order)
    
    # If requested, print individual transactions
    if args.list_transactions:
        transactions = get_misc_transactions(args.input)
        if transactions:
            print_misc_transactions(transactions, sort_by=args.sort_by, order=args.order)
        else:
            print("No transactions found.")

    # plot_misc_expenses(aggregated, sort_by=args.sort_by, order=args.order, output_file=args.output)

if __name__ == "__main__":
    main()

    # python misc_analysis.py --sort_by value --order desc
    # python misc_analysis.py --list_transactions --sort_by date --order asc
    # python misc_analysis.py --list_transactions --sort_by date --order asc --category dining

#     python3 misc_analysis.py \
#   --keyword wegmans \
#   --start_date 2025-04-01 \
#   --end_date 2025-04-30

# python3 misc_analysis.py \
#   --start_date 2025-04-01 \
#   --end_date   2025-04-30