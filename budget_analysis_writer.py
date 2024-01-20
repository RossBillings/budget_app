import csv
import os

def write_budget_analysis_to_csv(file_name, year, month, category_budgets, amount_by_category):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, file_name)

    # Prepare the data for CSV
    analysis_data = []
    for category, budgeted_amount in category_budgets.items():
        spent_amount = amount_by_category.get(category, 0)
        remaining = budgeted_amount - spent_amount
        analysis_data.append({
            'Year': year,
            'Month': month,
            'Category': category,
            'Budgeted': budgeted_amount,
            'Spent': spent_amount,
            'Remaining': remaining
        })

    # Write data to CSV
    try:
        with open(file_path, 'r', newline='') as file:
            reader = csv.DictReader(file)
            existing_data = list(reader)
    except FileNotFoundError:
        existing_data = []

    # Update or append new data
    for new_row in analysis_data:
        existing_row = next((item for item in existing_data if item['Year'] == str(year) and item['Month'] == str(month) and item['Category'] == new_row['Category']), None)
        if existing_row:
            existing_data.remove(existing_row)
        existing_data.append(new_row)

    with open(file_path, 'w', newline='') as file:
        fieldnames = ['Year', 'Month', 'Category', 'Budgeted', 'Spent', 'Remaining']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data)
