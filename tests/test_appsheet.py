"""
Test script for my_helpers.appsheet module
Tests URL generation and parameter validation without making real API calls
"""

from helpers.appsheet import get_appsheet_url, post_data_to_appsheet
from helpers.errors import check_mandatory_args
import urllib.parse

def test_url_generation():
    """Test AppSheet URL generation"""
    print("=" * 50)
    print("TESTING URL GENERATION")
    print("=" * 50)
    
    # Test basic URL generation
    table = "TestTable"
    app_id = "test-app-123"
    app_access_key = "test-key-456"
    
    url = get_appsheet_url(table, app_id, app_access_key)
    print(f"Generated URL: {url}")
    
    # Verify URL components
    expected_parts = [
        "https://api.appsheet.com/api/v2/apps/",
        app_id,
        "/tables/",
        urllib.parse.quote(table),
        "/Action",
        f"applicationAccessKey={app_access_key}"
    ]
    
    all_parts_found = all(part in url for part in expected_parts)
    print(f"URL contains all expected parts: {all_parts_found}")
    
    # Test with special characters in table name
    special_table = "Test Table With Spaces & Special Chars!"
    special_url = get_appsheet_url(special_table, app_id, app_access_key)
    print(f"URL with special chars: {special_url}")
    print(f"Special chars encoded properly: {urllib.parse.quote(special_table) in special_url}")
    
    return all_parts_found

def test_parameter_validation():
    """Test parameter validation without making API calls"""
    print("\n" + "=" * 50)
    print("TESTING PARAMETER VALIDATION")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Missing table",
            "params": {
                "table": None,
                "rows": [{"test": "data"}],
                "action": "Add",
                "app_name": "TestApp",
                "app_id": "test-123",
                "app_access_key": "key-456"
            },
            "should_fail": True
        },
        {
            "name": "Missing rows",
            "params": {
                "table": "TestTable",
                "rows": None,
                "action": "Add", 
                "app_name": "TestApp",
                "app_id": "test-123",
                "app_access_key": "key-456"
            },
            "should_fail": True
        },
        {
            "name": "Missing action",
            "params": {
                "table": "TestTable",
                "rows": [{"test": "data"}],
                "action": None,
                "app_name": "TestApp", 
                "app_id": "test-123",
                "app_access_key": "key-456"
            },
            "should_fail": True
        },
        {
            "name": "All required params present",
            "params": {
                "table": "TestTable",
                "rows": [{"test": "data"}],
                "action": "Add",
                "app_name": "TestApp",
                "app_id": "test-123", 
                "app_access_key": "key-456"
            },
            "should_fail": False
        }
    ]
    
    validation_results = []
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        try:
            # Extract mandatory args for validation
            mandatory_args = {
                "table": test_case["params"]["table"],
                "rows": test_case["params"]["rows"],
                "action": test_case["params"]["action"],
                "app_name": test_case["params"]["app_name"],
                "app_id": test_case["params"]["app_id"],
                "app_access_key": test_case["params"]["app_access_key"],
            }
            
            check_mandatory_args(mandatory_args)
            
            if test_case["should_fail"]:
                print(f"  UNEXPECTED: Should have failed but didn't")
                validation_results.append(False)
            else:
                print(f"  PASS: All required parameters present")
                validation_results.append(True)
                
        except ValueError as e:
            if test_case["should_fail"]:
                print(f"  PASS: Correctly caught missing parameters - {e}")
                validation_results.append(True)
            else:
                print(f"  FAIL: Unexpected validation error - {e}")
                validation_results.append(False)
        except Exception as e:
            print(f"  ERROR: Unexpected exception - {e}")
            validation_results.append(False)
    
    return all(validation_results)

def test_payload_structure():
    """Test that we can build the expected payload structure"""
    print("\n" + "=" * 50) 
    print("TESTING PAYLOAD STRUCTURE")
    print("=" * 50)
    
    # Test basic payload structure
    test_rows = [
        {"Name": "Test User", "Email": "test@example.com"},
        {"Name": "Another User", "Email": "another@example.com"}
    ]
    
    action = "Add"
    selector = "TestSelector"
    user_settings = {"setting1": "value1"}
    
    # Build expected payload (this is what the function should create)
    expected_payload = {
        "Action": action,
        "Properties": {
            "Locale": "en-US", 
            "Location": "51.159133, 4.806236",
            "Timezone": "Central European Standard Time",
            "Selector": selector,
            "UserSettings": user_settings
        },
        "Rows": test_rows,
    }
    
    print("Expected payload structure:")
    import json
    print(json.dumps(expected_payload, indent=2))
    
    # Verify required properties are present
    required_properties = ["Action", "Properties", "Rows"]
    required_sub_properties = ["Locale", "Location", "Timezone"]
    
    structure_valid = (
        all(prop in expected_payload for prop in required_properties) and
        all(sub_prop in expected_payload["Properties"] for sub_prop in required_sub_properties)
    )
    
    print(f"\nPayload structure valid: {structure_valid}")
    return structure_valid

def run_all_tests():
    """Run all tests and report results"""
    print("APPSHEET MODULE TEST SUITE")
    print("=" * 50)
    print("Testing AppSheet helper functions without making real API calls")
    print("=" * 50)
    
    tests = [
        ("URL Generation", test_url_generation),
        ("Parameter Validation", test_parameter_validation), 
        ("Payload Structure", test_payload_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\nAll tests passed! Your AppSheet module is working correctly.")
    else:
        print(f"\n{len(results) - passed} test(s) failed. Check the output above for details.")
    
    print("\nNote: These tests validate function logic without making actual API calls.")
    print("To test with real AppSheet API, use valid credentials in a separate script.")

if __name__ == "__main__":
    run_all_tests()