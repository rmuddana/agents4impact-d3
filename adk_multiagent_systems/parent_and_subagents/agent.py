import os
import sys
import logging

sys.path.append("..")
from callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
import google.cloud.logging
from google.adk import Agent
from google.genai import types
from typing import Optional, List, Dict

from google.adk.tools.tool_context import ToolContext
from location import get_coordinates

load_dotenv()

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

# Tools (add the tool here when instructed)


def get_pollen_data(api_key: str, city: str, state: str, days=5: int) -> dict:
    """
    Fetch pollen forecast data for given city, state and past days.

    Returns:
        Dictionary containing pollen data
    """

    #print(f"Fetching location data for location {city}, {state})")
    latitude, longitude = get_coordinates(city, state)
    #print(f"Fetched location({latitude}, {longitude}) for city: {city}, state: {state}")

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
    #print("\n" + "="*60)
    #print("="*60)

    # Show region
#    if "regionCode" in data:
#        print(f"Region: {data['regionCode']}")

    for day in data.get("dailyInfo", []):
        date = day.get("date", {})
        date_str = f"{date.get('year')}-{date.get('month'):02d}-{date.get('day'):02d}"
        #print(f"\n📅 {date_str}")

        # Pollen type info (grass, tree, weed)
        #for pollen_type in day.get("pollenTypeInfo", []):
        #    name = pollen_type.get("displayName", "Unknown")
        #    in_season = pollen_type.get("inSeason", False)
        #    index = pollen_type.get("indexInfo", {})
        #    value = index.get("value", "N/A")
        #    category = index.get("category", "N/A")
        #    season_text = "🌱" if in_season else "❄️"
        #    #print(f"   {season_text} {name}: {category} (Index: {value})")

        # Plant-specific pollen (if available)
        #if "plantInfo" in day:
        #    print(f"   Specific Plants:")
        #    for plant in day["plantInfo"]:
        #        name = plant.get("displayName", "Unknown")
        #        in_season = plant.get("inSeason", False)
        #        index = plant.get("indexInfo", {})
        #        value = index.get("value", "N/A")
        #        category = index.get("category", "N/A")
        #        season_text = "🌱" if in_season else "❄️"
        #        print(f"     {season_text} {name}: {category} (Index: {value})")
    return data


def save_attractions_to_state(
    tool_context: ToolContext,
    attractions: List[str]
) -> dict[str, str]:
    """Saves the list of attractions to state["attractions"].

    Args:
        attractions [str]: a list of strings to add to the list of attractions

    Returns:
        None
    """
    # Load existing attractions from state. If none exist, start an empty list
    existing_attractions = tool_context.state.get("attractions", [])

    # Update the 'attractions' key with a combo of old and new lists.
    # When the tool is run, ADK will create an event and make
    # corresponding updates in the session's state.
    tool_context.state["attractions"] = existing_attractions + attractions

    # A best practice for tools is to return a status message in a return dict
    return {"status": "success"}

# Agents

attractions_planner = Agent(
    name="attractions_planner",
    model=os.getenv("MODEL"),
    description="Build a list of attractions to visit in a country.",
    instruction="""
        - Provide the user options for attractions to visit within their selected country.
        - When they reply, use your tool to save their selected attraction
        and then provide more possible attractions.
        - If they ask to view the list, provide a bulleted list of
        { attractions? } and then suggest some more.
        """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    # When instructed to do so, paste the tools parameter below this line
    tools=[save_attractions_to_state]
    )

travel_brainstormer = Agent(
    name="travel_brainstormer",
    model=os.getenv("MODEL"),
    description="Help a user decide what country to visit.",
    instruction="""
        Provide a few suggestions of popular countries for travelers.

        Help a user identify their primary goals of travel:
        adventure, leisure, learning, shopping, or viewing art

        Identify countries that would make great destinations
        based on their priorities.
        """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)

root_agent = Agent(
    name="steering",
    model=os.getenv("MODEL"),
    description="Start a user on health and wellness advisory.",
    instruction="""
        Ask user for city and state, and then fetch pollen data.
        Then answer queries asked by user related to pollen and allergies.
        """,
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
    ),
    # Add the sub_agents parameter when instructed below this line
    tools=[get_pollen_data],
    sub_agents=[travel_brainstormer, attractions_planner],
)
