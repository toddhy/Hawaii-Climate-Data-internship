# TileDB Climate Database

This directory contains the high-performance storage layer for the HCDP AI workspace. It utilizes **TileDB Dense Arrays** to store multi-dimensional raster data, enabling rapid spatial and temporal queries that are significantly faster than reading individual TIFF files. Dates are ISO 8601 formatted in YYYY-MM.

## Directory Structure

- **`rainfall_array/`**: TileDB array containing monthly rainfall data (mm).
- **`temperature_array/`**: TileDB array containing monthly mean temperature data (Celsius).
- **`max_temp_array/`**: TileDB array containing monthly maximum temperature data (Celsius).
- **`min_temp_array/`**: TileDB array containing monthly minimum temperature data (Celsius).
- **`spi_array/`**: TileDB array containing Standardized Precipitation Index (SPI) data.
- **`tiledb_ingest.py`**: Utility to ingest raw TIFF files (Rainfall/Temp) from `HCDP_API/` into TileDB arrays.
- **`ingest_spi.py`**: Utility specifically for ingesting SPI data.
- **`optimize_storage.py`**: Utility to migrate/re-ingest data with high-level Zstd compression (Level 7) for maximum disk efficiency.
- **`db_stats.py`**: Utility to retrieve and display statistics (range, count, resolution) for all arrays in the database.
- `tiledb_access.py`: Library functions for querying the arrays from other scripts.
- `DATA_DISCREPANCY.md`: Important information explaining why gridded TileDB data may differ from raw station observations.

## Data Schema

The arrays are stored as 3D dense structures with the following dimensions:
1. **`time`**: Indexed by month (mapped to 'YYYY-MM' strings in metadata).
2. **`y`**: Latitude index (row).
3. **`x`**: Longitude index (column).

Each cell contains a `float32` value representing the climate metric (mm, Celsius, or SPI units) for that specific pixel and month.

## Usage

### Ingesting Data
To ingest new TIFFs into the database:
```powershell
# For Rainfall/Temperature
python database/tiledb_ingest.py --input_dir HCDP_API/monthly_rainfall --array_uri database/rainfall_array

# For SPI
python database/ingest_spi.py --input_dir HCDP_API/monthly_spi --array_uri database/spi_array
```

### Accessing Data Programmatically
```python
from database.tiledb_access import get_data_for_month, get_timeseries_for_pixel

# Get a 2D slice for a specific month (e.g., Rainfall)
grid = get_data_for_month("database/rainfall_array", "1995-05")

# Get a time-series for a specific pixel
history = get_timeseries_for_pixel("database/rainfall_array", y_idx, x_idx)
```

### Viewing Database Statistics
To see a summary of all stored years, months, and variables:
```powershell
python database/db_stats.py
```

---
*Powered by TileDB and Rasterio.*
