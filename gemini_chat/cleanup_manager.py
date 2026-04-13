import os
import time
import glob

def cleanup_outputs(max_age_hours=24):
    """
    Deletes HTML files in the outputs directory that are older than max_age_hours.
    """
    # Dynamic path resolution to find outputs directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    outputs_dir = os.path.join(project_root, "outputs")
    
    if not os.path.exists(outputs_dir):
        return 0

    now = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0

    # Look for all .html files in the outputs directory
    # Note: we only target .html to avoid deleting .gitkeep or other important files
    files = glob.glob(os.path.join(outputs_dir, "*.html"))
    
    for f in files:
        try:
            # Check modification time
            file_age = now - os.path.getmtime(f)
            if file_age > max_age_seconds:
                os.remove(f)
                deleted_count += 1
        except Exception as e:
            # Skip if file is being used or other error
            print(f"[!] Maintenance Warning: Could not delete {os.path.basename(f)}: {e}")

    if deleted_count > 0:
        print(f"[*] Maintenance: Cleaned up {deleted_count} stale visualization(s) older than {max_age_hours}h.")
    
    return deleted_count

if __name__ == "__main__":
    # Allow running manually if needed
    import argparse
    parser = argparse.ArgumentParser(description="Clean up old generated maps and graphs.")
    parser.add_argument("--age", type=int, default=24, help="Max age in hours (default: 24)")
    args = parser.parse_args()
    
    print(f"[*] Checking for files older than {args.age} hours...")
    count = cleanup_outputs(args.age)
    if count == 0:
        print("[*] No stale files found.")
