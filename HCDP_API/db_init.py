import os
import json
import sqlite3

def init_db(json_path="station_rainfall_data.json", db_path="hcdp_stations.db"):
    """
    Initializes a local SQLite database from station data found in JSON.
    """
    if not os.path.exists(json_path):
        print(f"Error: Could not find {json_path}")
        return

    print(f"[*] Reading station data from {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    print(f"[*] Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute("DROP TABLE IF EXISTS hcd_stations")
    cursor.execute("""
        CREATE TABLE hcd_stations (
            skn REAL PRIMARY KEY,
            name TEXT,
            lat REAL,
            lng REAL
        )
    """)

    # Populate table
    count = 0
    for entry in data:
        if 'station_info' not in entry:
            continue
        info = entry['station_info']
        
        # Map JSON 'lon' to DB 'lng' as expected by station_finder.py
        cursor.execute("""
            INSERT INTO hcd_stations (skn, name, lat, lng)
            VALUES (?, ?, ?, ?)
        """, (info['skn'], info['name'], info['lat'], info['lon']))
        count += 1

    conn.commit()
    conn.close()
    print(f"[*] Success! Created 'hcd_stations' table with {count} records in {db_path}.")

if __name__ == "__main__":
    # Use paths relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_json = os.path.join(base_dir, "station_rainfall_data.json")
    target_db = os.path.join(base_dir, "hcdp_stations.db")
    
    init_db(target_json, target_db)
