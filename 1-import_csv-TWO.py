import os
import csv

def convert_csv(input_files, output_file):
    combined_rows = []
    fieldnames = ['Description', 'Amount', 'Category', 'Transaction Date']

    for input_file in input_files:
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

# ENTER CATEGORIES AND KEYWORDS
def categorize_transaction(description):
    groceries_keywords = ["wegmans", "weis", "santoni's", "wine post", "LIDL"]
    dining_keywords = ["qdoba", "panera", "chick-fil-a", "starbucks", "5GUYS", "SONNY", "HOFFMANS", "POPEYES"]
    target_keywords = ["target"]
    home_supplies_keywords = ["home depot", "lowes"]
    beauty_supplies = ["BEAUTYCOUNTER"]

    description_lower = description.lower()  # Convert description to lowercase
    if any(keyword in description_lower for keyword in groceries_keywords):
        return "Groceries"
    elif any(keyword in description_lower for keyword in dining_keywords):
        return "Dining"
    elif any(keyword in description_lower for keyword in target_keywords):
        return "Target"
    elif any(keyword in description_lower for keyword in home_supplies_keywords):
        return "Home_Supplies"
    elif any(keyword in description_lower for keyword in beauty_supplies):
        return "Beauty"
    else:
        return "Misc"

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # List of input CSV files
    input_csvs = [
        os.path.join(script_dir, "Expense_Inputs", "INPUT.csv"),
        os.path.join(script_dir, "Expense_Inputs", "INPUT_USAA.csv")
    ]

    # Output CSV file
    output_csv = os.path.join(script_dir, "Expense_Inputs", "cleaned_expenses2024.csv")

    # Run the conversion
    convert_csv(input_csvs, output_csv)

    print("CSV conversion and combination completed.")

if __name__ == "__main__":
    main()
