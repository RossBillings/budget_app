#!/usr/bin/env python3

import os
import argparse
import sys
import csv
from datetime import datetime

# Add the parent directory to Python path to import budget_app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from budget_app.core.models import Transaction, SessionLocal
    from budget_app.core.database import get_db
except ImportError as e:
    print(f"Error importing budget_app modules: {e}")
    print("Make sure you're running this script from the budget_app root directory")
    sys.exit(1)

def create_keyword_analysis(keyword, output_dir="data/outputs/Output"):
    print(f"Analyzing transactions for keyword: '{keyword}'")
    
    # Step 1: Load the data from database
    db = SessionLocal()
    try:
        # Step 2: Query transactions containing the keyword from database
        filtered_transactions = db.query(Transaction).filter(
            Transaction.description.ilike(f'%{keyword}%')
        ).all()
        
        if not filtered_transactions:
            print(f"No transactions found containing keyword '{keyword}'.")
            return
        
        print(f"Found {len(filtered_transactions)} transactions containing '{keyword}'")
        
        # Convert to list of dictionaries for CSV output
        filtered_data = []
        total_amount = 0.0
        
        for transaction in filtered_transactions:
            row_data = {
                'Description': transaction.description,
                'Transaction Date': str(transaction.transaction_date),
                'Amount': transaction.amount,
                'Category': transaction.category,
                'Source': transaction.source
            }
            filtered_data.append(row_data)
            total_amount += transaction.amount
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return
    finally:
        db.close()

    # Step 3: Save to a new CSV
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{keyword}_history.csv")
    
    # Write CSV manually
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Description', 'Transaction Date', 'Amount', 'Category', 'Source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_data)
    
    print(f"Filtered data saved to {output_file}")
    
    # Step 4: Show summary statistics
    avg_amount = total_amount / len(filtered_data)
    print(f"\nSummary:")
    print(f"Total transactions: {len(filtered_data)}")
    print(f"Total amount: ${total_amount:.2f}")
    print(f"Average amount: ${avg_amount:.2f}")
    
    # Show sample transactions
    print(f"\nSample transactions (first 10):")
    print(f"{'Date':<12} {'Amount':<10} {'Description'[:30]:<30}")
    print("-" * 52)
    for row in filtered_data[:10]:
        desc_short = row['Description'][:27] + "..." if len(row['Description']) > 30 else row['Description']
        print(f"{row['Transaction Date']:<12} ${row['Amount']:<9.2f} {desc_short:<30}")
    
    print(f"\nAnalysis complete for keyword '{keyword}'!")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze transactions for a specific keyword from the budget database."
    )
    parser.add_argument("keyword", type=str, help="Keyword to filter transactions")
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/outputs/Output", 
        help="Directory to save output files (default: data/outputs/Output)"
    )
    args = parser.parse_args()

    create_keyword_analysis(args.keyword, args.output_dir)

# Example Usage
# python3 scripts/4-deep_keyword_analysis.py Target
# python3 scripts/4-deep_keyword_analysis.py Groceries --output-dir custom_output/