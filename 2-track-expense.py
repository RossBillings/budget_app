# Imports
import os
from expense_adv import Expense
from budget_adv import BudgetADV
from datetime import datetime
import calendar
from category_loader import get_categories
import csv
import matplotlib.pyplot as plt
import argparse
from budget_analysis_writer import write_budget_analysis_to_csv
from prettytable import PrettyTable


def get_user_expense():
    print(f" 🎯Getting User Expense")
    expense_name = input("Enter expense name:")
    expense_amount = float(input("Enter Expense amount:"))
    transaction_date = input("Enter Transaction Date (YYYY-MM-DD) or press Enter for today: ")
    
    if not transaction_date:
        transaction_date = datetime.now().strftime('%Y-%m-%d')  # Use today's date if not provided

def summarize_expenses(expense_file_path, budget, budget_tracker, year, month):
    print(f" 🎯Summarizing User Expense for {month}/{year}")
    expenses = []
    with open(expense_file_path, "r") as f:
        reader = csv.DictReader(f)  # Use DictReader to automatically handle the header
        for row in reader:
            transaction_date = row['Transaction Date'].strip()  # Strip whitespace once here
            try:
                # Attempt to parse the date and skip any rows where the date is not in the correct format
                expense_date = datetime.strptime(transaction_date, '%Y-%m-%d')
                
                # Check if the expense is in the specified month and year
                if expense_date.year == year and expense_date.month == month:
                    expense_name = row['Description'].strip()
                    expense_amount = float(row['Amount'].strip())
                    expense_category = row['Category'].strip()

                    # Create and append the expense object
                    line_expense = Expense(
                        name=expense_name, 
                        amount=expense_amount, 
                        category=expense_category,
                        transaction_date=transaction_date
                    )
                    expenses.append(line_expense)

            except ValueError:
                # Log an error or pass if a row with an invalid date format is encountered
                print(f"Skipping row with invalid date format: {row}")
                continue  # This ensures the rest of the loop is skipped for this iteration

            

    amount_by_category = {}
    for expense in expenses:
        key = expense.category
        if key in amount_by_category:
            amount_by_category[key] += expense.amount
        else:
            amount_by_category[key] = expense.amount

    table = PrettyTable()
    table.field_names = ["Category", "Budgeted", "Spent", "Remaining"]
    category_budgets = budget_tracker.category_budgets
    total_budgeted = 0
    total_spent = 0
    total_remaining = 0
    for category in category_budgets.keys():
        # Skip the Income category
        if category.strip().lower() == "income":
            continue
        if category.strip().lower() == "transfer":
            continue
        budgeted_amount = category_budgets.get(category, 0)
        spent_amount = amount_by_category.get(category, 0)
        difference = budgeted_amount - spent_amount
        table.add_row([category, f"${budgeted_amount:.2f}", f"${spent_amount:.2f}", f"${difference:.2f}"])
        total_budgeted += budgeted_amount
        total_spent += spent_amount
        total_remaining += difference
    table.add_row(["TOTAL", f"${total_budgeted:.2f}", f"${total_spent:.2f}", f"${total_remaining:.2f}"])
    print("\nCategory-wise Expense Summary 📊:")
    print(table)

    total_spent = sum(expense.amount for expense in expenses)
    remaining_budget = budget - total_spent

        # Visualization using a bar chart
    fig, ax = plt.subplots()
    categories = list(category_budgets.keys())
    budgeted = [category_budgets.get(cat, 0) for cat in categories]
    spent = [amount_by_category.get(cat, 0) for cat in categories]

    ax.bar(categories, budgeted, label='Budgeted', alpha=0.6)
    ax.bar(categories, spent, label='Spent', alpha=0.6)
    ax.set_ylabel('Amount ($)')
    ax.set_title('Budget vs Spent by Category')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    # plt.show()

    # Save the plot to a file
    script_dir2 = os.path.dirname(os.path.abspath(__file__))
    filename = f"budget_analysis_plot_{year}_{month}.png"
    plot_file_path = os.path.join(script_dir2, "Output", filename)
    # plot_file_path = os.path.join(script_dir2, "Output", "budget_analysis_plot.png")
    plt.savefig(plot_file_path)
 
    return total_spent, remaining_budget, amount_by_category


