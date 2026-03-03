# Code is generated with Gemini 3 Flash
"""
Takes a list of stations and creates a map with color-coded markers 
representing average rainfall. Currently uses output from fetch_station_data.py and 
map_HCDP_stations.py.
"""

import json
import folium
import branca.colormap as cm
import os
import numpy as np

# --- Configuration ---
INPUT_FILE = "station_rainfall_data.json"
OUTPUT_MAP = "average_rainfall_map.html"

def create_rainfall_map():
    """
    Processes station data to create a map with color-coded markers 
    representing average rainfall.
    """
    # 1. Load the data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run fetch_station_data.py first.")
        return

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    if not data:
        print("No station data found.")
        return

    # 2. Process Data: Calculate averages for each station
    stations_processed = []
    rainfall_values = []

    for entry in data:
        info = entry['station_info']
        api_res = entry['api_response']
        
        # Calculate average rainfall (skipping any error responses)
        if isinstance(api_res, dict) and "error" not in api_res:
            # Extract only the numerical values from the timeseries dictionary
            values = [v for v in api_res.values() if isinstance(v, (int, float))]
            if values:
                avg_rf = sum(values) / len(values)
                
                station_data = {
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'name': info['name'],
                    'skn': info['skn'],
                    'avg_rainfall': avg_rf
                }
                stations_processed.append(station_data)
                rainfall_values.append(avg_rf)

    if not stations_processed:
        print("No valid rainfall data found to visualize.")
        return

    # 3. Setup Visualization Components
    # Create a colormap for the markers (Drier = Yellow/Green, Wetter = Blue)
    min_rf = min(rainfall_values)
    max_rf = max(rainfall_values)
    colormap = cm.LinearColormap(
        colors=['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594'],
        index=np.linspace(min_rf, max_rf, 8),
        vmin=min_rf,
        vmax=max_rf,
        caption='Average Monthly Rainfall (mm)'
    )

    # 4. Initialize Map
    center_lat = np.mean([s['lat'] for s in stations_processed])
    center_lon = np.mean([s['lon'] for s in stations_processed])
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles='cartodbpositron')


    # 6. Add Color-coded CircleMarkers
    for s in stations_processed:
        popup_text = f"""
        <div style='font-family: Arial; font-size: 12px; width: 200px;'>
            <b>{s['name']}</b><br>
            SKN: {s['skn']}<br>
            <b>Avg Rainfall: {s['avg_rainfall']:.2f} mm</b>
        </div>
        """
        
        folium.CircleMarker(
            location=[s['lat'], s['lon']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=250),
            color='black',
            weight=1,
            fill=True,
            fill_color=colormap(s['avg_rainfall']),
            fill_opacity=0.9
        ).add_to(m)

    # 7. Add Colormap Legend and Save
    colormap.add_to(m)
    m.save(OUTPUT_MAP)
    print(f"Success! Map generated: {os.path.abspath(OUTPUT_MAP)}")

if __name__ == "__main__":
    create_rainfall_map()
