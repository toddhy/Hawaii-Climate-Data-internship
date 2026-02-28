import pandas as pd
import sqlite3

# Set Pandas options to display all rows and columns without truncation
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Create a connection to the SQLite database
conn = sqlite3.connect(r'C:\SCIPE\my_maps\my_database.db')

# Read CSV data into a Pandas DataFrame
df = pd.read_csv(r'C:\SCIPE\my_maps\HCDPstations_compact.csv')

# Write the DataFrame to a table in the SQLite database
df.to_sql('hcd_stations', conn, if_exists='replace', index=False)
'''
# Perform aggregation analysis using Pandas
query_agg = "SELECT island, AVG(elevation_m) FROM hcd_stations GROUP BY island"
df_agg = pd.read_sql_query(query_agg, conn)
print("Average Elevation by Island:")
print(df_agg)
print("\n" + "="*30 + "\n")
'''

# Query for stations within a specific latitude and longitude range
lat_min, lat_max = 19.65, 19.7
lon_min, lon_max = -157.5, -153.5

query_spatial = """
SELECT skn, name, lat, lng 
FROM hcd_stations 
WHERE lat BETWEEN ? AND ? 
  AND lng BETWEEN ? AND ?
"""

df_spatial = pd.read_sql_query(query_spatial, conn, params=(lat_min, lat_max, lon_min, lon_max))

print(f"Stations between Lat [{lat_min}, {lat_max}] and Lon [{lon_min}, {lon_max}]:")
if df_spatial.empty:
    print("No matches found.")
else:
    #print(df_spatial.head()) # Print first few matches to keep output clean
     print(df_spatial) # Print first few matches to keep output clean


# Close the connection
conn.close()