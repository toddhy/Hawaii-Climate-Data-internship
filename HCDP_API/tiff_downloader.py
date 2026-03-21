"""
Takes a start and end date in YYYY-MM format and downloads rainfall TIFF files for each month in that range. 
The data is from https://api.hcdp.ikewai.org/raster/timeseries
example: python tiff_downloader.py 2022-01 2022-12
"""

import os
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Load environment variables (for API token)
load_dotenv()

# --- Configuration ---
API_URL = "https://api.hcdp.ikewai.org/raster"
AUTH_TOKEN = os.getenv("HCDP_API_TOKEN")

def download_tiff(date_str, output_path):
    """
    Downloads a single TIFF file for a specific date from the HCDP API.
    """
    params = {
        'date': date_str,
        'location': 'hawaii',
        'returnEmptyNotFound': 'false',
        'datatype': 'temperature',
        'extent': 'statewide',
        #'production': 'new', #for rainfall only. values new/legacy
        'period': 'month',
        'aggregation': 'min' #for temperature, comment out otherwise. values min/max/mean
    }
    
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
    parser = argparse.ArgumentParser(description="Batch download rainfall TIFFs from HCDP API.")
    parser.add_argument("start_date", help="Start date (YYYY-MM)")
    parser.add_argument("end_date", help="End date (YYYY-MM)")
    parser.add_argument("--output_dir", default="downloads", help="Directory to save TIFFs (default: downloads)")
    
    args = parser.parse_args()

    if not AUTH_TOKEN:
        print("Error: HCDP_API_TOKEN environment variable is not set.")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created directory: {args.output_dir}")

    # Parse dates
    try:
        current_date = datetime.strptime(args.start_date, "%Y-%m")
        end_date = datetime.strptime(args.end_date, "%Y-%m")
    except ValueError:
        print("Error: Dates must be in YYYY-MM format.")
        return

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m")
        file_name = f"{date_str}.tiff"
        output_path = os.path.join(args.output_dir, file_name)
        
        download_tiff(date_str, output_path)
        
        # Increment month
        current_date += relativedelta(months=1)

    print("Batch download complete.")

if __name__ == "__main__":
    main()
