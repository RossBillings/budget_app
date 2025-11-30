#!/usr/bin/env python3

import sys
import os
from collections import Counter

# Add the parent directory to Python path to import budget_app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from budget_app.core.models import Transaction, SessionLocal
    from budget_app.core.database import get_db
except ImportError as e:
    print(f"Error importing budget_app modules: {e}")
    print("Make sure you're running this script from the budget_app root directory")
    sys.exit(1)

def main():
    print("Starting expense trends analysis...")
    
    # Create database session
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # Query transactions in the 'Misc' category from database
        print("Querying misc transactions...")
        misc_transactions = db.query(Transaction).filter(Transaction.category == 'misc').all()
        
        print(f"Found {len(misc_transactions)} misc transactions")
        
        if not misc_transactions:
            print("No transactions found in 'Misc' category.")
            return
        
        # Analyze the descriptions in 'Misc' transactions using Counter
        print("Analyzing descriptions...")
        descriptions = [t.description for t in misc_transactions]
        description_counts = Counter(descriptions)

        print("Most common descriptions in the 'Misc' category:")
        for desc, count in description_counts.most_common(15):
            print(f"{desc}: {count}")
        
        print(f"\nTotal unique descriptions: {len(description_counts)}")
        
        # Apply the function to assign new categories
        print("\nAnalyzing categories for reclassification...")
        proposed_categories = []
        transaction_details = []
        
        for transaction in misc_transactions:
            proposed_cat = assign_new_category(transaction.description)
            proposed_categories.append(proposed_cat)
            transaction_details.append({
                'description': transaction.description,
                'amount': transaction.amount,
                'proposed_category': proposed_cat
            })

        # Display the counts of proposed new categories
        new_category_counts = Counter(proposed_categories)

        print("\nProposed new categories for 'Misc' transactions:")
        for category, count in new_category_counts.most_common(15):
            print(f"{category}: {count}")

        # Display sample 'Misc' transactions with proposed new categories
        print(f"\n'Misc' transactions with proposed new categories (showing first 20):")
        print(f"{'Description':<40} {'Amount':<10} {'Proposed Category':<20}")
        print("-" * 70)
        for detail in transaction_details[:20]:
            desc_short = detail['description'][:37] + "..." if len(detail['description']) > 40 else detail['description']
            print(f"{desc_short:<40} ${detail['amount']:<9.2f} {detail['proposed_category']:<20}")

        # Get category counts from database for all transactions
        print("\nGetting all transactions for updated category counts...")
        all_transactions = db.query(Transaction).all()
        
        # Update misc categories with proposed categories for display purposes
        updated_categories = []
        for transaction in all_transactions:
            if transaction.category == 'misc':
                # Find the proposed category for this transaction
                proposed_cat = assign_new_category(transaction.description)
                updated_categories.append(proposed_cat)
            else:
                updated_categories.append(transaction.category)
        
        # Display the updated category counts
        category_counter = Counter(updated_categories)
        print("\nUpdated category counts:")
        for category, count in category_counter.most_common():
            print(f"{category}: {count}")
        
    except Exception as e:
        print(f"Error during database operations: {e}")
        raise
    finally:
        db.close()

# Function to assign new categories based on keywords in descriptions
def assign_new_category(description):
    """Assign category using configuration system."""
    try:
        from budget_app.core.category_config import get_category_config
        config = get_category_config()
        return config.categorize_by_keywords(description)
    except ImportError:
        # Fallback to simple categorization if config not available
        description_lower = description.lower()
        if 'fun zone' in description_lower or 'deep creek funzone' in description_lower:
            return 'Entertainment'
        elif 'shell' in description_lower or 'royal farms' in description_lower:
            return 'Gas/Transportation'
        elif 'chick-fil-a' in description_lower:
            return 'Dining'
        elif 'party city' in description_lower:
            return 'Shopping'
        else:
            return 'Misc'


if __name__ == "__main__":
    main()