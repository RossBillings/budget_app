#!/usr/bin/env python3
"""
Script to populate the database with default categories and keywords.

This script creates the default categories based on the hardcoded keywords
from the categorization module.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from budget_app.core.database import create_category

def populate_default_categories():
    """Populate the database with default categories and their keywords."""
    
    default_categories = [
        {
            'name': 'Groceries',
            'description': 'Food and grocery shopping',
            'color': '#28a745',
            'keywords': ['wegmans', 'weis', 'santonis', 'wine post', 'lidl', 'aldi']
        },
        {
            'name': 'Dining',
            'description': 'Restaurants and food delivery',
            'color': '#fd7e14',
            'keywords': [
                'iron rooster', 'tst*iron rooster', 'qdoba', 'panera', 'chickfila', 
                'starbucks', '5guys', 'sonny', 'hoffmans', 'popeyes', 'taco', 'cracker', 
                'el gran pollo', 'alfeos', 'chipotle', 'bubbakoos', 'papa johns', 'papa', 
                'pizza', 'dunkin', 'dunkin donuts'
            ]
        },
        {
            'name': 'Target',
            'description': 'Target, Walmart, and general retail',
            'color': '#dc3545',
            'keywords': ['target', 'hobby lobby', 'target.com', 'walmart', 'hobbylobby', 'amazon']
        },
        {
            'name': 'Home_Supplies',
            'description': 'Home improvement and supplies',
            'color': '#6f42c1',
            'keywords': ['home depot', 'lowes', 'lawns', 'homedepot']
        },
        {
            'name': 'Subscription',
            'description': 'Digital subscriptions and services',
            'color': '#e83e8c',
            'keywords': [
                'applecom', 'amazonprime', 'netflix', 'disney', 'hulu', 'spotify', 
                'youtube', 'youtube premium', 'youtube.com'
            ]
        },
        {
            'name': 'Gas',
            'description': 'Fuel and gas stations',
            'color': '#20c997',
            'keywords': ['royalfarms', 'exxon', 'wawa', 'royal farms']
        },
        {
            'name': 'Insurance',
            'description': 'Insurance payments',
            'color': '#0dcaf0',
            'keywords': [
                'healthy paws', 'ohio national', 'mass mutual', 
                'usaa property and casualty insurance', 'northwestern'
            ]
        },
        {
            'name': 'bilbrowhomes',
            'description': 'Housing and mortgage payments',
            'color': '#6c757d',
            'keywords': [
                'bilbrowhomes', 'bilbrow homes', 'bobrow', 'chase', 'chase.com', 
                'chase bank', 'mr. cooper', 'cooper', 'mr cooper'
            ]
        },
        {
            'name': 'Income',
            'description': 'Salary and income',
            'color': '#198754',
            'keywords': ['istari', 'istari federal', 'istari federal pay akpf', 'srectrade inc']
        },
        {
            'name': 'Tithe',
            'description': 'Religious donations and tithing',
            'color': '#ffc107',
            'keywords': ['horizon', 'tithe.ly', 'compassion international', 'tithe']
        },
        {
            'name': 'Transfer',
            'description': 'Bank transfers and payments',
            'color': '#adb5bd',
            'keywords': ['usaa transfer', 'capital one payment', 'capital one', 'apple savings transfer']
        },
        {
            'name': 'Required',
            'description': 'Required payments and bills',
            'color': '#dc3545',
            'keywords': ['roundpoint', 'mortgage']
        },
        {
            'name': 'Utilities',
            'description': 'Utility bills',
            'color': '#0d6efd',
            'keywords': ['baltimore gas']
        },
        {
            'name': 'Automotive',
            'description': 'Car-related expenses',
            'color': '#495057',
            'keywords': ['toyota']
        },
        {
            'name': 'Retirement',
            'description': 'Retirement savings and investments',
            'color': '#6610f2',
            'keywords': ['lpl financial']
        },
        {
            'name': 'Health',
            'description': 'Medical and health expenses',
            'color': '#d63384',
            'keywords': ['cvs', 'pharmacy', 'doctor', 'medical', 'hospital', 'clinic']
        },
        {
            'name': 'Misc',
            'description': 'Miscellaneous and uncategorized expenses',
            'color': '#6c757d',
            'keywords': []
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for category_data in default_categories:
        try:
            result = create_category(
                name=category_data['name'],
                description=category_data['description'],
                color=category_data['color'],
                keywords=category_data['keywords']
            )
            print(f"✓ Created category: {result['name']} with {len(result['keywords'])} keywords")
            created_count += 1
        except ValueError as e:
            if "already exists" in str(e):
                print(f"- Skipped existing category: {category_data['name']}")
                skipped_count += 1
            else:
                print(f"✗ Error creating category {category_data['name']}: {e}")
        except Exception as e:
            print(f"✗ Unexpected error creating category {category_data['name']}: {e}")
    
    print(f"\nSummary: {created_count} created, {skipped_count} skipped")
    return created_count, skipped_count

if __name__ == '__main__':
    print("Populating database with default categories...")
    try:
        created, skipped = populate_default_categories()
        if created > 0:
            print(f"\n🎉 Successfully populated {created} default categories!")
        else:
            print(f"\n📝 All categories already exist ({skipped} skipped)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
