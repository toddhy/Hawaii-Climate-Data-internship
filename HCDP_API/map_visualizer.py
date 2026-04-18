"""
Unified Rainfall Map Generator

This script creates an interactive Folium map that combines:
1. Weather station markers (colored by average rainfall from JSON, or grey location markers).
2. A raster (gridded) rainfall overlay (aggregated from TIFF files in the downloads directory).

Usage:
    python unified_rainfall_map.py [--json PATH] [--tiff_dir DIR] [--output FILENAME]
                                   [--lat LAT] [--lon LON] [--radius KM] [--no_json]

Notes:
- This script DOES NOT download new data. It only processes existing local files.
- Use --no_json to omit station rainfall data and just map station locations (markers will be grey).
- If JSON or TIFF data is missing, the script will attempt to fall back to available data.
"""
import os
import glob
import json
import math
import numpy as np
import rasterio
from rasterio.transform import xy
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from folium.raster_layers import ImageOverlay
import branca
import argparse
import pandas as pd
import sys

# Add project root to path so we can import from database folder
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from .station_finder import get_nearby_stations
except ImportError:
    from station_finder import get_nearby_stations


# --- Configuration ---
DEFAULT_JSON = "station_rainfall_data.json"
DEFAULT_TIFF_DIR = "downloads"
OUTPUT_MAP = "unified_rainfall_map.html"

def get_station_data(json_path):
    """
    Extracts and averages station rainfall data from JSON.
    Returns a list of dicts with lat, lon, name, skn, and avg_rainfall.
    """
    if not json_path or not os.path.exists(json_path):
        return []

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        stations = []
        for entry in data:
            if 'station_info' not in entry or 'api_response' not in entry:
                continue
            info = entry['station_info']
            api_res = entry['api_response']
            if isinstance(api_res, dict) and "error" not in api_res:
                values = [v for v in api_res.values() if isinstance(v, (int, float))]
                if values:
                    avg_rf = sum(values) / len(values)
                    stations.append({
                        'lat': info['lat'], 'lon': info['lon'],
                        'name': info['name'], 'skn': info['skn'],
                        'avg_rainfall': avg_rf
                    })
        return stations
    except Exception as e:
        print(f"Warning: Error reading JSON station data: {e}")
        return []

def get_location_only_stations(lat, lon, radius_km):
    """
    Fetches station locations using station_finder without rainfall data.
    """
    print(f"Fetching station locations within {radius_km}km of ({lat}, {lon})...")
    df = get_nearby_stations(lat, lon, radius_km)
    if df.empty:
        return []
    
    stations = []
    for _, row in df.iterrows():
        stations.append({
            'lat': row['lat'], 'lon': row['lng'],
            'name': row['name'], 'skn': row['skn'],
            'avg_rainfall': None # No rainfall data
        })
    return stations

