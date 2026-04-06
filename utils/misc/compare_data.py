import sys
import os
import json
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = r"c:\SCIPE\HCDP-data-for-AI"
sys.path.append(PROJECT_ROOT)

from database.tiledb_access import get_metadata, get_data_for_month

def compare(lat, lon, month):
    array_uri = os.path.join(PROJECT_ROOT, "database", "rainfall_array")
    meta = get_metadata(array_uri)
    transform = meta["transform"]
    a, b, c, d, e, f = transform
    
    col = int((lon - c) / a)
    row = int((lat - f) / e)
    
    # Raster value
    data = get_data_for_month(array_uri, month)
    raster_val = data[row, col]
    
    print(f"--- Comparison for {month} at ({lat}, {lon}) ---")
    print(f"Grid Pixel (Row {row}, Col {col}) Value: {raster_val} mm")
    
    # Station Data
    json_path = os.path.join(PROJECT_ROOT, "HCDP_API", "station_rainfall_data.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f_json:
            stations = json.load(f_json)
            for s in stations:
                # Find station closest to these coordinates
                s_lat = s['station_info']['lat']
                s_lon = s['station_info']['lon']
                dist = np.sqrt((s_lat - lat)**2 + (s_lon - lon)**2)
                if dist < 0.01: # Roughly 1km
                    resp = s.get('api_response', {})
                    # The JSON structure seems to use ISO strings or something
                    for k, v in resp.items():
                        if k.startswith(month):
                            print(f"Station {s['station_info']['skn']} ({s['station_info']['name']}) Value: {v} mm")

if __name__ == "__main__":
    # Honolulu example
    compare(21.3069, -157.8583, "1995-01")
    compare(21.3069, -157.8583, "2025-01")
