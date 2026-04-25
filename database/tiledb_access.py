"""
TileDB Data Access Layer
------------------------
Core utility for querying and aggregating geospatial climate data from TileDB Dense Arrays.

Features:
- Efficient spatial/temporal slicing.
- Automatic De-quantization: Detects 'mm * 10' metadata and automatically restores float values.
- Regional Aggregation: Provides mean/sum statistics for specified bounding boxes.
"""
import tiledb
import json
import numpy as np
import rasterio
import os
import hashlib

def get_metadata(array_uri):
    with tiledb.DenseArray(array_uri, mode='r') as array:
        meta = {
            "transform": json.loads(array.meta["transform"]),
            "crs": array.meta.get("crs", "EPSG:4326"),
            "nodata": array.meta.get("nodata"),
            "width": array.meta.get("width", array.shape[2]),
            "height": array.meta.get("height", array.shape[1]),
            "time_mapping": json.loads(array.meta["time_mapping"])
        }
    return meta

def get_data_for_month(array_uri, date_str):
    """
    Retrieves the 2D geospatial array for a specific month.
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        time_mapping = json.loads(array.meta["time_mapping"])
        if date_str not in time_mapping:
            raise ValueError(f"Date {date_str} not found in array metadata.")
        
        time_index = time_mapping[date_str]
        
        # TileDB slicing is highly efficient since it only fetches the needed blocks
        data = array[time_index, :, :]["value"]
        
        # Ensure float type for NaN support
        data = data.astype(float)
        
        # Mask nodata/legacy values efficiently
        nodata_val = array.meta.get("nodata")
        
        # Use fast direct comparison and thresholding instead of slow np.isclose
        if nodata_val is not None and not np.isnan(nodata_val):
            data[data == nodata_val] = np.nan
        
        data[data == -9999.0] = np.nan
        data[data < -1e30] = np.nan
            
        # Handle quantization if present
        unit = array.meta.get("unit", "")
        if "mm * 10" in unit:
            data = data / 10.0

        return data

def get_timeseries_for_pixel(array_uri, y, x):
    """
    Retrieves the temporal slice (time series) for a specific pixel coordinate.
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        # Slice across the time dimension for a single (y, x)
        data = array[:, y, x]["value"]
        time_mapping = json.loads(array.meta["time_mapping"])
        
        # Invert mapping to return {date: value}
        inverted_mapping = {v: k for k, v in time_mapping.items()}
        
        # Mask common fill values in time series efficiently
        data = data.astype(float)
        data[data == -9999.0] = np.nan
        data[data < -1e30] = np.nan
        
        # Handle quantization if present
        unit = array.meta.get("unit", "")
        if "mm * 10" in unit:
            data = data / 10.0

        series = {}
        for idx, val in enumerate(data):
            if idx in inverted_mapping:
                # Skip NaNs in the final result series
                if not np.isnan(val):
                    series[inverted_mapping[idx]] = float(val)
        return series

