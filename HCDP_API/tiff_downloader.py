"""
HCDP TIFF Downloader Utility

This script facilitates batch downloading GeoTIFF raster data from the Hawaii Climate Data Portal (HCDP) API.
It supports both monthly and daily data for various climate variables.

Usage (Monthly):
    python tiff_downloader.py 2022-01 2022-12 --datatype rainfall

Usage (Daily):
    python tiff_downloader.py 2026-01-01 2026-04-01 --datatype rainfall

The API requires an authentication token, which should be set in the HCDP_API_TOKEN environment variable.
"""

import os
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Load environment variables (for API token)
load_dotenv()

# --- Configuration ---
API_URL = "https://api.hcdp.ikewai.org/raster"
AUTH_TOKEN = os.getenv("HCDP_API_TOKEN")

def download_tiff(date_str, output_path, datatype='rainfall', period='month'):
    """
    Downloads a single TIFF file for a specific date from the HCDP API.

    Args:
        date_str (str): The date string in YYYY-MM or YYYY-MM-DD format.
        output_path (str): The local file path to save the downloaded TIFF.
        datatype (str): The climate variable to download (e.g., 'rainfall', 'temperature').
        period (str): The time resolution of the data ('month' or 'day').

    Returns:
        bool: True if the download was successful, False otherwise.
    """
    params = {
        'date': date_str,
        'location': 'hawaii',
        'returnEmptyNotFound': 'false',
        'datatype': datatype,
        'extent': 'statewide',
        'period': period,
    }
    
    # Optional parameters based on datatype
    if datatype == 'rainfall':
        params['production'] = 'new'
    elif datatype == 'temperature':
        # params['aggregation'] = 'mean' # could be min/max/mean
        pass
    
    headers = {
        'accept': 'image/tif',
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }

    try:
        print(f"Downloading {date_str}...")
        response = requests.get(API_URL, params=params, headers=headers, stream=True)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  Saved to {output_path}")
            return True
        else:
            print(f"  Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Batch download TIFFs from HCDP API.")
    parser.add_argument("start_date", help="Start date (YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (YYYY-MM or YYYY-MM-DD)")
    parser.add_argument("--datatype", default="rainfall", help="Data type: rainfall, temperature, etc. (default: rainfall)")
    parser.add_argument("--output_dir", default="downloads", help="Directory to save TIFFs (default: downloads)")
    
    args = parser.parse_args()

    if not AUTH_TOKEN:
        print("Error: HCDP_API_TOKEN environment variable is not set.")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created directory: {args.output_dir}")

    # Detect format and parse dates
    is_daily = len(args.start_date) == 10 # YYYY-MM-DD is 10 chars
    date_format = "%Y-%m-%d" if is_daily else "%Y-%m"
    period = "day" if is_daily else "month"

    try:
        current_date = datetime.strptime(args.start_date, date_format)
        end_date = datetime.strptime(args.end_date, date_format)
    except ValueError:
        print(f"Error: Dates must be in {date_format} format.")
        return

    while current_date <= end_date:
        date_str = current_date.strftime(date_format)
        file_name = f"{date_str}.tiff"
        output_path = os.path.join(args.output_dir, file_name)
        
        download_tiff(date_str, output_path, datatype=args.datatype, period=period)
        
        # Increment
        if is_daily:
            current_date += timedelta(days=1)
        else:
            current_date += relativedelta(months=1)

    print("Batch download complete.")

if __name__ == "__main__":
    main()
