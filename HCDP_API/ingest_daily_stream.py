"""
HCDP Daily Rainfall Stream Ingestor
-----------------------------------
This utility performs space-efficient ingestion of high-resolution daily rainfall data 
from the HCDP API into a local TileDB database.

Usage Examples:
    1. Initialize the empty array:
       python HCDP_API/ingest_daily_stream.py --init

    2. Ingest a specific year (e.g., 1990):
       python HCDP_API/ingest_daily_stream.py --start 1990-01-01 --end 1990-12-31 --batch_size 30

Arguments:
    --init        : Creates the TileDB array schema at the default URI. Run this once before ingestion.
    --start       : The starting date in YYYY-MM-DD format.
    --end         : The ending date in YYYY-MM-DD format.
    --batch_size  : Number of days to process in a single TileDB write (default: 30). 
                    Larger batches are faster but use more RAM (~7MB per day).

Key Features:
    - "No-Disk" Streaming: Downloads directly to memory, avoiding 450GB+ of intermediate TIFF storage.
    - Integer Quantization: Converts rainfall (mm) to uint16 (mm * 10) to reduce storage size by ~90%.
    - Smart Skipping: Automatically detects and skips dates already present in the database.
    - WSL Optimized: Designed for WSL/Linux to bypass Windows filesystem locking issues.

Requirements:
    - HCDP_API_TOKEN environment variable or .env entry.
    - Python modules: tiledb, rasterio, requests, numpy, python-dotenv.
"""
import os
import sys
import requests
import numpy as np
from dotenv import load_dotenv
import io
import json
import time
import tiledb
import rasterio
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
print("DEBUG: Script started and environment loaded.")

API_URL = "https://api.hcdp.ikewai.org/raster"
AUTH_TOKEN = os.getenv("HCDP_API_TOKEN")

# Global TileDB Context
# config = tiledb.Config({
#     "sm.num_reader_threads": 1,
#     "sm.num_writer_threads": 1,
#     "vfs.min_parallel_size": 0
# })
# ctx = tiledb.Ctx(config)
ctx = None

def create_daily_rainfall_array(array_uri, height, width, transform, crs):
    if tiledb.array_exists(array_uri):
        print(f"Array already exists at {array_uri}")
        return

    tiling = (365, 64, 64)
    dom = tiledb.Domain(
        tiledb.Dim(name="time", domain=(0, 15000), tile=tiling[0], dtype=np.int32, ctx=ctx),
        tiledb.Dim(name="y", domain=(0, height - 1), tile=tiling[1], dtype=np.int32, ctx=ctx),
        tiledb.Dim(name="x", domain=(0, width - 1), tile=tiling[2], dtype=np.int32, ctx=ctx),
        ctx=ctx
    )

    attr = tiledb.Attr(
        name="value",
        dtype=np.uint16,
        fill=65535,
        filters=tiledb.FilterList([tiledb.ZstdFilter(level=7)]),
        ctx=ctx
    )

    schema = tiledb.ArraySchema(
        domain=dom,
        attrs=[attr],
        sparse=False,
        cell_order='row-major',
        tile_order='row-major',
        ctx=ctx
    )

    print(f"Creating TileDB array at {array_uri}...")
    tiledb.DenseArray.create(array_uri, schema)

    with tiledb.DenseArray(array_uri, mode='w', ctx=ctx) as array:
        array.meta["transform"] = json.dumps(list(transform))
        array.meta["crs"] = crs
        array.meta["nodata"] = 65535
        array.meta["height"] = height
        array.meta["width"] = width
        array.meta["unit"] = "mm * 10 (uint16)"
        array.meta["time_mapping"] = json.dumps({})
        array.meta["next_time_index"] = 0

