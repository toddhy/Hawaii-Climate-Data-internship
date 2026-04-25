# High-Resolution Daily Rainfall Ingestion
This directory contains tools for handling storm-level daily rainfall data from the HCDP.

## Key Utility: `ingest_daily_stream.py`
This script allows for the mass-ingestion of 30+ years of daily rainfall data without requiring intermediate disk space for GeoTIFFs.

### Optimization Strategy
- **Integer Quantization**: Data is stored as `uint16` (Rainfall mm * 10).
- **Time Chunking**: Arrays are tiled in (365, 64, 64) blocks to allow fast time-series extraction.
- **Memory Streaming**: Downloads 3.5 million pixel rasters directly into RAM for processing.

### Usage (WSL / Linux)
Due to Windows filesystem locking issues, it is **strongly recommended** to run this script in a WSL environment.

1. **Setup WSL Environment**:
   ```bash
   # From your project root in WSL
   source .venv_linux/bin/activate
   export HCDP_API_TOKEN=your_token_here
   ```

2. **Initialize the Array**:
   ```bash
   python HCDP_API/ingest_daily_stream.py --init
   ```

3. **Ingest a Range (e.g., Year 1990)**:
   ```bash
   python HCDP_API/ingest_daily_stream.py --start 1990-01-01 --end 1990-12-31 --batch_size 30
   ```

### Skipping Logic
The script is "Smart"—it checks the database metadata before every batch. If you stop the script and restart it with the same dates, it will automatically skip days that are already ingested.

## Map Visualization
Once ingested, the data can be visualized using `map_visualizer.py` by specifying `data_type='daily_rainfall'`.
- **Aggregation**: Defaults to `sum` (total accumulation for the requested range).
- **Transparency**: The `tiledb_access.py` layer automatically converts the integer data back to millimeters (divides by 10) so the maps show correct physical values.
