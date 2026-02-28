"""
Finds stations within a given km radius and latitude/longitude coordinates.
"""

import pandas as pd
import sqlite3
import math

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on the Earth (specified in decimal degrees) in kilometers.
    """
    R = 6371  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_nearby_stations(target_lat, target_lon, radius_km, db_path=r'C:\SCIPE\my_maps\my_database.db'):
    """
    Finds stations within a given radius using a bounding box pre-filter and Haversine distance.
    Returns a Pandas DataFrame of results.
    """
    conn = sqlite3.connect(db_path)
    
    # 1. Calculate Bounding Box (Pre-filter)
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * math.cos(math.radians(target_lat)))
    
    lat_min, lat_max = target_lat - lat_delta, target_lat + lat_delta
    lon_min, lon_max = target_lon - lon_delta, target_lon + lon_delta

    # 2. Query Database
    query_spatial = """
    SELECT skn, name, lat, lng 
    FROM hcd_stations 
    WHERE lat BETWEEN ? AND ? 
      AND lng BETWEEN ? AND ?
    """
    df_spatial = pd.read_sql_query(query_spatial, conn, params=(lat_min, lat_max, lon_min, lon_max))
    conn.close()

    if df_spatial.empty:
        return pd.DataFrame()

    # 3. Refine with Exact Haversine Distance
    df_spatial['distance_km'] = df_spatial.apply(
        lambda row: haversine(target_lat, target_lon, row['lat'], row['lng']), 
        axis=1
    )
    
    # Filter and sort
    df_result = df_spatial[df_spatial['distance_km'] <= radius_km].sort_values('distance_km')
    return df_result

if __name__ == "__main__":
    # --- Configuration ---
    target_lat, target_lon = 19.6728, -156.0203
    radius_km = 10.0

    # Set Pandas options for CLI display
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    results = get_nearby_stations(target_lat, target_lon, radius_km)
    
    if not results.empty:
        print(f"Stations within {radius_km}km of ({target_lat}, {target_lon}):")
        print(results.to_string())
    else:
        print(f"No stations found within {radius_km}km of ({target_lat}, {target_lon}).")

