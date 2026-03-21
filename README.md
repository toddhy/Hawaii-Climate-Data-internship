# HCDP-data-for-AI
Analyzing data from the Hawaii Climate Data Portal.

## Project Highlights

### Gemini Chatbot Automation
We've integrated a Gemini 2.0 Flash powered chatbot that can:
- **Execute Local Scripts**: Trigger data fetching and mapping directly from natural language.
- **Inferred Geolocation**: Understand place names (like "Honolulu") and automatically provide coordinates to data scripts.
- **Intelligent Defaults**: Automatically applies a **5.0 km radius** and the **current year (2026)** to map requests if not specified.
- **Batch Processing**: Handle complex workflows like "fetch data for Hilo and then map it".

### High-Performance TileDB Storage
A centralized storage layer in `database/` that:
- **Optimized Access**: Replaces slow individual TIFF reads with high-speed multi-dimensional array slicing.
- **Pixel-Perfect AI Queries**: Provides the backend for the AI agent to retrieve exact historical climate values for any coordinate in Hawaii instantly.
- **Decades of Coverage**: Now includes over **430 months** of data, spanning from **January 1990 to February 2026**.
- **Scalable**: Efficiently manages ~12GB of raster data with optimized multi-dimensional indexing.

> [!NOTE]
> For information on slight differences between gridded (TIFF) data and station observations, see [database/DATA_DISCREPANCY.md](database/DATA_DISCREPANCY.md).

### HCDP API Tools
A suite of tools located in `HCDP_API/` for:
- Finding weather stations within a specific radius.
- Fetching historical rainfall timeseries data.
- Batch downloading rainfall TIFF rasters.
- Creating unified maps with both station points and gridded rainfall overlays.
- Creating interactive rainfall distribution maps.

## Quick Start

To run the complete application (both the FastAPI backend and the React frontend), you can use the provided startup script:

1.  **Double-click** `start_app.cmd` in the project root.
2.  Alternatively, run `.\start_app.ps1` from a PowerShell terminal.

The script will start both servers and ensure they are properly terminated when you close the window or press **Ctrl+C**.

## Useful Links
- [HCDP Publication List](https://www.hawaii.edu/climate-data-portal/publications-list/)
- [Additional Works Cited (Scholar)](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=15630183130413266936&as_sdt=5)