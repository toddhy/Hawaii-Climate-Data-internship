# Gemini interaction

This directory contains scripts for interacting with the Gemini API using the `google-genai` File API.

## Scripts

### 1. `fileAPI_uploader.py`
Uploads local text files to the Gemini File API.
Documentation on file uploading here: https://ai.google.dev/api/files and https://ai.google.dev/gemini-api/docs/file-input-methods


- **Functionality**: Scans a directory for `.txt` files and uploads them.
- **CLI Argument**: accepts `--path` to specify the search directory (defaults to current directory).
- **Initial Prompt**: Generates an initial summary of uploaded texts.
- **Usage**: `python fileAPI_uploader.py --path /your/data/folder`

### 2. `chatbot.py`
Continuous chat session using all active uploaded files as context.
- **Functionality**: Fetches active files and starts an interactive chat.
- **Memory**: Maintains conversation history within the session.
- **Usage**: `python chatbot.py`

### 3. `prompt_existing.py`
Single-turn interaction with already uploaded files.
- **Functionality**: Fetches `ACTIVE` files and prompts for a single question.
- **Usage**: `python prompt_existing.py`

### 4. `langchain_agent.py` (Recommended Agent)
A modern LangChain-based agent that uses local scripts as tools.
- **Functionality**:
    - **Geocoding**: Automatically resolves place names (e.g., "Honolulu") using `geopy`.
    - **Station Finder**: Finds weather stations within a specified radius.
    - **Interactive Mapping**: Generates station maps and unified gridded rainfall maps.
    - **TileDB Climate Queries**: Performs pixel-perfect historical lookups (Rainfall/Temperature) for any coordinate in Hawaii using the high-performance database.
    - **Intelligent Defaults**: Automatically applies a **5.0 km radius** and the **current year (2026)** to map requests if they are not explicitly provided by the user.
    - **Tool Chaining**: Executes multi-step workflows in a single turn.
- **Usage**: `python langchain_agent.py`

## Requirements
- Python **3.14+** compatible (uses `bind_tools` pattern).
- Libraries: `langchain`, `langchain-google-genai`, `geopy`, `pandas`, `folium`, `rasterio`.
- An active Google Gemini API Key (`GOOGLE_API_KEY`) configured in a `.env` file.