def get_timeseries_for_region(array_uri, start_date, end_date, y_min, y_max, x_min, x_max):
    """
    Retrieves a spatial average (mean) time series for a bounding box region.
    Coordinates y_min, y_max, x_min, x_max should be integer pixel indices.
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        time_mapping = json.loads(array.meta["time_mapping"])
        # Sort months to find the indices
        sorted_months = sorted(time_mapping.keys())
        
        # Determine start/end indices for time slicing
        relevant_months = [m for m in sorted_months if (not start_date or m >= start_date) and (not end_date or m <= end_date)]
        if not relevant_months:
            return {}
        
        # Sort the relevant months to ensure correct mapping to the slice
        relevant_months.sort()
        
        start_idx = time_mapping[relevant_months[0]]
        end_idx = time_mapping[relevant_months[-1]]
        
        # Ensure pixel indices are within array bounds
        h, w = array.meta["height"], array.meta["width"]
        y_min = max(0, min(y_min, h - 1))
        y_max = max(0, min(y_max, h - 1))
        x_min = max(0, min(x_min, w - 1))
        x_max = max(0, min(x_max, w - 1))

        # TileDB slicing in Python follows NumPy conventions (stop index is exclusive)
        data_block = array[start_idx:end_idx + 1, y_min:y_max, x_min:x_max]["value"]
        
        # Ensure float type for NaN support
        data_block = data_block.astype(float)
        
        # Mask nodata/legacy values efficiently
        nodata_val = array.meta.get("nodata")
        if nodata_val is not None and not np.isnan(nodata_val):
            data_block[data_block == nodata_val] = np.nan
        
        data_block[data_block == -9999.0] = np.nan
        data_block[data_block < -1e30] = np.nan
            
        # Handle quantization if present
        unit = array.meta.get("unit", "")
        if "mm * 10" in unit:
            data_block = data_block / 10.0
            
        # Spatial aggregation (mean over y and x dims)
        with np.errstate(all='ignore'):
            # axis=(1, 2) averages across height and width
            spatial_mean = np.nanmean(data_block, axis=(1, 2))
            
        # Construct the result dictionary
        series = {}
        for i, month in enumerate(relevant_months):
            val = float(spatial_mean[i])
            if not np.isnan(val):
                series[month] = val
                
        return series

def get_raster_for_date_range(array_uri, start_date, end_date, aggregation='mean'):
    """
    Retrieves an aggregated 2D raster for a specific date range.
    aggregation: 'sum' (for rainfall) or 'mean' (for temperature/SPI)
    """
    with tiledb.DenseArray(array_uri, mode='r') as array:
        time_mapping = json.loads(array.meta["time_mapping"])
        sorted_months = sorted(time_mapping.keys())
        relevant_months = [m for m in sorted_months if (not start_date or m >= start_date) and (not end_date or m <= end_date)]
        
        if not relevant_months:
            return None, None
        
        relevant_months.sort()
        start_idx = time_mapping[relevant_months[0]]
        end_idx = time_mapping[relevant_months[-1]]
        num_slices = end_idx - start_idx + 1
        
        # Fetch metadata and initialize buffers for incremental accumulation
        try:
            h, w = array.meta["height"], array.meta["width"]
        except KeyError:
            # Fallback: Infer from array dimensions (shape is [time, row, col])
            h, w = array.shape[1], array.shape[2]
            
        nodata_val = array.meta.get("nodata")

        # Process in spatial blocks to keep memory usage low and disk I/O efficient
        block_size = 512
        aggregated = np.full((h, w), np.nan, dtype=np.float64)
        
        # 1. Check Cache for heavy operations (Percentile)
        cache_path = None
        if aggregation == 'percentile':
            cache_dir = os.path.join(os.path.dirname(array_uri), "cache")
            os.makedirs(cache_dir, exist_ok=True)
            cache_name = f"perc99_{os.path.basename(array_uri)}_{start_date}_{end_date}.npy"
            cache_path = os.path.join(cache_dir, cache_name)
            if os.path.exists(cache_path):
                print(f"[*] Loading 99th percentile from cache: {cache_name}")
                return np.load(cache_path), None, None

        total_blocks = ((h + block_size - 1) // block_size) * ((w + block_size - 1) // block_size)
        current_block = 0
        
        print(f"[*] Aggregating {num_slices} slices using Unified Block Engine ({aggregation})...")
        for r in range(0, h, block_size):
            r_end = min(r + block_size, h)
            for c in range(0, w, block_size):
                c_end = min(c + block_size, w)
                current_block += 1
                
                # 1. Fetch entire time-stack for this spatial block
                block_stack = array[start_idx:end_idx + 1, r:r_end, c:c_end]["value"]
                
                # 2. Fast Ocean Skip
                if nodata_val is not None and np.all(block_stack == nodata_val):
                    continue
                    
                # 3. Mask and de-quantize
                block_stack = block_stack.astype(np.float32)
                if nodata_val is not None and not np.isnan(nodata_val):
                    block_stack[block_stack == nodata_val] = np.nan
                block_stack[block_stack == -9999.0] = np.nan
                block_stack[block_stack < -1e30] = np.nan
                
                unit = array.meta.get("unit", "")
                if "mm * 10" in unit:
                    block_stack = block_stack / 10.0
                
                # 4. Perform Aggregation
                if aggregation == 'sum':
                    block_result = np.nansum(block_stack, axis=0)
                    # If all were NaN, nansum returns 0. Correct this to NaN.
                    all_nan = np.all(np.isnan(block_stack), axis=0)
                    block_result[all_nan] = np.nan
                elif aggregation == 'mean':
                    block_result = np.nanmean(block_stack, axis=0)
                elif aggregation == 'percentile':
                    # Land-only optimization for percentiles
                    num_days, bh, bw = block_stack.shape
                    space_flat = block_stack.reshape(num_days, -1)
                    any_data_mask = np.any(~np.isnan(space_flat), axis=0)
                    
                    block_result_flat = np.full(space_flat.shape[1], np.nan)
                    if np.any(any_data_mask):
                        valid_pixels = space_flat[:, any_data_mask]
                        # Replace NaNs with -1 for fast partitioning
                        valid_pixels[np.isnan(valid_pixels)] = -1.0
                        k = int(num_days * 0.99)
                        if k >= num_days: k = num_days - 1
                        partitioned = np.partition(valid_pixels, k, axis=0)
                        block_result_flat[any_data_mask] = partitioned[k, :]
                    block_result = block_result_flat.reshape(bh, bw)
                else:
                    block_result = np.nanmean(block_stack, axis=0) # Default to mean
                
                aggregated[r:r_end, c:c_end] = block_result
                
                if current_block % 5 == 0 or current_block == total_blocks:
                    print(f"    - Progress: {int((current_block/total_blocks)*100)}%")

        # Save to Cache
        if cache_path:
            try:
                np.save(cache_path, aggregated)
                print(f"[*] Saved result to cache: {os.path.basename(cache_path)}")
            except Exception as e:
                print(f"Warning: Could not save cache: {e}")

        # Get metadata for the mapper
        meta = {
            "transform": json.loads(array.meta["transform"]),
            "crs": array.meta["crs"],
            "width": array.meta["width"],
            "height": array.meta["height"]
        }
        
        # Calculate bounds for Folium (bottom-left, top-right)
        # transform: [res_x, shear_x, x_min, shear_y, res_y, y_max]
        t = meta["transform"]
        x_min, y_max = t[2], t[5]
        x_max = x_min + t[0] * meta["width"]
        y_min = y_max + t[4] * meta["height"]
        
        folium_bounds = [[y_min, x_min], [y_max, x_max]]
        
        return aggregated, folium_bounds, meta

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query a TileDB Array containing Monthly Rasters")
    parser.add_argument("--array_uri", required=True, help="Path/URI for the TileDB array")
    parser.add_argument("--month", help="Month to query (e.g., '2022-01')")
    args = parser.parse_args()
    
    if args.month:
        try:
            data = get_data_for_month(args.array_uri, args.month)
            print(f"Extracted shape for {args.month}: {data.shape}")
            print(f"Min Data Value: {np.nanmin(data)}")
            print(f"Max Data Value: {np.nanmax(data)}")
        except Exception as e:
            print(f"Error querying data: {e}")
    else:
        meta = get_metadata(args.array_uri)
        print(f"--- TileDB Array Metadata ---")
        print(f"Shape: (time: {len(meta['time_mapping'])}, y: {meta['height']}, x: {meta['width']})")
        print(f"CRS: {meta['crs']}")
        print(f"Stored Months: {sorted(list(meta['time_mapping'].keys()))}")
