# Gemini interaction

This directory contains scripts for interacting with the Gemini API using the `google-genai` File API.

Detailed documentation on the agent's capabilities and its underlying technical architecture can be found in [AGENT_TOOLS.md](file:///c:/SCIPE/HCDP-data-for-AI/gemini_chat/AGENT_TOOLS.md).


## Scripts

### 1. `server.py` (Backend API)
FastAPI-based backend that exposes the LangChain agent as a REST API for integration with the React frontend.
- **Functionality**:
    - **Session Management**: Maintains conversation history across multiple API calls using `session_id`.
    - **Static Content**: Serves generated interactive maps (HTML) via the `/maps` endpoint.
    - **CORS Enabled**: Configured for seamless communication with the frontend dev server.
- **Usage**: `python server.py` (Starts on `http://127.0.0.1:8000`)

### 2. `langchain_agent.py` (Recommended Agent)
A modern LangChain-based agent that uses local scripts and TileDB as tools to answer climate questions and generate maps.
- **Functionality**:
    - **Geocoding**: Automatically resolves place names (e.g., "Honolulu") using `geopy`.
    - **Station Finder**: Finds weather stations within a specified radius.
    - **Interactive Mapping**: Generates station maps and unified gridded maps for all supported variables.
    - **TileDB Climate Queries**: Performs pixel-perfect historical lookups for **Rainfall, Temperature (Mean/Max/Min), and SPI** for any coordinate in Hawaii.
    - **Intelligent Defaults**: Automatically applies a **5.0 km radius** and the **current year (2026)** to requests if they are not explicitly provided.
    - **Tool Chaining**: Executes multi-step workflows (e.g., Geocode -> Query -> Map) in a single turn.
- **Usage**: `python langchain_agent.py` (CLI interactive mode)

## Requirements
- Python **3.14+** compatible (uses `bind_tools` pattern).
- Libraries: `langchain`, `langchain-google-genai`, `geopy`, `pandas`, `folium`, `rasterio`.
- An active Google Gemini API Key (`GOOGLE_API_KEY`) configured in a `.env` file.
