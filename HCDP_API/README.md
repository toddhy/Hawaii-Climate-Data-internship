# HCDP API Documentation

This directory contains Python scripts for interacting with the Hawaiʻi Climate Data Portal (HCDP) API to search for weather stations, fetch rainfall data, and visualize the results on interactive maps.

## Scripts Overview

### [station_finder.py](station_finder.py)
A utility module that finds HCDP weather stations within a specified radius of a given latitude and longitude. It uses a local SQLite database for spatial queries and the Haversine formula for precise distance calculations.

### [fetch_station_data.py](fetch_station_data.py)
Uses `station_finder.py` to identify nearby stations and then fetches monthly rainfall timeseries data for each station via the HCDP API (`/raster/timeseries`). The results are saved to `station_rainfall_data.json`.

### [map_HCDP_stations.py](map_HCDP_stations.py)
Takes the JSON output from `fetch_station_data.py` and generates an interactive Folium map (`station_map.html`) showing the locations of all identified stations with clickable popups.

### [average_rainfall_map.py](average_rainfall_map.py)
Processes the rainfall data from `station_rainfall_data.json` to calculate the average monthly rainfall for each station. It then generates an interactive map (`average_rainfall_map.html`) with color-coded markers representing the rainfall intensity.

## Workflow

1.  **Search & Fetch**: Run `fetch_station_data.py` to find stations and download their data.
    -   *Requires*: `.env` file with `HCDP_API_TOKEN`.
2.  **Visualize Stations**: Run `map_HCDP_stations.py` to see where the data is coming from.
3.  **Analyze & Map Rainfall**: Run `average_rainfall_map.py` to see the average rainfall distribution.

---
*Code in this directory was generated with the aid of Gemini 3 Flash.*