def haversine_dist(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the earth.
    Can accept numpy arrays.
    """
    R = 6371.0  # Earth radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def mask_raster_to_circle(data, meta, center_lat, center_lon, radius_km):
    """
    Masks raster data to a circular area using Haversine distance.
    """
    rows, cols = data.shape
    transform = meta['transform']
    
    # Generate meshgrid of row/col indices
    r_idx, c_idx = np.meshgrid(np.arange(rows), np.arange(cols), indexing='ij')
    
    # Convert to coordinates (lon, lat) using the transform
    # transform is (a, b, c, d, e, f) where x = a*col + b*row + c, y = d*col + e*row + f
    # Rasterio transform: (res_x, shear_x, x_min, shear_y, res_y, y_max)
    # x = transform[0] * c + transform[1] * r + transform[2]
    # y = transform[3] * c + transform[4] * r + transform[5]
    
    lons = transform[0] * c_idx + transform[1] * r_idx + transform[2]
    lats = transform[3] * c_idx + transform[4] * r_idx + transform[5]
    
    # Calculate distance for all pixels
    dist = haversine_dist(center_lat, center_lon, lats, lons)
    
    masked_data = data.copy()
    masked_data[dist > radius_km] = np.nan
    return masked_data

def process_tiffs(tiff_dir, start_date=None, end_date=None):
    """
    Aggregates TIFF files and returns data + metadata for overlay.
    Filters by date range (YYYY-MM) if provided.
    """
    tiff_files = glob.glob(os.path.join(tiff_dir, "*.tiff"))
    if not tiff_files:
        return None, None, None
    
    # Filter by date range
    if start_date or end_date:
        filtered_files = []
        for f in tiff_files:
            date_str = os.path.splitext(os.path.basename(f))[0]
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            filtered_files.append(f)
        tiff_files = filtered_files
        
    if not tiff_files:
        print(f"No TIFF files found within the range {start_date} to {end_date}.")
        return None, None, None

    print(f"Processing {len(tiff_files)} TIFF files...")
    aggregated_data = None
    meta = None
    count = 0

    for tiff_path in tiff_files:
        try:
            with rasterio.open(tiff_path) as src:
                data = src.read(1).astype(float)
                if src.nodata is not None:
                    data[data == src.nodata] = np.nan
                
                if aggregated_data is None:
                    aggregated_data = data
                    meta = src.meta
                else:
                    if data.shape != aggregated_data.shape:
                        print(f"Warning: Skipping {os.path.basename(tiff_path)} - shape {data.shape} does not match {aggregated_data.shape}")
                        continue
                    aggregated_data = np.nansum([aggregated_data, data], axis=0)
                count += 1
        except Exception as e:
            print(f"Warning: Could not process {os.path.basename(tiff_path)}: {e}")
            continue

    if aggregated_data is not None:
        aggregated_data /= count
    
    with rasterio.open(tiff_files[0]) as src:
        bounds = src.bounds
        folium_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
    
    return aggregated_data, folium_bounds, meta

def process_tiledb(data_type, start_date=None, end_date=None, array_uri=None):
    """
    Aggregates data from TileDB and returns data + metadata for overlay.
    """
    # Deferred import to prevent 'Illegal Instruction' crash on systems without AVX
    from database.tiledb_access import get_raster_for_date_range

    if array_uri is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        db_dir = os.path.join(project_root, "database")
        
        array_name_map = {
            'rainfall': 'rainfall_array',
            'temperature': 'temperature_array',
            'min_temp': 'min_temp_array',
            'max_temp': 'max_temp_array',
            'spi': 'spi_array'
        }
        
        if data_type not in array_name_map:
            return None, None, None
            
        array_uri = os.path.join(db_dir, array_name_map[data_type])

    if not os.path.exists(array_uri):
        print(f"TileDB array not found at {array_uri}")
        return None, None, None
        
    # All mapping currently expects 'mean' (average monthly values)
    # Note: For rainfall this might be 'sum' if aggregating multiple days/months, 
    # but 'mean' is used hereafter for unified range calculation.
    aggregation = 'sum' if data_type == 'rainfall' else 'mean'
    
    print(f"Processing data from TileDB array: {os.path.basename(array_uri)}...")
    try:
        data, bounds, meta = get_raster_for_date_range(array_uri, start_date, end_date, aggregation)
        return data, bounds, meta
    except Exception as e:
        print(f"Error processing TileDB: {e}")
        return None, None, None

def create_unified_map(json_path, tiff_dir=None, output_file=OUTPUT_MAP, center_lat=None, center_lon=None, radius_km=None, omit_json_data=False, add_stations=False, statewide=False, data_type='rainfall', start_date=None, end_date=None, array_uri=None):



    """
    Creates a map with both raster overlay and station markers.
    """
    print(f"Loading {data_type} data...")
    
    # Set default tiff_dir based on data_type if not provided
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if tiff_dir is None:
        if data_type == 'temperature':
            tiff_dir = os.path.join(script_dir, "monthly_temperature")
        elif data_type == 'max_temp':
            tiff_dir = os.path.join(script_dir, "monthly_max_temperature")
        elif data_type == 'min_temp':
            tiff_dir = os.path.join(script_dir, "monthly_min_temperature")
        elif data_type == 'spi':
            tiff_dir = os.path.join(script_dir, "spi")
        else:
            tiff_dir = os.path.join(script_dir, "monthly_rainfall")

    # Handle json_path default if it's the standard filename
    if json_path == DEFAULT_JSON:
        json_path = os.path.join(script_dir, DEFAULT_JSON)

    if not os.path.exists(tiff_dir):
        print(f"Warning: Directory '{tiff_dir}' does not exist.")


    
    # 1. Background context for center/radius if not provided
    # Fallback default (Honolulu)
    default_lat, default_lon = 21.3069, -157.8583
    
    # 2. Try to get station data (with rainfall)
    stations_with_data = []
    if not omit_json_data and json_path:
        stations_with_data = get_station_data(json_path)

    # 3. Process Data (TileDB first, then TIFFs)
    raster_data, raster_bounds, raster_meta = process_tiledb(data_type, start_date, end_date, array_uri)
    
    if raster_data is None:
        print("Falling back to TIFF processing...")
        raster_data, raster_bounds, raster_meta = process_tiffs(tiff_dir, start_date, end_date)

    # 4. Determine Area of Interest
    if center_lat and center_lon:
        center = [center_lat, center_lon]
    elif stations_with_data:
        center = [np.mean([s['lat'] for s in stations_with_data]), np.mean([s['lon'] for s in stations_with_data])]
    elif raster_bounds:
        center = [(raster_bounds[0][0] + raster_bounds[1][0]) / 2, (raster_bounds[0][1] + raster_bounds[1][1]) / 2]
    else:
        center = [default_lat, default_lon]

    if statewide and not (center_lat and center_lon):
        if raster_bounds:
            center = [(raster_bounds[0][0] + raster_bounds[1][0]) / 2, (raster_bounds[0][1] + raster_bounds[1][1]) / 2]
        else:
            center = [20.4, -157.4] # General Hawaii maritime center

    if radius_km is None:
        if statewide:
            radius_km = 500.0 # Large enough for all islands
        else:
            radius_km = 5.0 # Default radius if not specified

    # 5. Spatially Filter Stations and Merge Results
    print(f"[*] Spatial Search: center={center}, radius={radius_km:.2f}km")
    
    # A. Filter JSON stations spatially
    spatially_filtered_json = []
    for s in stations_with_data:
        dist = haversine_dist(center[0], center[1], s['lat'], s['lon'])
        if dist <= radius_km:
            spatially_filtered_json.append(s)
            
    # B. Fetch all local station locations via station_finder
    local_stations = get_location_only_stations(center[0], center[1], radius_km)
    
    # C. Merge Logic: JSON data takes priority for the same 'skn'
    # Use a dict keyed by skn to merge
    merged_map = {s['skn']: s for s in local_stations}
    for s in spatially_filtered_json:
        merged_map[s['skn']] = s 
        
    final_stations = list(merged_map.values())
    
    if not final_stations and not omit_json_data and stations_with_data:
        print("[!] Warning: Found JSON stations but none were within the search radius.")

    if not final_stations and raster_data is None:
        print("No data found to map (Stations or Raster).")
        return

    print(f"Masking raster to {radius_km:.2f}km radius around {center}...") if not statewide else print("Statewide mode: skipping raster masking.")
    
    zoom = 7 if statewide else 9
    m = folium.Map(location=center, zoom_start=zoom, tiles='cartodbpositron')

    # Mask the raster data
    if raster_data is not None and not statewide:
        raster_data = mask_raster_to_circle(raster_data, raster_meta, center[0], center[1], radius_km)


    # Define Unified Colormap based on data type and LOCAL range
    if data_type == 'temperature' or data_type == 'min_temp' or data_type == 'max_temp':
        colors = ['#ffffcc', '#ffeb99', '#ffcc66', '#ff9933', '#ff6600', '#ff3300', '#cc0000', '#990000']
        caption = f"Average Monthly {data_type.replace('_', ' ').capitalize()} (°C)"
    elif data_type == 'spi':
        # Diverging RdYlBu (Red for dry, Blue for wet)
        colors = ['#a50026', '#d73027', '#f46d43', '#fdae61', '#fee090', '#ffffbf', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695']
        caption = "Standardized Precipitation Index (SPI)"
    else:
        colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594']
        caption = "Average Monthly Rainfall (mm)"
    
    # Calculate LOCAL range for normalization
    vals = []
    has_rainfall_data = False
    for s in final_stations:
        if s['avg_rainfall'] is not None:
            d = haversine_dist(center[0], center[1], s['lat'], s['lon'])
            if d <= radius_km:
                vals.append(s['avg_rainfall'])
                has_rainfall_data = True
    
    if raster_data is not None:
        r_min, r_max = np.nanmin(raster_data), np.nanmax(raster_data)
        if not np.isnan(r_min): vals.append(r_min)
        if not np.isnan(r_max): vals.append(r_max)
    
    if not vals:
        vmin, vmax = 0, 100
    else:
        vmin, vmax = min(vals), max(vals)

    print(f"Color range (relative): {vmin:.2f} to {vmax:.2f}")
    colormap = branca.colormap.LinearColormap(colors=colors, vmin=vmin, vmax=vmax, caption=caption)

    # 1. Add Raster Overlay
    if raster_data is not None:
        print("Adding raster overlay...")
        cmap = mcolors.LinearSegmentedColormap.from_list("hcdp", colors)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colored_data = cmap(norm(raster_data))
        colored_data[np.isnan(raster_data), 3] = 0
        
        plt.imsave("temp_unified.png", colored_data)
        ImageOverlay(image="temp_unified.png", bounds=raster_bounds, opacity=0.6, interactive=True, zindex=1).add_to(m)

    # 2. Add Station Markers
    if add_stations:
        if final_stations:
            print(f"[*] Adding {len(final_stations)} station markers to the map...")
            station_group = folium.FeatureGroup(name="Weather Stations").add_to(m)
        for s in final_stations:
            if s['avg_rainfall'] is not None:
                unit = "mm" if data_type == 'rainfall' else ""
                popup_text = f"<b>{s['name']}</b><br>SKN: {s['skn']}<br>Avg {data_type.capitalize()}: {s['avg_rainfall']:.2f} {unit}"
                f_color = colormap(s['avg_rainfall'])
            else:
                popup_text = f"<b>{s['name']}</b><br>SKN: {s['skn']}<br>(No {data_type} data loaded)"
                f_color = '#666666' # Grey for location-only
            
            folium.CircleMarker(
                location=[s['lat'], s['lon']],
                radius=6,
                popup=folium.Popup(popup_text, max_width=200),
                color='black', weight=1, fill=True,
                fill_color=f_color,
                fill_opacity=0.9
            ).add_to(station_group)

    # Add Circle for visualization of the mask area
    if add_stations and not statewide:
        folium.Circle(
            location=center,
            radius=radius_km * 1000,
            color='blue',
            weight=1,
            fill=False,
            dash_array='5, 5'
        ).add_to(m)




    # Add Layer Control and Legend
    folium.LayerControl().add_to(m)
    colormap.add_to(m)
    
    m.save(output_file)
    print(f"Success! Unified map generated: {os.path.abspath(output_file)}")
    if os.path.exists("temp_unified.png"):
        os.remove("temp_unified.png")

def main():
    parser = argparse.ArgumentParser(description="Create a unified HCDP map (Stations + Raster).")
    parser.add_argument("--type", choices=['rainfall', 'temperature', 'spi', 'min_temp', 'max_temp'], default='rainfall', help="Data type to map (default: rainfall)")
    parser.add_argument("--json", default=DEFAULT_JSON, help=f"Station JSON file (default: {DEFAULT_JSON})")
    parser.add_argument("--tiff_dir", help="Directory with TIFFs (defaults to monthly_rainfall or monthly_temperature)")
    parser.add_argument("--array_uri", help="Path to a specific TileDB array to use as the raster source")
    parser.add_argument("--output", default=OUTPUT_MAP, help=f"Output file (default: {OUTPUT_MAP})")

    parser.add_argument("--lat", type=float, help="Center latitude for clipping")
    parser.add_argument("--lon", type=float, help="Center longitude for clipping")
    parser.add_argument("--radius", type=float, help="Radius in km for clipping")
    parser.add_argument("--no_json", action="store_true", help="Omit station rainfall JSON and just map locations")
    parser.add_argument("--add_stations", action="store_true", help="Include station markers on the map (default: False)")
    parser.add_argument("--statewide", action="store_true", help="Map the entire state (ignores radius clipping, default: False)")
    
    parser.add_argument("--start_date", help="Start date (YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--end_date", help="End date (YYYY-MM or YYYY-MM-DD)")
    
    args = parser.parse_args()
    create_unified_map(args.json, args.tiff_dir, args.output, args.lat, args.lon, args.radius, args.no_json, args.add_stations, args.statewide, args.type, args.start_date, args.end_date, args.array_uri)



if __name__ == "__main__":
    main()
