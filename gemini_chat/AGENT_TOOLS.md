# LangChain Agent: Tools & Utilities Documentation

This document outlines the specialized functions provided to the LangChain AI agent and the underlying utility modules that perform the technical operations.

## Overview

The LangChain agent acts as an orchestrator. It receives natural language requests (e.g., "Show me rainfall in Honolulu") and decides which **Tools** to call. These tools, in turn, leverage **Utilities** to process data, query databases, and generate visualizations.

---

## 🛠️ Agent Tools
Tools are high-level functions decorated with `@tool` that the LLM is explicitly aware of. They handle parameter parsing and return formatted string results to the agent.

| Tool Name | Purpose | Key Inputs |
| :--- | :--- | :--- |
| `geocode_placename` | Converts Hawaii place names into Latitude/Longitude coordinates. | `place_name` |
| `find_nearby_stations` | Finds weather stations within a specific KM radius. | `latitude`, `longitude`, `radius_km` |
| `map_nearby_stations` | Generates a basic HTML map showing station locations only. | `latitude`, `longitude`, `radius_km` |
| `generate_gridded_map` | Generates a complex map with raster overlays (Rainfall/Temp) and stations. | `data_type`, `latitude`, `longitude`, `start_date`, `end_date`, `add_stations` |
| `query_historical_climate_data` | Queries exact historical climate values from the TileDB database for a single month. | `latitude`, `longitude`, `month`, `variable` |
| `query_historical_timeseries` | Queries the TileDB database for summarized regional climate data over a date range. | `latitude`, `longitude`, `radius_km`, `start_date`, `end_date`, `variable` |

---

## ⚙️ Underlying Utilities
Utilities are internal python modules and scripts that perform the heavy lifting. The agent does not "see" these; it only interacts with them through the tools.

### 1. Data Retrieval & Spatial Search
*   **[station_finder.py](file:///c:/SCIPE/HCDP-data-for-AI/HCDP_API/station_finder.py)**: Performs SQLite queries against `hcdp_stations.db` to find stations based on geographic distance.
*   **[tiledb_access.py](file:///c:/SCIPE/HCDP-data-for-AI/database/tiledb_access.py)**: Handles low-level reading of TileDB arrays. It includes the coordinate-to-pixel transformation logic using affine matrices.

### 2. Map Generation & Visualization
*   **[map_visualizer.py](file:///c:/SCIPE/HCDP-data-for-AI/HCDP_API/map_visualizer.py)**: The core visualization engine. It handles:
    *   Merging multiple GeoTIFF files for temporal aggregation.
    *   Clipping raster data to a user-defined radius.
    *   Generating Folium maps with custom colormaps and station overlays.
*   **[map_HCDP_stations.py](file:///c:/SCIPE/HCDP-data-for-AI/HCDP_API/map_HCDP_stations.py)**: A lighter-weight utility focused specifically on plotting station markers without raster data.

### 3. External Services
*   **Geopy (Nominatim)**: An external library used within the `geocode_placename` tool to provide geographic search capabilities (OpenStreetMap).

---
> [!TIP]
> When adding new functionality, first create a **Utility** to handle the logic, then wrap it in a `@tool` within `langchain_agent.py` to make it accessible to the AI.
