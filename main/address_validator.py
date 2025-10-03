"""
Address validation utility for iWashCars
Validates that customer addresses are within the service area (15 miles from 91602)
"""
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

logger = logging.getLogger(__name__)

# Service area configuration
SERVICE_AREA_ZIP = '91602'  # North Hollywood, CA
SERVICE_AREA_RADIUS_MILES = 15
SERVICE_AREA_COORDS = (34.1714, -118.4287)  # Approximate coordinates for 91602

# Geocoder configuration
geolocator = Nominatim(user_agent="iwashcars_booking", timeout=5)


def geocode_address(address, city, zip_code):
    """
    Geocode a full address to get latitude and longitude

    Args:
        address (str): Street address
        city (str): City name
        zip_code (str): ZIP code

    Returns:
        tuple: (latitude, longitude) or None if geocoding fails
    """
    try:
        # Build full address string
        full_address = f"{address}, {city}, {zip_code}, USA"

        logger.info(f"Geocoding address: {full_address}")
        location = geolocator.geocode(full_address)

        if location:
            logger.info(f"Geocoded to: {location.latitude}, {location.longitude}")
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode address: {full_address}")
            return None

    except GeocoderTimedOut:
        logger.error("Geocoding timed out")
        return None
    except GeocoderServiceError as e:
        logger.error(f"Geocoding service error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {str(e)}")
        return None


def calculate_distance_miles(coords1, coords2):
    """
    Calculate distance in miles between two coordinate pairs

    Args:
        coords1 (tuple): (latitude, longitude) of first location
        coords2 (tuple): (latitude, longitude) of second location

    Returns:
        float: Distance in miles
    """
    return geodesic(coords1, coords2).miles


def validate_service_area(address, city, zip_code):
    """
    Validate that an address is within the service area

    Args:
        address (str): Street address
        city (str): City name
        zip_code (str): ZIP code

    Returns:
        dict: {
            'valid': bool,
            'distance_miles': float or None,
            'message': str
        }
    """
    # Geocode the customer address
    customer_coords = geocode_address(address, city, zip_code)

    if not customer_coords:
        # If we can't geocode, try zip code validation as fallback
        return validate_zip_code_only(zip_code)

    # Calculate distance from service area center
    distance_miles = calculate_distance_miles(SERVICE_AREA_COORDS, customer_coords)

    # Check if within service radius
    if distance_miles <= SERVICE_AREA_RADIUS_MILES:
        return {
            'valid': True,
            'distance_miles': round(distance_miles, 2),
            'message': f'Address is within our service area ({round(distance_miles, 1)} miles from North Hollywood)'
        }
    else:
        return {
            'valid': False,
            'distance_miles': round(distance_miles, 2),
            'message': f'Sorry, this address is {round(distance_miles, 1)} miles away. We only service within {SERVICE_AREA_RADIUS_MILES} miles of North Hollywood (ZIP: {SERVICE_AREA_ZIP}).'
        }


def validate_zip_code_only(zip_code):
    """
    Fallback validation using only ZIP code
    Geocodes the ZIP code and checks distance

    Args:
        zip_code (str): ZIP code

    Returns:
        dict: Validation result
    """
    try:
        location = geolocator.geocode(f"{zip_code}, USA")

        if not location:
            # If we can't even geocode the ZIP, allow it (don't block customer)
            logger.warning(f"Could not validate ZIP code: {zip_code}")
            return {
                'valid': True,
                'distance_miles': None,
                'message': 'Could not verify distance. Proceeding with booking.'
            }

        zip_coords = (location.latitude, location.longitude)
        distance_miles = calculate_distance_miles(SERVICE_AREA_COORDS, zip_coords)

        if distance_miles <= SERVICE_AREA_RADIUS_MILES:
            return {
                'valid': True,
                'distance_miles': round(distance_miles, 2),
                'message': f'ZIP code is within our service area'
            }
        else:
            return {
                'valid': False,
                'distance_miles': round(distance_miles, 2),
                'message': f'Sorry, ZIP code {zip_code} is approximately {round(distance_miles, 1)} miles away. We only service within {SERVICE_AREA_RADIUS_MILES} miles of North Hollywood (ZIP: {SERVICE_AREA_ZIP}).'
            }

    except Exception as e:
        logger.error(f"ZIP code validation error: {str(e)}")
        # On error, allow the booking (don't block due to technical issues)
        return {
            'valid': True,
            'distance_miles': None,
            'message': 'Could not verify distance. Proceeding with booking.'
        }


def get_service_area_info():
    """
    Get information about the service area

    Returns:
        dict: Service area information
    """
    return {
        'center_zip': SERVICE_AREA_ZIP,
        'center_location': 'North Hollywood, CA',
        'radius_miles': SERVICE_AREA_RADIUS_MILES,
        'center_coords': SERVICE_AREA_COORDS
    }
