import csv
import os
import matplotlib.pyplot as plt
from datetime import datetime

def read_budget_history(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            year_month = (int(row['Year']), int(row['Month']))  # Create a sortable tuple
            data.append((year_month, row))
    # Sort data by year and month
    data.sort(key=lambda x: x[0])
    # sorted_months = sorted(monthly_data.keys(), key=lambda x: datetime.strptime(x, "%

    return [row for _, row in data]

def read_budget_data(file_path):
    budget_data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            budget_data.append(row)
    return budget_data

def create_visualizations(data, budget_data, output_dir):
    # Process budget data to get budgeted amounts for each category
    budgeted_amounts = {row['Category']: float(row['Amount']) for row in budget_data}

    # Organize spending data by category and month
    category_data = {}
    for row in data:
        category = row['Category']
        # Create a sortable key with zero-padded month and year
        year_month_key = f"{row['Year']}-{int(row['Month']):02d}"
        if category not in category_data:
            category_data[category] = {}
        category_data[category][year_month_key] = float(row['Spent'])

    # Create a bar chart for each category
    for category, monthly_data in category_data.items():
        # Sort months for plotting
        sorted_months = sorted(monthly_data.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))
        spent_amounts = [monthly_data[month] for month in sorted_months]

        fig, ax = plt.subplots()
        ax.bar(sorted_months, spent_amounts, label='Spent')

        # Add a horizontal line for the budgeted amount
        if category in budgeted_amounts:
            ax.axhline(y=budgeted_amounts[category], color='r', linestyle='-', label='Budgeted')

        ax.set_ylabel('Amount ($)')
        ax.set_title(f'Spending in {category}')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot
        plot_file_path = os.path.join(output_dir, f"spending_{category}.png")
        plt.savefig(plot_file_path)
        plt.close()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(script_dir,"Output", "budget_history.csv")
    budget_file_path = os.path.join(script_dir,"Expense_Inputs", "budgets.csv")  # Path to budget.csv
    output_dir = os.path.join(script_dir, "Output")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    budget_data = read_budget_data(budget_file_path)  # Read budget data
    spending_data = read_budget_history(csv_file_path)  # Read spending data
    create_visualizations(spending_data, budget_data, output_dir)

if __name__ == "__main__":
    main()
