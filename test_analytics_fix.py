#!/usr/bin/env python3
"""
Test script to validate analytics functionality and catch errors.
This will test the API endpoints and ensure they return valid data.
"""

import requests
import json
import sys
from datetime import datetime, date

def test_api_endpoint(url, description):
    """Test an API endpoint and validate the response."""
    try:
        print(f"Testing {description}...")
        response = requests.get(url, timeout=10)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ ERROR: Expected 200, got {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"  ❌ ERROR: Invalid JSON response")
            print(f"  Error: {e}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        print(f"  Response structure: {type(data)}")
        
        # Check if response has success field
        if 'success' not in data:
            print(f"  ❌ ERROR: Missing 'success' field")
            print(f"  Data: {data}")
            return False
        
        if not data['success']:
            print(f"  ❌ ERROR: API returned success=False")
            print(f"  Error: {data.get('error', 'Unknown error')}")
            return False
        
        # Check if response has data field
        if 'data' not in data:
            print(f"  ❌ ERROR: Missing 'data' field")
            print(f"  Data: {data}")
            return False
        
        if data['data'] is None:
            print(f"  ❌ ERROR: 'data' field is null")
            return False
        
        print(f"  ✅ SUCCESS: Valid response with data")
        print(f"  Data type: {type(data['data'])}")
        
        # Print sample data structure
        if isinstance(data['data'], dict):
            print(f"  Data keys: {list(data['data'].keys())}")
        elif isinstance(data['data'], list):
            print(f"  Data length: {len(data['data'])}")
            if len(data['data']) > 0:
                print(f"  First item type: {type(data['data'][0])}")
                if isinstance(data['data'][0], dict):
                    print(f"  First item keys: {list(data['data'][0].keys())}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ ERROR: Request failed")
        print(f"  Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: Unexpected error")
        print(f"  Error: {e}")
        return False

def test_monthly_trends_data_structure(url):
    """Test the monthly trends endpoint specifically for required data structure."""
    print("Testing monthly trends data structure...")
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('success') or not data.get('data'):
            print("  ❌ ERROR: Invalid basic response structure")
            return False
        
        trends_data = data['data']
        
        # Check required fields
        required_fields = ['months', 'expenses', 'income']
        for field in required_fields:
            if field not in trends_data:
                print(f"  ❌ ERROR: Missing required field '{field}'")
                return False
            
            if not isinstance(trends_data[field], list):
                print(f"  ❌ ERROR: Field '{field}' is not a list")
                return False
        
        # Check arrays have same length
        months_len = len(trends_data['months'])
        expenses_len = len(trends_data['expenses'])
        income_len = len(trends_data['income'])
        
        if not (months_len == expenses_len == income_len):
            print(f"  ❌ ERROR: Array length mismatch")
            print(f"    months: {months_len}, expenses: {expenses_len}, income: {income_len}")
            return False
        
        print(f"  ✅ SUCCESS: Valid data structure with {months_len} data points")
        
        # Print sample data
        if months_len > 0:
            print(f"  Sample month: {trends_data['months'][0]}")
            print(f"  Sample expense: {trends_data['expenses'][0]}")
            print(f"  Sample income: {trends_data['income'][0]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False

def main():
    """Main test function."""
    base_url = "http://127.0.0.1:8080"
    
    # Test parameters
    start_date = "2025-01-01"
    end_date = "2025-11-26"
    
    print("🧪 Testing Analytics API Endpoints")
    print("=" * 50)
    
    tests = [
        (f"{base_url}/api/categories", "Categories endpoint"),
        (f"{base_url}/api/expenses/aggregated?category=all&start_date={start_date}&end_date={end_date}", "Aggregated expenses (all categories)"),
        (f"{base_url}/api/trends/monthly?category=all&start_date={start_date}&end_date={end_date}", "Monthly trends (all categories)"),
        (f"{base_url}/api/category/budget?category=food", "Category budget endpoint"),
    ]
    
    results = []
    
    for url, description in tests:
        result = test_api_endpoint(url, description)
        results.append((description, result))
        print()
    
    # Special test for monthly trends data structure
    monthly_trends_url = f"{base_url}/api/trends/monthly?category=all&start_date={start_date}&end_date={end_date}"
    trends_result = test_monthly_trends_data_structure(monthly_trends_url)
    results.append(("Monthly trends data structure", trends_result))
    print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for description, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {description}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"Total: {len(results)} tests, {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed! Check the errors above.")
        sys.exit(1)
    else:
        print("✅ All tests passed! Analytics API is working correctly.")
        sys.exit(0)

if __name__ == "__main__":
    main()
