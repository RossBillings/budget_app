import os
import csv
import re  # Import the regular expressions module

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
# def categorize_transaction(description, current_category=None):
    
#      # If the current category exists and starts with '+', do not overwrite it
#     if current_category and current_category.startswith('+'):
#         return current_category  # Return the current category without changes

def categorize_transaction(description, current_category=None):
    
    # If the description starts with '+', keep the current category unchanged.
    if description and description.startswith('+'):
        return current_category    
    # Convert description to lowercase and remove punctuation
    description_clean = re.sub(r'[^\w\s]', '', description.lower())

    # Define your keywords, all in lowercase
    groceries_keywords = ["wegmans", "weis", "santonis", "wine post", "lidl", "aldi"]
    dining_keywords = ["iron rooster", "tst*iron rooster", "qdoba", "panera", "chickfila", "starbucks", "5guys", "sonny", "hoffmans", "popeyes", "taco", "cracker", "el gran pollo", "alfeos", "chipotle", "bubbakoos", "papa johns", "papa", "pizza", "dunkin", "dunkin donuts"]
    target_keywords = ["target", "hobby lobby", "target.com", "walmart", "hobbylobby", "amazon"]  
    home_supplies_keywords = ["home depot", "lowes", "lawns", "homedepot"]
    # beauty_supplies = ["beautycounter"]
    subscription = ["applecom", "amazonprime", "netflix", "disney", "hulu", "spotify", "youtube", "youtube premium", "youtube.com"]
    gas = ["royalfarms", "exxon", "wawa", "royal farms"]
    insurance = ["healthy paws", "ohio national","mass mutual", "usaa property and casualty insurance","northwestern"]
    bilbrowhomes = ["bilbrowhomes", "bilbrow homes", "bobrow", "chase", "chase", "chase.com", "chase bank", "mr. cooper", "cooper", "mr cooper"]
    income = ["istari", "istari federal", "istari federal pay akpf", "srectrade inc"]
    tithe = ["horizon", "tithe.ly", "compassion international","tithe"]
    transfer = ["usaa transfer", "capital one payment", "capital one", "apple savings transfer"]
    required = ["roundpoint", "mortgage"]
    utilities = ["baltimore gas"]
    automotive = ["toyota"]
    # savings = []
    health = ["equip", "valence nutra", "doctors supplement store", "sp bodybio inc", "revive"]
    retirement = ["lpl financial"]


    # Now check if any keyword is in the cleaned description
    if any(keyword in description_clean for keyword in required):
        return "Required"
    elif any(keyword in description_clean for keyword in tithe):
        return "Tithe"
    elif any(keyword in description_clean for keyword in utilities):
        return "Utilities"
    elif any(keyword in description_clean for keyword in insurance):
        return "Insurance"
    elif any(keyword in description_clean for keyword in dining_keywords):
        return "Dining"
    elif any(keyword in description_clean for keyword in groceries_keywords):
        return "Groceries"
    elif any(keyword in description_clean for keyword in automotive):
        return "Automotive"
    elif any(keyword in description_clean for keyword in home_supplies_keywords):
        return "Home_Supplies"
    elif any(keyword in description_clean for keyword in target_keywords):
        return "Target"
    elif any(keyword in description_clean for keyword in subscription):
        return "Subscription"
    elif any(keyword in description_clean for keyword in gas):
        return "Gas"
    elif any(keyword in description_clean for keyword in bilbrowhomes):
        return "bilbrowhomes"
    elif any(keyword in description_clean for keyword in health):
        return "Health"
    elif any(keyword in description_clean for keyword in retirement):
        return "Retreirement"
    elif any(keyword in description_clean for keyword in income):
        return "Income"
    elif any(keyword in description_clean for keyword in transfer):
        return "Transfer"
    else:
        return "Misc"
    
    # if any(keyword in description_clean for keyword in groceries_keywords):
    #     return "Groceries"
    # elif any(keyword in description_clean for keyword in dining_keywords):
    #     return "Dining"
    # elif any(keyword in description_clean for keyword in target_keywords):
    #     return "Target"
    # elif any(keyword in description_clean for keyword in home_supplies_keywords):
    #     return "Home_Supplies"
    # # elif any(keyword in description_clean for keyword in beauty_supplies):
    # #     return "Beauty"
    # elif any(keyword in description_clean for keyword in subscription):
    #     return "Subscription"
    # elif any(keyword in description_clean for keyword in gas):
    #     return "Gas"
    # elif any(keyword in description_clean for keyword in insurance):
    #     return "Insurance"
    # elif any(keyword in description_clean for keyword in bilbrowhomes):
    #     return "bilbrowhomes"

    # elif any(keyword in description_clean for keyword in tithe):
    #     return "Tithe"

    # elif any(keyword in description_clean for keyword in required):
    #     return "Required"
    # elif any(keyword in description_clean for keyword in utilities):
    #     return "Utilities"
    # elif any(keyword in description_clean for keyword in automotive):
    #     return "Automotive"

    # else:
    #     return "Misc"

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # List of input CSV files
    input_csvs = [
        os.path.join(script_dir, "Expense_Inputs", "CapOne_03-2025.csv"),
        os.path.join(script_dir, "Expense_Inputs", "USAA_03-2025.csv")
    ]

    # Output CSV file
    output_csv = os.path.join(script_dir, "Expense_Inputs", "cleaned_expenses2025.csv")

    # Run the conversion
    convert_csv(input_csvs, output_csv)

    print("CSV conversion and combination completed.")

if __name__ == "__main__":
    main()
