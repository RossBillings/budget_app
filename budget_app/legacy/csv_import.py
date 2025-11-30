import os
import csv
import re  # Import the regular expressions module

def convert_csv(input_files, output_file):
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
                        # Process INPUT.csv format
                        amount = row['Debit'] or f"-{row['Credit']}"
                        transaction_date = row['Transaction Date']
                        description = row['Description']
                    else:
                        # Process INPUT_USAA.csv format
                        try:
                            amount_val = float(row['Amount'])
                            # Invert the sign for USAA input
                            amount_val = -amount_val
                            amount = str(amount_val)
                        except ValueError:
                            amount = row['Amount']
                        transaction_date = row['Date']
                        description = row['Description']

                    # Skip rows that should be excluded
                    if should_exclude(description):
                        continue

                    # Automatic categorization based on the description
                    category = categorize_transaction(description)

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
    
    # Write the combined data to the output file
    with open(output_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)

# Function to check if a transaction should be excluded
def should_exclude(description):
    exclude_keywords = ["CAPITAL ONE MOBILE PYMT"]
    description_lower = description.lower()
    return any(keyword.lower() in description_lower for keyword in exclude_keywords)

def categorize_transaction(description, current_category=None):
    """
    Categorize transaction using configurable keyword patterns.
    
    This function now uses the category configuration system instead of
    hardcoded keyword lists, making it easy to modify categorization rules
    without changing code.
    """
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    
    try:
        from budget_app.core.category_config import get_category_config
        config = get_category_config()
        return config.categorize_by_keywords(description, current_category)
    except ImportError:
        # Fallback to simple logic if config system isn't available
        if description and description.startswith('+'):
            return current_category or "Misc"
        return "Misc"

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # List of input CSV files
    input_csvs = [
        os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "1-CapOne_input_2025.csv"),
        os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "1-USAA_2025.csv")
    ]

    # Output CSV file
    output_csv = os.path.join(script_dir, "..", "..", "data", "inputs", "Expense_Inputs", "cleaned_expenses2025.csv")

    # Run the conversion
    convert_csv(input_csvs, output_csv)

    print("CSV conversion and combination completed.")

if __name__ == "__main__":
    main()
