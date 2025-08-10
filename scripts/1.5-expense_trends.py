import pandas as pd

def main():

# Read the CSV file into a DataFrame
    df = pd.read_csv('Expense_Inputs/cleaned_expenses2024.csv')

# Filter transactions in the 'Misc' category
    misc_transactions = df[df['Category'] == 'Misc']

# Analyze the descriptions in 'Misc' transactions
    description_counts = misc_transactions['Description'].value_counts()

    print("Most common descriptions in the 'Misc' category:")
    print(description_counts.head(15))

# Function to assign new categories based on keywords in descriptions
    def assign_new_category(description):
        description_lower = description.lower()
        if 'fun zone' in description_lower or 'deep creek funzone' in description_lower:
            return 'Entertainment'
        elif 'shell' in description_lower or 'royal farms' in description_lower:
            return 'Gas/Transportation'
        elif 'cracker barrel' in description_lower or 'chick-fil-a' in description_lower:
            return 'Dining'
        elif 'apple.com' in description_lower:
            return 'Subscription'
        elif 'driveezmd' in description_lower:
            return 'Tolls'
        elif 'health' in description_lower or 'pet insuran' in description_lower:
            return 'Insurance'
        elif 'party city' in description_lower:
            return 'Shopping'
        elif 'deep creek' in description_lower or 'state park' in description_lower:
            return 'Recreation'
        else:
            return 'Misc'

    # Apply the function to assign new categories
    misc_transactions['Proposed Category'] = misc_transactions['Description'].apply(assign_new_category)

    # Display the counts of proposed new categories
    new_category_counts = misc_transactions['Proposed Category'].value_counts()

    print("\nProposed new categories for 'Misc' transactions:")
    print(new_category_counts.head(15))

    # Display the 'Misc' transactions with proposed new categories
    print("\n'Misc' transactions with proposed new categories:")
    print(misc_transactions[['Description', 'Amount', 'Proposed Category']])

    # Optionally, update the original DataFrame with new categories
    df.loc[df['Category'] == 'Misc', 'Category'] = misc_transactions['Proposed Category']

    # Display the updated category counts
    print("\nUpdated category counts:")
    print(df['Category'].value_counts())


if __name__ == "__main__":
    main()