def download_and_preprocess(date_str):
    if not AUTH_TOKEN:
        raise ValueError("HCDP_API_TOKEN not set.")

    params = {
        'date': date_str,
        'location': 'hawaii',
        'datatype': 'rainfall',
        'extent': 'statewide',
        'period': 'day',
        'production': 'new'
    }
    
    headers = {
        'accept': 'image/tif',
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers, stream=True)
        if response.status_code != 200:
            print(f"  Error {response.status_code} for {date_str}")
            return None

        with rasterio.MemoryFile(response.content) as memfile:
            with memfile.open() as src:
                data = src.read(1).astype(np.float32)
                data[data < 0] = np.nan
                quantized = np.round(data * 10).astype(np.float32)
                quantized[np.isnan(quantized)] = 65535
                return quantized.astype(np.uint16)
    except Exception as e:
        print(f"  Exception for {date_str}: {e}")
        return None

def ingest_batch(dates, array_uri):
    # 1. Read metadata and filter existing dates
    try:
        with tiledb.DenseArray(array_uri, mode='r', ctx=ctx) as array:
            next_idx = int(array.meta.get("next_time_index", 0))
            time_mapping = json.loads(array.meta.get("time_mapping", "{}"))
    except Exception as e:
        print(f"[!] Error reading metadata: {e}")
        return 0

    # Filter out dates already in the database
    dates_to_process = [d for d in dates if d not in time_mapping]
    skip_count = len(dates) - len(dates_to_process)
    
    if skip_count > 0:
        print(f"[*] Skipping {skip_count} dates already present in the database.")
    
    if not dates_to_process:
        print("[*] All dates in this batch are already ingested.")
        return 0

    # 2. Download and preprocess
    print(f"[*] Downloading {len(dates_to_process)} days from HCDP API...")
    data_list = []
    successful_dates = []
    
    start_time = time.time()
    for date_str in dates_to_process:
        print(f"  > Fetching {date_str} into memory...", end="\r")
        img = download_and_preprocess(date_str)
        if img is not None:
            data_list.append(img)
            successful_dates.append(date_str)
        time.sleep(0.1) 
    
    if not data_list:
        print("\n[!] No data successfully downloaded in this batch.")
        return 0

    download_duration = time.time() - start_time
    print(f"\n[*] Downloaded {len(data_list)} days in {download_duration:.1f}s (Avg: {download_duration/len(data_list):.2f}s/day)")

    # 3. Cooling down (Stability for Windows/WSL interoperability)
    print(f"[*] Cooling down for 5s to ensure filesystem stability...")
    time.sleep(5)

    # 4. Atomic Write to TileDB
    print(f"[*] Writing {len(data_list)} days to TileDB [Index: {next_idx} to {next_idx + len(successful_dates) - 1}]...")
    batch_data = np.stack(data_list)
    end_idx = next_idx + len(successful_dates)
    
    max_retries = 5
    write_start = time.time()
    for attempt in range(max_retries):
        try:
            with tiledb.DenseArray(array_uri, mode='w', ctx=ctx) as array:
                array[next_idx:end_idx, :, :] = batch_data
                for d in successful_dates:
                    time_mapping[d] = next_idx
                    next_idx += 1
                array.meta["time_mapping"] = json.dumps(time_mapping)
                array.meta["next_time_index"] = next_idx
            
            write_duration = time.time() - write_start
            print(f"[+] Batch write successful! ({write_duration:.1f}s)")
            return len(successful_dates)
        except Exception as e:
            wait_time = (attempt + 1) * 5
            print(f"  [!] Attempt {attempt+1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    print("[!!] Failed to write batch after multiple retries.")
    return 0

def generate_date_list(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = []
    curr = start
    while curr <= end:
        dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return dates

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--start", help="YYYY-MM-DD")
    parser.add_argument("--end", help="YYYY-MM-DD")
    parser.add_argument("--batch_size", type=int, default=30)
    
    args = parser.parse_args()
    ARRAY_URI = "database/daily_rainfall_optimized"
    
    if args.init:
        create_daily_rainfall_array(ARRAY_URI, 1520, 2288, [0.002245, 0.0, -160.25, 0.0, -0.002245, 22.25], "EPSG:4326")

    if args.start and args.end:
        all_dates = generate_date_list(args.start, args.end)
        total_success = 0
        for i in range(0, len(all_dates), args.batch_size):
            batch = all_dates[i:i + args.batch_size]
            total_success += ingest_batch(batch, ARRAY_URI)
        print(f"\nFinal Success: {total_success}/{len(all_dates)} days.")
