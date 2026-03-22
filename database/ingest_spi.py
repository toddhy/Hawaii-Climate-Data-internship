import os
import sys
import subprocess

# Add the database directory to path to import tiledb_ingest if needed, 
# although we'll just call it via subprocess for simplicity and to avoid path issues.

DATABASE_DIR = r"c:\SCIPE\HCDP-data-for-AI\database"
SPI_DIR = r"c:\SCIPE\HCDP-data-for-AI\HCDP_API\spi"
ARRAY_URI = os.path.join(DATABASE_DIR, "spi_array")
INGEST_SCRIPT = os.path.join(DATABASE_DIR, "tiledb_ingest.py")

def run_ingestion():
    if not os.path.exists(INGEST_SCRIPT):
        print(f"Error: Ingestion script not found at {INGEST_SCRIPT}")
        return

    print(f"Starting SPI data ingestion from {SPI_DIR} to {ARRAY_URI}...")
    
    # We run in a loop because tiledb_ingest.py limits to 120 files per run on Windows 
    # to avoid fragment locking/memory issues.
    max_loops = 10 
    for i in range(max_loops):
        print(f"\n--- Batch Run {i+1} ---")
        result = subprocess.run([
            sys.executable, INGEST_SCRIPT, 
            "--input_dir", SPI_DIR, 
            "--array_uri", ARRAY_URI
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
        if "No TIFF files found" in result.stdout or "already ingested in array" in result.stdout and "Limiting to 120 files" not in result.stdout:
            # If we didn't limit to 120, it means we finished all remaining files.
            # But the script always prints "already ingested" for skipped files.
            # If it doesn't say "Loading X files" and just says skipping, we are done.
            if "Loading 0 files" in result.stdout or "Skipping" in result.stdout and "Loading" not in result.stdout:
                 print("All files processed.")
                 break
        
        # A more reliable check: if "Successfully finished ingestion" is in stdout 
        # but it didn't find any NEW files to ingest.
        if "Loading" not in result.stdout and "Successfully finished ingestion" in result.stdout:
            print("All files already ingested or no new files found.")
            break

if __name__ == "__main__":
    run_ingestion()
