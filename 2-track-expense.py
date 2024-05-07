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

    print("\nCategory-wise Expense Summary 📊:")
    category_budgets = budget_tracker.category_budgets
    for category in category_budgets.keys():
        budgeted_amount = category_budgets.get(category, 0)
        spent_amount = amount_by_category.get(category, 0)
        difference = budgeted_amount - spent_amount
        print(f"{category}: Budgeted: ${budgeted_amount:.2f}, Spent: ${spent_amount:.2f}, Remaining: ${difference:.2f}")

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
    expense_file_path = os.path.join(script_dir, "Expense_Inputs", "cleaned_expenses.csv")
    budget_file_path = os.path.join(script_dir,"Expense_Inputs", "budgets.csv")
    output_csv_name = os.path.join(script_dir, "Output", "budget_history.csv")  # file name within the relative path


    budget_tracker = BudgetADV()
    budget_tracker.load_budgets_from_csv(budget_file_path)
    budget = budget_tracker.get_total_budget()

    if args.category and args.year and args.month:
        print_expenses_by_category(expense_file_path, args.category, args.year, args.month)
    else:
        # Ask user for the year and month if not provided via command line
        analysis_year = args.year if args.year else int(input("Enter the year for expense analysis (e.g., 2024): "))
        analysis_month = args.month if args.month else int(input("Enter the month for expense analysis (1-12): "))

        # Get the total spent and remaining budget from summarize_expenses
        # total_spent, remaining_budget = summarize_expenses(expense_file_path, budget, budget_tracker, analysis_year, analysis_month)
        total_spent, remaining_budget, amount_by_category = summarize_expenses(
            expense_file_path, budget, budget_tracker, analysis_year, analysis_month)



    # Prepare the analysis data
    analysis_data = {
        'Total Budget': budget,
        'Total Spent': total_spent,
        'Remaining Budget': remaining_budget
        # Add other relevant data if necessary
    }

    # Write the analysis data to CSV
    category_budgets = budget_tracker.category_budgets
    # amount_by_category = ... # gather your amounts by category data

    # write_budget_analysis_to_csv(output_csv_name, analysis_year, analysis_month, category_budgets, amount_by_category)
    write_budget_analysis_to_csv(output_csv_name, analysis_year, analysis_month, category_budgets, amount_by_category)


    # write_budget_analysis_to_csv(output_csv_name, analysis_year, analysis_month, analysis_data)

if __name__ == "__main__":
    main()