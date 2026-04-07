# HCDP-data-for-AI
Analyzing data from the Hawaii Climate Data Portal.

## Project Highlights

### Gemini Chatbot Automation
We've integrated a Gemini 2.0 Flash powered chatbot that can:
- **Execute Local Scripts**: Trigger data fetching and mapping directly from natural language.
- **Inferred Geolocation**: Understand place names (like "Honolulu") and automatically provide coordinates to data scripts.
- **Intelligent Defaults**: Automatically applies a **5.0 km radius** and the **current year (2026)** to map requests if not specified.
- **Batch Processing**: Handle complex workflows like "fetch data for Hilo and then map it".

For a detailed breakdown of the agent's tools and the underlying technical architecture, see [AGENT_TOOLS.md](file:///c:/SCIPE/HCDP-data-for-AI/gemini_chat/AGENT_TOOLS.md).


### High-Performance TileDB Storage
A centralized storage layer in `database/` that:
- **Optimized Access**: Replaces slow individual TIFF reads with high-speed multi-dimensional array slicing.
- **Pixel-Perfect AI Queries**: Provides the backend for the AI agent to retrieve exact historical climate values for any coordinate in Hawaii instantly.
- **Decades of Coverage**: Now includes over **1,800 total time slices** across five variables:
    - **Rainfall**: 1990 - 2026
    - **Temperature (Mean)**: 1990 - 2026
    - **Temperature (Max)**: 1990 - 2026
    - **Temperature (Min)**: 1990 - 2026
    - **SPI (36-month timescale)**: 1992 - 2026
- **Scalable**: Efficiently manages ~25GB of raster data with optimized Zstd compression and multi-dimensional indexing.

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

To run the complete application (both the FastAPI backend and the React frontend), you can use the following startup scripts:

- **Windows**: Double-click `start_app.cmd` or run `.\start_app.ps1` from PowerShell.
- **Linux / macOS**: Run `./start_app.sh` from your terminal.

The script will handle dependency checks (e.g., `node_modules`, `.venv`), start both the backend and frontend servers, and ensure they are properly terminated when closed.

## Maintenance and Deployment

- **Deployment**: Use `./deploy.sh` to automate the deployment process to a remote server (e.g., Nginx setup).
- **Data Synchronization**: Use `./sync.sh` to synchronize the local research corpus and TileDB database with remote sources.

## Useful Links
- [Database files](https://drive.google.com/file/d/1ziKvCJKqoPZUaJnIzUN4bQwdcNVA-fDu/view?usp=sharing)
- [TIFF files](https://drive.google.com/file/d/1gIkX3MZ0_DjaBf8u7FsD6sNHf3o_mv_N/view?usp=sharing)
- [System Architecture](ARCHITECTURE.md)
- [Workflow](WORKFLOW.md)
- [HCDP Publication List](https://www.hawaii.edu/climate-data-portal/publications-list/)
- [Additional Works Cited (Scholar)](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=15630183130413266936&as_sdt=5)