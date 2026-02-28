import os
from google import genai
from google.genai import types

def run_chatbot():
    client = genai.Client()
    MODEL_ID = "gemini-2.0-flash"

    # 1. Fetch uploaded files
    print("Fetching active uploaded files...")
    all_files = []
    try:
        for file in client.files.list():
            if file.state.name == 'ACTIVE':
                all_files.append(file)
            else:
                print(f"Skipping {file.display_name} (State: {file.state})")
    except Exception as e:
        print(f"Error fetching files: {e}")
        return

    # 2. Filter and deduplicate files
    # Exclude common non-content files
    EXCLUDE_PATTERNS = ['license', 'readme', 'authors', 'vendor', 'entry_points', '.txt.txt']
    
    filtered_files = {}
    ignored_count = 0
    
    for f in all_files:
        name_lower = f.display_name.lower()
        if any(pat in name_lower for pat in EXCLUDE_PATTERNS):
            ignored_count += 1
            continue
        
        # Deduplicate by display_name, keeping the latest (list() usually returns newest first or consistent order)
        if f.display_name not in filtered_files:
            filtered_files[f.display_name] = f
        else:
            ignored_count += 1

    files = list(filtered_files.values())

    if not files:
        print("No suitable active files found. Running without additional context.")
    else:
        print(f"Context optimized: Using {len(files)} files (Ignored/Deduplicated {ignored_count} files).")
        for f in files:
            print(f" - {f.display_name}")

    # 3. Initialize chat session with files as context
    # Note: We provide the files in the history or as initial context parts.
    # In the current SDK, we can start a chat and pass the files in the first message or as context.
    chat = client.chats.create(model=MODEL_ID)

    print("\n--- CHATBOT READY ---")
    print("Type 'exit' or 'quit' to end the session.\n")

    history_with_files = False

    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        if not user_input.strip():
            continue

        try:
            # If it's the first message, include the files for context
            if not history_with_files:
                contents = files + [user_input]
                response = chat.send_message(message=contents)
                history_with_files = True
            else:
                response = chat.send_message(user_input)
            
            print(f"\nGemini: {response.text}\n")
        except Exception as e:
            print(f"Error during chat: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_chatbot()
