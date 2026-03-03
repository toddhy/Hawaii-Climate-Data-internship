# Code is generated with Gemini 3 Flash
"""
Takes lat and long coordinates and a radius in km. Runs a query to HCDP API with chosen parameters 
in the function fetch_rainfall_data(). Returns results to a json file.
"""

import json
import requests
import time
import os
from dotenv import load_dotenv
from station_finder import get_nearby_stations

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
TARGET_LAT = 19.6728
TARGET_LON = -156.0203
RADIUS_KM = 10.0
OUTPUT_FILE = "station_rainfall_data.json"

# API Settings (Token should be set in environment variable HCDP_API_TOKEN)
API_URL = "https://api.hcdp.ikewai.org/raster/timeseries"
AUTH_TOKEN = os.getenv("HCDP_API_TOKEN")

def fetch_rainfall_data(lat, lon):
    """
    Fetches rainfall timeseries data for a single coordinate from the HCDP API.
    """
    # Parameters based on your CURL example
    params = {
        'location': 'hawaii',
        'start': '2008-01',
        'end': '2022-12',
        'lat': lat,
        'lng': lon,
        'datatype': 'rainfall',
        'extent': 'bi',
        'production': 'new',
        'period': 'month'
    }
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }

    try:
        # Perform the GET request (equivalent to your CURL command)
        response = requests.get(API_URL, params=params, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data for ({lat}, {lon}): HTTP {response.status_code}")
            return {"error": f"HTTP {response.status_code}", "detail": response.text}
            
    except Exception as e:
        print(f"Exception for ({lat}, {lon}): {str(e)}")
        return {"error": "Exception", "detail": str(e)}

def main():
    # 0. Check for API Token
    if not AUTH_TOKEN:
        print("Error: HCDP_API_TOKEN environment variable is not set.")
        print("Please set it using: $env:HCDP_API_TOKEN = 'your_token_here'")
        return

    # 1. Get the list of stations from our station_finder module
    print(f"Searching for stations within {RADIUS_KM}km of ({TARGET_LAT}, {TARGET_LON})...")
    stations_df = get_nearby_stations(TARGET_LAT, TARGET_LON, RADIUS_KM)
    
    if stations_df.empty:
        print("No stations found in range.")
        return

    print(f"Found {len(stations_df)} stations. Starting data fetch...")
    
    all_results = []

    # 2. Loop through each station found
    for index, row in stations_df.iterrows():
        station_name = row['name']
        lat = row['lat']
        lon = row['lng']
        skn = row['skn']
        
        print(f"[{index+1}/{len(stations_df)}] Fetching data for {station_name} (SKN: {skn})...")
        
        # Fetch the data
        data = fetch_rainfall_data(lat, lon)
        
        # Package the result with some metadata for easier checking
        result_entry = {
            "station_info": {
                "skn": skn,
                "name": station_name,
                "lat": lat,
                "lon": lon,
                "distance_km": row['distance_km']
            },
            "api_response": data
        }
        
        all_results.append(result_entry)
        
        # Brief pause to be polite to the API
        time.sleep(0.5)

    # 3. Write everything to a file
    print(f"Saving results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=4)
        
    print("Done! You can now check the output file.")

if __name__ == "__main__":
    main()
