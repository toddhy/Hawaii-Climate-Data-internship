import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

# 1. Setup Environment and Paths
load_dotenv()

# Add project root and HCDP_API directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HCDP_API_DIR = os.path.join(PROJECT_ROOT, "HCDP_API")

for path in [PROJECT_ROOT, HCDP_API_DIR]:
    if path not in sys.path:
        sys.path.append(path)

# Import HCDP_API modules
try:
    from HCDP_API.station_finder import get_nearby_stations
    from HCDP_API.map_HCDP_stations import create_station_map
    from HCDP_API.map_visualizer import create_unified_map
except ImportError as e:
    print(f"[!] Warning: Could not import HCDP_API modules ({e}). Tools may be disabled.")
    get_nearby_stations = None
    create_station_map = None
    create_unified_map = None

# Import geopy
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeopyError
except ImportError as e:
    print(f"[!] Warning: Could not import geopy ({e}). Geocoding will be disabled.")
    Nominatim = None
    GeopyError = None

# Initialize Geocoder with a user agent
geolocator = None
if Nominatim:
    try:
        geolocator = Nominatim(user_agent="hcdp_agent_assistant")
        print("[*] Geocoder initialized successfully.")
    except Exception as e:
        print(f"[!] Warning: Failed to initialize Nominatim geocoder ({e}). Geocoding tool will be restricted.")
else:
    print("[!] Warning: Geocoding is disabled (geopy missing).")

# 2. Define the Tools
@tool
def geocode_placename(place_name: str) -> str:
    """
    Converts a place name (e.g., 'Honolulu', 'Hilo Airport') into latitude and longitude coordinates.
    Returns a string with latitude and longitude, or an error message if not found.
    Use this tool automatically when a user mentions a place name instead of coordinates.
    """
    if geolocator is None:
        return "Error: Geocoder not initialized."
    try:
        location = geolocator.geocode(place_name)
        if location:
            return f"Latitude: {location.latitude}, Longitude: {location.longitude} (Resolved from: {place_name})"
        return f"Could not find coordinates for: {place_name}"
    except GeopyError as e:
        return f"Geocoding error: {str(e)}"

@tool
def find_nearby_stations(latitude: float, longitude: float, radius_km: float = 10.0) -> str:
    """
    Finds weather stations within a specified kilometer radius of a given latitude and longitude.
    Returns a string representation of the stations found, including their ID (skn), name, and distance.
    """
    if get_nearby_stations is None:
        return "Error: station_finder utility not found."
    
    try:
        results = get_nearby_stations(latitude, longitude, radius_km)
        if results.empty:
            return f"No stations found within {radius_km}km of ({latitude}, {longitude})."
        
        # Format the DataFrame for the agent
        return results[['skn', 'name', 'distance_km']].to_string(index=False)
    except Exception as e:
        return f"Error finding stations: {str(e)}"

@tool
def map_nearby_stations(latitude: float, longitude: float, radius_km: float = 10.0) -> str:
    """
    Finds weather stations within a specified kilometer radius and generates an interactive HTML map.
    Returns the file path of the generated map.
    Useful when the user wants to see the stations on a map.
    """
    if create_station_map is None or get_nearby_stations is None:
        return "Error: Mapping tools not properly initialized."
    try:
        results = get_nearby_stations(latitude, longitude, radius_km)
        if results.empty:
            return f"No stations found to map within {radius_km}km of ({latitude}, {longitude})."
        
        map_path = create_station_map(results)
        return f"Interactive map created successfully: {map_path}"
    except Exception as e:
        return f"Error creating map: {str(e)}"

@tool
def generate_gridded_rainfall_map(latitude: float, longitude: float, radius_km: float = 10.0, use_existing_rainfall_data: bool = False) -> str:
    """
    Generates a unified rainfall map with a gridded raster overlay and station markers.
    The raster data is aggregated from local TIFF files. 
    If use_existing_rainfall_data is True, it tries to use 'station_rainfall_data.json' for colored markers.
    Otherwise, it fetches just station locations (grey markers) and combines them with the raster overlay.
    Useful when the user wants a detailed rainfall visualization with both markers and grids.
    """
    if create_unified_map is None:
        return "Error: Unified mapping utility not found."
    
    output_file = "gridded_rainfall_map.html"
    try:
        # Use absolute paths for reliability
        json_path = os.path.join(HCDP_API_DIR, "station_rainfall_data.json") if use_existing_rainfall_data else None
        tiff_dir = os.path.join(HCDP_API_DIR, "downloads")
        output_file_abs = os.path.join(PROJECT_ROOT, output_file)

        create_unified_map(
            json_path=json_path,
            tiff_dir=tiff_dir,
            output_file=output_file_abs,
            center_lat=latitude,
            center_lon=longitude,
            radius_km=radius_km,
            omit_json_data=not use_existing_rainfall_data
        )
        return f"Gridded rainfall map generated successfully: {output_file_abs}"
    except Exception as e:
        return f"Error creating gridded map: {str(e)}"

# 3. Simple Tool-Calling Loop (Modern Pattern)
def run_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[!] ERROR: GOOGLE_API_KEY not found.")
        return

    # Initialize Gemini 2.0 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0
    )

    # Bind tools to the LLM
    tools = [geocode_placename, find_nearby_stations, map_nearby_stations, generate_gridded_rainfall_map]
    llm_with_tools = llm.bind_tools(tools)
    
    # Simple message history
    messages = []

    print("\n--- HCDP LangChain Agent Ready (Gridded Mapping Enabled) ---")
    print("Example: 'Create a gridded rainfall map for Honolulu'")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        if not user_input.strip():
            continue

        messages.append(HumanMessage(content=user_input))
        
        try:
            # 1. Ask LLM
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
            # 2. Check for Tool Calls (Loop for tool chaining)
            while response.tool_calls:
                for tool_call in response.tool_calls:
                    # Find the tool
                    tool_map = {
                        "geocode_placename": geocode_placename,
                        "find_nearby_stations": find_nearby_stations,
                        "map_nearby_stations": map_nearby_stations,
                        "generate_gridded_rainfall_map": generate_gridded_rainfall_map
                    }
                    selected_tool = tool_map[tool_call["name"]]
                    
                    # Execute tool
                    print(f"[*] Calling tool: {tool_call['name']}({tool_call['args']})")
                    tool_output = selected_tool.invoke(tool_call)
                    
                    # Add tool result to history
                    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
                
                # Get next response from LLM (to handle tool results or multi-step tasks)
                response = llm_with_tools.invoke(messages)
                messages.append(response)
                
            print(f"\nAgent: {response.content}")

        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    run_agent()
