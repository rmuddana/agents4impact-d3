import requests
from location import get_coordinates

def get_pollen_data(api_key, city, state, days=5):
    """
    Fetch pollen forecast data for given coordinates.
    
    Returns:
        Dictionary containing pollen forecast data
    """

    print(f"Fetching location data for location {city}, {state})")
    latitude, longitude = get_coordinates(city, state)
    print(f"Fetched location({latitude}, {longitude}) for city: {city}, state: {state}") 

    # API endpoint - note this is a GET request with query parameters
    url = "https://pollen.googleapis.com/v1/forecast:lookup"
    
    # Query parameters
    params = {
        "key": api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "days": min(days, 5)  # Max 5 days
    }
    
    # Make the GET request
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    # Display results
    print("\n" + "="*60)
    print("="*60)
    
    # Show region
    if "regionCode" in data:
        print(f"Region: {data['regionCode']}")
    
    for day in data.get("dailyInfo", []):
        date = day.get("date", {})
        date_str = f"{date.get('year')}-{date.get('month'):02d}-{date.get('day'):02d}"
        print(f"\n📅 {date_str}")
        
        # Pollen type info (grass, tree, weed)
        for pollen_type in day.get("pollenTypeInfo", []):
            name = pollen_type.get("displayName", "Unknown")
            in_season = pollen_type.get("inSeason", False)
            index = pollen_type.get("indexInfo", {})
            value = index.get("value", "N/A")
            category = index.get("category", "N/A")
            season_text = "🌱" if in_season else "❄️"
            print(f"   {season_text} {name}: {category} (Index: {value})")
        
        # Plant-specific pollen (if available)
        if "plantInfo" in day:
            print(f"   Specific Plants:")
            for plant in day["plantInfo"]:
                name = plant.get("displayName", "Unknown")
                in_season = plant.get("inSeason", False)
                index = plant.get("indexInfo", {})
                value = index.get("value", "N/A")
                category = index.get("category", "N/A")
                season_text = "🌱" if in_season else "❄️"
                print(f"     {season_text} {name}: {category} (Index: {value})")
    return data


#API_KEY = "AIzaSyBL9jG-kFKuEmlYQPLPbGHmNINkdVXTw4M"    
#city = "Austin"
#state = "Texas"
#pollen_data = get_pollen_data(API_KEY, city, state)
#print(pollen_data)
