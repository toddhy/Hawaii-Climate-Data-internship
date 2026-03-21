# TileDB Climate Database

This directory contains the high-performance storage layer for the HCDP AI workspace. It utilizes **TileDB Dense Arrays** to store multi-dimensional raster data, enabling rapid spatial and temporal queries that are significantly faster than reading individual TIFF files.

## Directory Structure

- **`rainfall_array/`**: TileDB array containing monthly rainfall data (mm).
- **`temperature_array/`**: TileDB array containing monthly temperature data (Celsius).
- **`tiledb_ingest.py`**: Utility to ingest raw TIFF files from `HCDP_API/` into the TileDB arrays.
- `tiledb_access.py`: Library functions for querying the arrays from other scripts.
- `DATA_DISCREPANCY.md`: Important information explaining why gridded TileDB data may differ from raw station observations.

## Data Schema

The arrays are stored as 3D dense structures with the following dimensions:
1. **`time`**: Indexed by month (mapped to 'YYYY-MM' strings in metadata).
2. **`y`**: Latitude index (row).
3. **`x`**: Longitude index (column).

Each cell contains a `float32` value representing the climate metric for that specific pixel and month.

## Usage

### Ingesting Data
To ingest new TIFFs into the database:
```powershell
python database/tiledb_ingest.py --input_dir HCDP_API/monthly_rainfall --array_uri database/rainfall_array
```

### Accessing Data Programmatically
```python
from database.tiledb_access import get_data_for_month, get_timeseries_for_pixel

# Get a 2D slice for a specific month
grid = get_data_for_month("database/temperature_array", "1995-05")

# Get a time-series for a specific pixel
history = get_timeseries_for_pixel("database/rainfall_array", y_idx, x_idx)
```

---
*Powered by TileDB and Rasterio.*
