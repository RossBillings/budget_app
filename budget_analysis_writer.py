# budget_analysis_writer.py
import csv
import os

def write_budget_analysis_to_csv(file_name, year, month, analysis_data):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, file_name)

    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            existing_data = list(reader)
    except FileNotFoundError:
        existing_data = []

    update_index = None
    for index, row in enumerate(existing_data):
        if row['Year'] == str(year) and row['Month'] == str(month):
            update_index = index
            break

    new_row = {'Year': str(year), 'Month': str(month), **analysis_data}
    if update_index is not None:
        existing_data[update_index] = new_row
    else:
        existing_data.append(new_row)

    with open(file_path, 'w', newline='') as file:
        fieldnames = ['Year', 'Month'] + list(analysis_data.keys())
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data)
