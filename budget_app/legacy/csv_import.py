import os
import csv

from budget_app.core.categorizer import load_category_rules


def convert_csv(input_files, output_file):
    rules = load_category_rules()
    combined_rows = []
    fieldnames = ['Description', 'Amount', 'Category', 'Transaction Date']

    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: Input file {input_file} not found, skipping...")
            continue

        try:
            with open(input_file, 'r') as infile:
                reader = csv.DictReader(infile)

                for row in reader:
                    if 'Debit' in row and 'Credit' in row:
                        amount = row['Debit'] or f"-{row['Credit']}"
                        transaction_date = row['Transaction Date']
                        description = row['Description']
                    else:
                        try:
                            amount_val = float(row['Amount'])
                            amount_val = -amount_val
                            amount = str(amount_val)
                        except ValueError:
                            amount = row['Amount']
                        transaction_date = row['Date']
                        description = row['Description']

                    if rules.should_exclude(description):
                        continue

                    category = rules.categorize(description)

                    new_row = {
                        'Transaction Date': transaction_date,
                        'Description': description,
                        'Category': category,
                        'Amount': amount
                    }

                    combined_rows.append(new_row)
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
            continue

    with open(output_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)


def should_exclude(description):
    return load_category_rules().should_exclude(description)


def categorize_transaction(description, current_category=None):
    return load_category_rules().categorize(description, current_category)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    input_csvs = [
        os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "1-CapOne_input_2025.csv"),
        os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "1-USAA_2025.csv")
    ]

    output_csv = os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "cleaned_expenses2025.csv")

    convert_csv(input_csvs, output_csv)

    print("CSV conversion and combination completed.")


if __name__ == "__main__":
    main()