def print_total_income(expense_file_path, year, month):
    """Parse the CSV input file for category 'Income' and print the total sum of income for the given month and year."""
    income_sum = 0
    with open(expense_file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                transaction_date = datetime.strptime(row['Transaction Date'].strip(), '%Y-%m-%d')
            except ValueError:
                print(f"Skipping row with invalid date format: {row}")
                continue
            if transaction_date.year == year and transaction_date.month == month and row['Category'].strip().lower() == 'income':
                try:
                    income_sum += float(row['Amount'].strip())
                except ValueError:
                    print(f"Skipping row with invalid amount: {row}")
                    continue
    print(f"Total Income for {month}/{year}: ${income_sum:.2f}")


# def calculate_net_income_from_categories(amount_by_category):
#     """Calculate net income for the month by subtracting all expense categories (excluding 'Income') from the total income.
#     This version uses the raw expense amounts (without applying absolute values) so that the calculations match the category-wise summary.
#     """
#     income_total = amount_by_category.get('Income', 0)
#     # If the income total is negative, invert it (assume it was recorded with the wrong sign)
#     if income_total < 0:
#         income_total = -income_total
#     # Sum the expense amounts for non-income categories without taking the absolute value
#     other_expenses = sum(amount for cat, amount in amount_by_category.items() if cat.strip().lower() != 'income')
#     net_income = income_total - other_expenses
#     table = PrettyTable()
#     table.field_names = ["Net Income for the Month"]
#     # Show the full equation in the table
#     equation = f"${income_total:.2f} - ${other_expenses:.2f} = ${net_income:.2f}"
#     table.add_row([equation])
#     print("\nNet Income Summary:")
#     print(table)
#     return net_income


# Preparation for CLI
def print_expenses_by_category(expense_file_path, category, year, month):
    print(f"Expenses for category {category} in {month}/{year}:")
    with open(expense_file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip any rows that don't have a valid date in 'Transaction Date'
            if row['Transaction Date'].lower() == 'transaction date':
                continue

            transaction_date = row['Transaction Date'].strip()
            try:
                expense_date = datetime.strptime(transaction_date, '%Y-%m-%d')
            except ValueError as e:
                print(f"Error parsing date from row: {row}")
                print(f"Error: {e}")
                continue

            # Check if the expense is in the specified month, year, and category
            if expense_date.year == year and expense_date.month == month and row['Category'].strip().lower() == category.lower():
                print(f"{row['Description']}: ${row['Amount']}")

def green(text):
    return f"\033[92m{text}\033[0m"

# New function to update budgets with missing categories
def update_budgets_with_missing_categories(expense_csv_path, budget_csv_path):
    """Read the expense CSV and update the budgets CSV with any missing categories.
    Any category found in the expense CSV that is not present in the budgets CSV will be appended with a default budget of 0.
    """
    import csv
    import os
    
    # Collect categories from the expense CSV
    expense_categories = set()
    with open(expense_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row.get('Category', '').strip()
            # Skip header or invalid rows
            if category and category.lower() != 'transaction date':
                expense_categories.add(category)
    
    # Collect existing categories from the budgets CSV
    budget_categories = set()
    if os.path.exists(budget_csv_path):
        with open(budget_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row.get('Category', '').strip()
                if cat:
                    budget_categories.add(cat)
    
    # Identify missing categories
    missing_categories = expense_categories - budget_categories
    
    # Append missing categories to budgets.csv with a default budget value (e.g., 0)
    if missing_categories:
        with open(budget_csv_path, 'a', newline='') as f:
            fieldnames = ['Category', 'Budgeted']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            # If the file is empty, write the header
            if os.stat(budget_csv_path).st_size == 0:
                writer.writeheader()
            for cat in missing_categories:
                writer.writerow({'Category': cat, 'Budgeted': 0})
        print("Added missing categories to budgets.csv: " + ", ".join(missing_categories))
    else:
        print("No missing categories found in budgets.csv.")


# Main program function
def main():
    parser = argparse.ArgumentParser(description="Expense Tracker")
    parser.add_argument("--category", help="The category of expenses to display", default=None)
    parser.add_argument("--year", help="The year for expense analysis", type=int, default=None)
    parser.add_argument("--month", help="The month for expense analysis", type=int, default=None)
    args = parser.parse_args()

    # ----> File Paths
    print(" 🎯Running Expense Tracker")
    

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the paths to the CSV files
    expense_file_path = os.path.join(script_dir, "Expense_Inputs", "cleaned_expenses2025.csv")
    budget_file_path = os.path.join(script_dir,"Expense_Inputs", "budgets.csv")
    output_csv_name = os.path.join(script_dir, "Output", "budget_history.csv")  # file name within the relative path
    update_budgets_with_missing_categories(expense_file_path, budget_file_path)


    budget_tracker = BudgetADV()
    budget_tracker.load_budgets_from_csv(budget_file_path)
    budget = budget_tracker.get_total_budget()

    if args.category and args.year and args.month:
        print_expenses_by_category(expense_file_path, args.category, args.year, args.month)
    else:
        # Ask user for the year and month if not provided via command line
        analysis_year = args.year if args.year else int(input("Enter the year for expense analysis (e.g., 2024): "))
        analysis_month = args.month if args.month else int(input("Enter the month for expense analysis (1-12): "))

        # Print the total income for the given month and year
        print_total_income(expense_file_path, analysis_year, analysis_month)

        # Get the total spent and remaining budget from summarize_expenses
        total_spent, remaining_budget, amount_by_category = summarize_expenses(
            expense_file_path, budget, budget_tracker, analysis_year, analysis_month)

    # Write the analysis data to CSV
    category_budgets = budget_tracker.category_budgets
    write_budget_analysis_to_csv(output_csv_name, analysis_year, analysis_month, category_budgets, amount_by_category)

    # Calculate and display net income: total income minus all expenses (excluding Income category)
    # calculate_net_income_from_categories(amount_by_category)

if __name__ == "__main__":
    main()

    # source venv/bin/activate