# Code is generated with Gemini 3 Flash
"""
This script creates an interactive map of HCDP weather stations using Folium. Takes json file as input
and outputs an html map file. Uses output from fetch_station_data.py.
"""

import json
import folium
import os

# --- Configuration ---
INPUT_FILE = "station_rainfall_data.json"
OUTPUT_MAP = "station_map.html"

def create_station_map():
    """
    Reads station data from JSON and creates an interactive Folium map.
    """
    # 1. Load the data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run fetch_station_data.py first.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    if not data:
        print("No station data found in the file.")
        return

    # 2. Initialize the map
    # We'll center the map on the first station's coordinates
    first_station = data[0]['station_info']
    m = folium.Map(
        location=[first_station['lat'], first_station['lon']], 
        zoom_start=12,
        tiles='cartodbpositron' # Clean, modern map style
    )

    print(f"Adding {len(data)} stations to the map...")

    # 3. Add markers for each station
    for entry in data:
        info = entry['station_info']
        lat = info['lat']
        lon = info['lon']
        name = info['name']
        skn = info['skn']
        dist = info['distance_km']

        # Create a popup with station details
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px;">
            <b>{name}</b><br>
            SKN: {skn}<br>
            Distance: {dist:.2f} km<br>
            Lat/Lon: {lat:.5f}, {lon:.5f}
        </div>
        """
        
        # Add a circular marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            popup=folium.Popup(popup_html, max_width=250),
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
            fill_opacity=0.7
        ).add_to(m)

    # 4. Save the map
    m.save(OUTPUT_MAP)
    print(f"Success! Map saved to: {os.path.abspath(OUTPUT_MAP)}")

if __name__ == "__main__":
    create_station_map()
