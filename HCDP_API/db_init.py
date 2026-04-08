import os
import csv
import sqlite3

def init_db(source_path="master_stations.csv", db_path="hcdp_stations.db"):
    """
    Initializes a local SQLite database from station data (CSV or JSON).
    """
    if not os.path.exists(source_path):
        print(f"Error: Could not find {source_path}")
        return

    print(f"[*] Reading station data from {source_path}...")
    
    stations = []
    
    # Handle CSV (New Master Format)
    if source_path.endswith('.csv'):
        with open(source_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stations.append({
                    'skn': float(row['skn']),
                    'name': row['name'],
                    'lat': float(row['lat']),
                    'lng': float(row['lng'])
                })
    # Handle JSON (Legacy Rainfall Results Format)
    elif source_path.endswith('.json'):
        with open(source_path, 'r') as f:
            data = json.load(f)
            for entry in data:
                if 'station_info' in entry:
                    info = entry['station_info']
                    stations.append({
                        'skn': info['skn'],
                        'name': info['name'],
                        'lat': info['lat'],
                        'lng': info.get('lon') or info.get('lng')
                    })

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

    # Create spatial indices
    cursor.execute("CREATE INDEX idx_lat ON hcd_stations(lat)")
    cursor.execute("CREATE INDEX idx_lng ON hcd_stations(lng)")

    # Populate table
    count = 0
    for s in stations:
        cursor.execute("""
            INSERT INTO hcd_stations (skn, name, lat, lng)
            VALUES (?, ?, ?, ?)
        """, (s['skn'], s['name'], s['lat'], s['lng']))
        count += 1

    conn.commit()
    conn.close()
    print(f"[*] Success! Created 'hcd_stations' table with {count} records in {db_path}.")

if __name__ == "__main__":
    # Use paths relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try CSV first (new source), then fall back to JSON
    source_csv = os.path.join(base_dir, "master_stations.csv")
    source_json = os.path.join(base_dir, "station_rainfall_data.json")
    
    target_db = os.path.join(base_dir, "hcdp_stations.db")
    
    if os.path.exists(source_csv):
        init_db(source_csv, target_db)
    else:
        init_db(source_json, target_db)
