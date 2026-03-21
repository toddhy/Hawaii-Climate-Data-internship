# HCDP API Documentation

This directory contains Python scripts for interacting with the Hawaiʻi Climate Data Portal (HCDP) API to search for weather stations, fetch rainfall data, and visualize the results on interactive maps.

## Scripts Overview

### [station_finder.py](station_finder.py)
A utility module that finds HCDP weather stations within a specified radius of a given latitude and longitude. It uses a local SQLite database for spatial queries and the Haversine formula for precise distance calculations.

### [fetch_station_data.py](fetch_station_data.py)
Uses `station_finder.py` to identify nearby stations and سپس fetches monthly rainfall timeseries data.
- **Usage**: `python fetch_station_data.py [lat] [lon] [radius]`
- **Arguments**: Optional positional arguments for Latitude, Longitude, and Radius (km).

### [tiff_downloader.py](tiff_downloader.py)
A batch downloader for HCDP rainfall TIFF rasters. Iterates through a specified date range and saves files as `YYYY-MM.tiff`.
- **Usage**: `python tiff_downloader.py start_date end_date` (e.g., `2008-01 2022-12`)

### [tiff_visualizer.py](tiff_visualizer.py)
Creates an aggregate, colored rainfall map from a directory of TIFF files. It averages the raster data and generates a Folium map with an image overlay.
- **Usage**: `python tiff_visualizer.py [--input_dir DIR]`

### [unified_rainfall_map.py](unified_rainfall_map.py)
Combines weather station markers (colored by rainfall or grey locations) and the aggregate rainfall raster (from TIFFs) onto a single interactive map. 
- **Features**: 
    - **Data Independence**: Can map station locations using `station_finder` even if rainfall JSON data is missing.
    - **Flexible Markers**: Automatically uses rainfall data for coloring if available; otherwise uses location markers.
    - **Spatial Clipping**: Automatically masks the raster data to a circular area around the center.
    - **Robust TIFF Handling**: Checks for consistent shapes and handles file access errors gracefully.
- **Usage**: `python unified_rainfall_map.py [--lat LAT] [--lon LON] [--radius KM] [--no_json]`
- **Note**: Use `--no_json` to skip station rainfall data and just map coordinates.

### [map_HCDP_stations.py](map_HCDP_stations.py)
Takes the JSON output from `fetch_station_data.py` and generates an interactive Folium map (`station_map.html`) showing the locations of all identified stations with clickable popups.

### [average_rainfall_map.py](average_rainfall_map.py)
Processes the rainfall data from `station_rainfall_data.json` to calculate the average monthly rainfall for each station. It then generates an interactive map (`average_rainfall_map.html`) with color-coded markers representing the rainfall intensity.

## Workflow & Automation

### Gemini Chatbot (Recommend)
The easiest way to use these tools is via the [chatbot](../gemini_chat/chatbot.py). You can simply ask:
- *"What is the average rainfall in Honolulu?"* (Automates location lookup + fetch + map)
- *"Download rainfall TIFFs for 2022"* (Triggers batch download)

### Manual Workflow
1.  **Search & Fetch**: Run `fetch_station_data.py` to find stations and download their data.
2.  **Visualize**: Run `average_rainfall_map.py` to see results.
3.  **Batch Export**: Use `tiff_downloader.py` for raw raster data.
4.  **Database Ingestion**: Once TIFF files are downloaded, use `database/tiledb_ingest.py` to move them into the high-performance TileDB storage for faster AI querying. The database now supports data from **1990 to 2026**.

> [!TIP]
> If you notice differences between the raster TIFF values and station observations, refer to [database/DATA_DISCREPANCY.md](../database/DATA_DISCREPANCY.md) for a technical explanation.

---
*Code in this directory was generated with the aid of Gemini 3 Flash.*
