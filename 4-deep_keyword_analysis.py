import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Use a non-GUI backend
import matplotlib.pyplot as plt
import os
import argparse

def create_keyword_analysis(input_file, keyword):
    # Step 1: Load the data
    data = pd.read_csv(input_file)

    # Ensure the 'Description', 'Transaction Date', and 'Amount' columns exist
    if 'Description' not in data.columns or 'Transaction Date' not in data.columns or 'Amount' not in data.columns:
        raise ValueError("CSV must have 'Description', 'Transaction Date', and 'Amount' columns.")

    # Step 2: Filter rows containing the keyword
    filtered_data = data[data['Description'].str.contains(keyword, case=False, na=False)]

    # Step 3: Save to a new CSV
    output_file = f"Output/{keyword}_history.csv"
    filtered_data.to_csv(output_file, index=False)
    print(f"Filtered data saved to {output_file}")

    # Step 4: Generate a graph
    # Convert 'Transaction Date' to datetime for plotting
    filtered_data.loc[:, 'Transaction Date'] = pd.to_datetime(filtered_data['Transaction Date'], errors='coerce')
    filtered_data = filtered_data.dropna(subset=['Transaction Date'])  # Drop rows with invalid dates

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.bar(filtered_data['Transaction Date'], filtered_data['Amount'], label=f"Transactions for {keyword}")    
    plt.title(f"{keyword} Transactions Over Time")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Save and show the plot
    plt.savefig(f"Output/{keyword}_transactions_plot.png")
    plt.show()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze transactions for a specific keyword.")
    parser.add_argument("input_file", type=str, help="Path to the input CSV file")
    parser.add_argument("keyword", type=str, help="Keyword to filter transactions")
    args = parser.parse_args()

    create_keyword_analysis(args.input_file, args.keyword)

# Example Usage
# python3 /Users/rossbillings/GitHub/budget_app/4-deep_keyword_analysis.py Expense_Inputs/cleaned_expenses2024.csv Target