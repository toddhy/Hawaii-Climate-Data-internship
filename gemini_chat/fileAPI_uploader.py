import pathlib
import argparse
import sys
from google import genai
from google.genai import types

def main():
    parser = argparse.ArgumentParser(description="Upload .txt files to GenAI File API")
    parser.add_argument("--path", type=str, required=True, help="Path to search for .txt files")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()

    client = genai.Client()
    MODEL_ID = "gemini-2.5-flash"

    files = []
    path_to_search = args.path
    print(f"Uploading files from {path_to_search}...")

    # Searching for files
    search_path = pathlib.Path(path_to_search)
    if not search_path.exists():
        print(f"Error: Path {path_to_search} does not exist.")
        return

    files_to_upload = []
    if search_path.is_file():
        files_to_upload.append(search_path)
    else:
        # Searching for .txt files in directory
        for p in search_path.rglob('*.txt'):
            if 'test' in str(p):
                continue
            files_to_upload.append(p)

    for p in files_to_upload:
        try:
            # Gemini File API workaround: .json files must be text/plain to be used as context
            mime_type = 'text/plain' if p.suffix.lower() == '.json' else None
            
            f = client.files.upload(
                file=p, 
                config={
                    'display_name': p.name,
                    'mime_type': mime_type
                }
            )
            files.append(f)
            print('.', end='', flush=True)
        except Exception as e:
            print(f"\nError uploading {p}: {e}")

    if not files:
        print("\nNo files found to upload! Check the path and file type.")
        return

    print(f"\nUploaded {len(files)} files.")

    

if __name__ == "__main__":
    main()