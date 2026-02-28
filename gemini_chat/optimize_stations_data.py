import json
import csv
import os

def optimize_data():
    json_path = r'C:\SCIPE\my_maps\HCDPstations.json'
    csv_path = r'C:\SCIPE\my_maps\HCDPstations_compact.csv'
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    print(f"Reading {json_path}...")
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    stations = data.get('result', [])
    print(f"Processing {len(stations)} stations...")

    # Define fields to keep
    fields = ['skn', 'name', 'lat', 'lng', 'island', 'elevation_m']
    
    count = 0
    with open(csv_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fields)
        writer.writeheader()
        
        for entry in stations:
            val = entry.get('value', {})
            # Create a clean dictionary with only the requested fields
            row = {field: val.get(field) for field in fields}
            
            # Basic validation: must have an ID and coordinates
            if row['skn'] and row['lat'] and row['lng']:
                writer.writerow(row)
                count += 1

    print(f"Successfully saved {count} stations to {csv_path}")
    
    # Show file size comparison
    json_size = os.path.getsize(json_path) / (1024 * 1024)
    csv_size = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"File Size Reduced: {json_size:.2f} MB -> {csv_size:.2f} MB")

if __name__ == "__main__":
    optimize_data()
