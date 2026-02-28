import argparse
import sys
from google import genai
from google.genai import types

def main():
    parser = argparse.ArgumentParser(description="Manage uploaded files on Gemini File API")
    parser.add_argument("--list", action="store_true", help="List all uploaded files (default)")
    parser.add_argument("--delete", type=str, help="Display Name or UUID of the file to delete")
    
    args = parser.parse_args()
    client = genai.Client()

    if args.delete:
        target = args.delete
        print(f"Searching for file matching: {target}...")
        
        found = False
        # The API usually identifies files by their unique 'name' (UUID-like)
        # but we allow users to seek by display_name too.
        for file in client.files.list():
            if target == file.name or target == file.display_name:
                print(f"Deleting file: {file.display_name} (ID: {file.name})...")
                client.files.delete(name=file.name)
                print("Successfully deleted.")
                found = True
                # Don't break if delete multiple files with same display name
        
        if not found:
            print(f"Error: No file found with name/display_name '{target}'")
    
    else:
        # Default action: list files
        print("Fetching uploaded files...")
        count = 0
        for file in client.files.list():
            print(f" - {file.display_name}")
            print(f"   UUID: {file.name} | State: {file.state.name} | Created: {file.created}")
            print("-" * 40)
            count += 1
        
        if count == 0:
            print("No files found.")
        else:
            print(f"\nTotal files: {count}")

if __name__ == "__main__":
    main()
