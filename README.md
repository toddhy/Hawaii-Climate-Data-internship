# HCDP-data-for-AI
Analyzing data from the Hawaii Climate Data Portal.

## Project Highlights

### Gemini Chatbot Automation
We've integrated a Gemini 3.1 Flash powered chatbot that can:
- **Execute Local Scripts**: Trigger data fetching and mapping directly from natural language.
- **Inferred Geolocation**: Understand place names (like "Honolulu") and automatically provide coordinates to data scripts.
- **Intelligent Defaults**: Automatically applies a **5.0 km radius** and the **current year (2026)** to map requests if not specified.

For a detailed breakdown of the agent's tools and the underlying technical architecture, see [AGENT_TOOLS.md](file:///c:/SCIPE/HCDP-data-for-AI/gemini_chat/AGENT_TOOLS.md).


### High-Performance TileDB Storage
A centralized storage layer in `database/` that:
- **`optimize_storage.py`**: Utility to migrate/re-ingest TileDB data with high-level Zstd compression (Level 7) for maximum disk efficiency.
- **Pixel-Perfect AI Queries**: Provides the backend for the AI agent to retrieve exact historical climate values for any coordinate in Hawaii instantly.
- **Decades of Coverage**: Now includes over **1,800 total time slices** across five variables:
    - **Rainfall**: 1990 - 2026
    - **Temperature (Mean)**: 1990 - 2026
    - **Temperature (Max)**: 1990 - 2026
    - **Temperature (Min)**: 1990 - 2026
    - **SPI (36-month timescale)**: 1992 - 2026
- **Scalable**: Efficiently manages ~11GB of raster data with optimized Zstd (TileDB) and LZW (TIFF) compression.
- **Robust NoData Handling**: Implements automated masking of legacy fill values (e.g., -9999.0) and extreme float values, ensuring all aggregations (mean, sum) are statistically accurate.
- **Memory-Efficient**: Optimized for large-scale map generation using an incremental 2D accumulation strategy to handle decades of data without exhausting system RAM.

### HCDP API Tools
A suite of tools located in `HCDP_API/` for:
- Finding weather stations within a specific radius.
- Fetching historical rainfall timeseries data.
- Batch downloading rainfall TIFF rasters.
- Creating unified maps with both station points and gridded rainfall overlays.
- Creating interactive rainfall distribution maps.

## Quick Installation Instructions

Install prerequisite software:
```
sudo apt install npm
```
Clone the repository and make startup script executable:
```
git clone https://github.com/toddhy/Hawaii-Climate-Data-internship.git
cd Hawaii-Climate-Data-internship/
chmod +x start_app.sh
```
Optional but highly recommended, create python venv and switch to it before installing python modules. It may give you instructions to install correct version of venv for you if not installed:
```
python3 -m venv .venv
source .venv/bin/activate
```
Install python packages:
```
pip install -r requirements.txt
```
Install node packages:
```
npm install
```

## Troubleshooting ##

Upgrade node version:
```
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v  # Should show v22.x.x
```


## Maintenance and Deployment

- **Deployment**: Use `./deploy.sh` to automate the deployment process to a remote server (e.g., Nginx setup).

## Useful Links
- [Database files](https://drive.google.com/file/d/1ziKvCJKqoPZUaJnIzUN4bQwdcNVA-fDu/view?usp=sharing)
- [TIFF files](https://drive.google.com/file/d/1gIkX3MZ0_DjaBf8u7FsD6sNHf3o_mv_N/view?usp=sharing)
- [System Architecture](ARCHITECTURE.md)
- [Workflow](WORKFLOW.md)
- [HCDP Publication List](https://www.hawaii.edu/climate-data-portal/publications-list/)
- [Additional Works Cited (Scholar)](https://scholar.google.com/scholar?oi=bibs&hl=en&cites=15630183130413266936&as_sdt=5)
