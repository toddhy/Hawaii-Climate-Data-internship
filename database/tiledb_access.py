import tiledb
import json
import numpy as np
import rasterio

def get_metadata(array_uri):
    with tiledb.DenseArray(array_uri, mode='r') as array:
        meta = {
            "transform": json.loads(array.meta["transform"]),
            "crs": array.meta["crs"],
            "nodata": array.meta["nodata"],
            "width": array.meta["width"],
            "height": array.meta["height"],
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
        
        # Fetch metadata and initialize buffers for incremental accumulation
        h, w = array.meta["height"], array.meta["width"]
        nodata_val = array.meta.get("nodata")
        
        # Process monthly to avoid giant memory allocations (e.g. for 72 months)
        sum_buffer = np.zeros((h, w), dtype=np.float64)
        count_buffer = np.zeros((h, w), dtype=np.int32)
        
        for i in range(start_idx, end_idx + 1):
            # Read single 2D month slice
            month_data = array[i, :, :]["value"].astype(np.float64)
            
            # Fast masking
            if nodata_val is not None and not np.isnan(nodata_val):
                month_data[month_data == nodata_val] = np.nan
            month_data[month_data == -9999.0] = np.nan
            month_data[month_data < -1e30] = np.nan
            
            # Identify valid pixels
            valid_mask = ~np.isnan(month_data)
            
            # Accumulate
            sum_buffer[valid_mask] += month_data[valid_mask]
            count_buffer[valid_mask] += 1
            
        # Perform final aggregation
        with np.errstate(divide='ignore', invalid='ignore'):
            if aggregation == 'sum':
                aggregated = sum_buffer
            else:
                aggregated = np.where(count_buffer > 0, sum_buffer / count_buffer, np.nan)
                
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
