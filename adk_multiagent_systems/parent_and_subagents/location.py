import requests

def get_coordinates(city: str, state: str) -> tuple[float | None, float | None]:
    """
    Gets the latitude and longitude for a given city and state using the Nominatim API.

    Args:
        city: The name of the city.
        state: The two-letter state abbreviation (e.g., "CA").

    Returns:
        A tuple containing the latitude and longitude, or (None, None) if not found.
    """
    # Define the API endpoint and parameters
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'city': city,
        'state': state,
        'format': 'json',
        'limit': 1
    }
    
    # It's good practice to set a custom User-Agent for API calls
    headers = {
        'User-Agent': 'HealthAndWellnessAgent/1.0'
    }

    try:
        # Make the API request
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # If we received data, extract the latitude and longitude from the first result
        if data:
            latitude = float(data[0]['lat'])
            longitude = float(data[0]['lon'])
            print(f"Successfully found coordinates for {city}, {state}: ({latitude}, {longitude})")
            return latitude, longitude
        else:
            print(f"Could not find coordinates for {city}, {state}.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the API request: {e}")
        return None, None
