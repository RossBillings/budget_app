
import os
import csv

def convert_csv(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['Description','Amount','Category','Transaction Date' ]
        # fieldnames = ['Transaction Date', 'Description', 'Category', 'Amount']

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in reader:
            # Use Debit amount if available, otherwise use Credit as a negative value
            amount = row['Debit'] or f"-{row['Credit']}"

            # Automatic categorization based on the description
            category = categorize_transaction(row['Description'])

            new_row = {
                'Transaction Date': row['Transaction Date'],
                'Description': row['Description'],
                'Category': category,
                'Amount': amount
            }
            writer.writerow(new_row)

#  ENTER CATGORIES AND KEYWORDS
def categorize_transaction(description):
    groceries_keywords = ["wegmans", "weis", "santoni's", "wine post"]
    dining_keywords = ["qdoba", "panera", "chick-fil-a", "starbucks"]
    target_keywords = ["target"]
    home_supplies_keywords = ["home depot", "lowes"]

    description_lower = description.lower()  # Convert description to lowercase
    if any(keyword in description_lower for keyword in groceries_keywords):
        return "Groceries"
    elif any(keyword in description_lower for keyword in dining_keywords):
        return "Dining"
    elif any(keyword in description_lower for keyword in target_keywords):
        return "Target"
    elif any(keyword in description_lower for keyword in home_supplies_keywords):
        return "Home_Supplies"
    else:
        return "Misc"


# ----> File Paths

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the paths to the CSV files relative to the script location
input_csv = os.path.join(script_dir, "Expense_Inputs", "Nov-Dec2023_transactionsCAP1.csv")
output_csv = os.path.join(script_dir, "Expense_Inputs", "cleaned_expenses.csv")

convert_csv(input_csv, output_csv)
