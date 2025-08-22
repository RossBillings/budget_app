"""
Automatic transaction categorization based on description keywords.

This module provides keyword-based categorization for financial transactions.
"""
import re
from typing import Optional


def categorize_transaction(description: str, current_category: Optional[str] = None) -> str:
    """
    Automatically categorize a transaction based on its description.
    
    Args:
        description: The transaction description
        current_category: The current category (if any)
        
    Returns:
        str: The categorized transaction type
    """
    # If the description starts with '+', keep the current category unchanged
    if description.startswith('+') and current_category:
        return current_category
    
    # Convert description to lowercase and remove punctuation
    description_clean = re.sub(r'[^\w\s]', '', description.lower())

    # Define keywords, all in lowercase
    groceries_keywords = ["wegmans", "weis", "santonis", "wine post", "lidl", "aldi"]
    dining_keywords = [
        "iron rooster", "tst*iron rooster", "qdoba", "panera", "chickfila", 
        "starbucks", "5guys", "sonny", "hoffmans", "popeyes", "taco", "cracker", 
        "el gran pollo", "alfeos", "chipotle", "bubbakoos", "papa johns", "papa", 
        "pizza", "dunkin", "dunkin donuts"
    ]
    target_keywords = ["target", "hobby lobby", "target.com", "walmart", "hobbylobby", "amazon"]
    home_supplies_keywords = ["home depot", "lowes", "lawns", "homedepot"]
    subscription = [
        "applecom", "amazonprime", "netflix", "disney", "hulu", "spotify", 
        "youtube", "youtube premium", "youtube.com"
    ]
    gas = ["royalfarms", "exxon", "wawa", "royal farms"]
    insurance = [
        "healthy paws", "ohio national", "mass mutual", 
        "usaa property and casualty insurance", "northwestern"
    ]
    bilbrowhomes = [
        "bilbrowhomes", "bilbrow homes", "bobrow", "chase", "chase.com", 
        "chase bank", "mr. cooper", "cooper", "mr cooper"
    ]
    income = ["istari", "istari federal", "istari federal pay akpf", "srectrade inc"]
    tithe = ["horizon", "tithe.ly", "compassion international", "tithe"]
    transfer = ["usaa transfer", "capital one payment", "capital one", "apple savings transfer"]
    required = ["roundpoint", "mortgage"]
    utilities = ["baltimore gas"]
    automotive = ["toyota"]
    retirement = ["lpl financial"]
    health = ["cvs", "pharmacy", "doctor", "medical", "hospital", "clinic"]

    # Check keywords in order of priority
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
        return "Retirement"
    elif any(keyword in description_clean for keyword in income):
        return "Income"
    elif any(keyword in description_clean for keyword in transfer):
        return "Transfer"
    else:
        return "Misc"


def should_exclude(description: str) -> bool:
    """
    Check if a transaction should be excluded from import.
    
    Args:
        description: The transaction description
        
    Returns:
        bool: True if the transaction should be excluded
    """
    exclude_keywords = ["payment thank you", "autopay", "online payment"]
    description_lower = description.lower()
    return any(keyword.lower() in description_lower for keyword in exclude_keywords)
