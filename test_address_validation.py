"""
Test address validation functionality
Tests the distance validation for service area (10 miles from 91602)
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwashcars.settings')
django.setup()

from main.address_validator import validate_service_area, get_service_area_info


def test_address_validation():
    """Test various addresses to verify validation"""
    print("=" * 70)
    print("ADDRESS VALIDATION TEST")
    print("=" * 70)

    # Get service area info
    service_info = get_service_area_info()
    print(f"\nService Area: {service_info['center_location']}")
    print(f"Center ZIP: {service_info['center_zip']}")
    print(f"Service Radius: {service_info['radius_miles']} miles")
    print(f"Center Coordinates: {service_info['center_coords']}")
    print("\n" + "=" * 70)

    # Test cases
    test_cases = [
        {
            'name': 'Within Service Area - North Hollywood',
            'address': '5230 Lankershim Blvd',
            'city': 'North Hollywood',
            'zip': '91601',
            'expected': True
        },
        {
            'name': 'Within Service Area - Studio City',
            'address': '4024 Radford Ave',
            'city': 'Studio City',
            'zip': '91604',
            'expected': True
        },
        {
            'name': 'Within Service Area - Van Nuys',
            'address': '6262 Van Nuys Blvd',
            'city': 'Van Nuys',
            'zip': '91401',
            'expected': True
        },
        {
            'name': 'Outside Service Area - Downtown LA',
            'address': '200 N Spring St',
            'city': 'Los Angeles',
            'zip': '90012',
            'expected': False
        },
        {
            'name': 'Outside Service Area - Santa Monica',
            'address': '1685 Main St',
            'city': 'Santa Monica',
            'zip': '90401',
            'expected': False
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        print(f"Address: {test_case['address']}, {test_case['city']}, {test_case['zip']}")

        result = validate_service_area(
            test_case['address'],
            test_case['city'],
            test_case['zip']
        )

        print(f"Valid: {result['valid']}")
        print(f"Distance: {result['distance_miles']} miles" if result['distance_miles'] else "Distance: Could not calculate")
        print(f"Message: {result['message']}")

        # Check if result matches expectation
        if result['valid'] == test_case['expected']:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL - Expected valid={}, got valid={}".format(
                test_case['expected'], result['valid']
            ))
            failed += 1

        print("-" * 70)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {len(test_cases)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("=" * 70)


def test_zip_code_91602():
    """Test the base location (91602) should always be valid"""
    print("\n" + "=" * 70)
    print("BASE LOCATION TEST (91602)")
    print("=" * 70)

    result = validate_service_area(
        "5230 Lankershim Blvd",
        "North Hollywood",
        "91602"
    )

    print(f"Address: 5230 Lankershim Blvd, North Hollywood, 91602")
    print(f"Valid: {result['valid']}")
    print(f"Distance: {result['distance_miles']} miles" if result['distance_miles'] else "Distance: N/A")
    print(f"Message: {result['message']}")

    if result['valid']:
        print("\n✅ Base location test PASSED - ZIP 91602 is within service area")
    else:
        print("\n❌ Base location test FAILED - ZIP 91602 should always be valid!")

    print("=" * 70)


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ADDRESS VALIDATION TEST SUITE" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    # Test base location first
    test_zip_code_91602()

    # Test various addresses
    test_address_validation()

    print("\n📝 NOTE:")
    print("   - Distance calculations use geodesic (straight-line) distance")
    print("   - Actual driving distance may vary")
    print("   - Geocoding uses OpenStreetMap (Nominatim)")
    print("   - Results may take a few seconds per address")
    print()
