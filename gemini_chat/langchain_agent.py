import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage

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
def find_nearby_stations(latitude: float, longitude: float, radius_km: float = 5.0) -> str:
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
def map_nearby_stations(latitude: float, longitude: float, radius_km: float = 5.0) -> str:
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
def generate_gridded_map(latitude: float = None, longitude: float = None, radius_km: float = None, data_type: str = 'rainfall', add_stations: bool = False, statewide: bool = False, start_date: str = None, end_date: str = None, use_existing_json: bool = True) -> str:
    """
    Generates a unified map (rainfall or temperature) with a gridded raster overlay.
    IMPORTANT: If a location name is given (e.g. 'Honolulu'), you MUST use geocode_placename first to get latitude/longitude.
    Args:
        latitude, longitude: Center of the map. REQUIRED unless statewide=True.
        radius_km: Radius for clipping/masking (default is dynamic/5km).
        data_type: 'rainfall' or 'temperature' (default: 'rainfall').
        add_stations: Whether to include weather station markers (default: False).
        statewide: If True, maps the entire state of Hawaii (ignores radius/center).
        start_date: Start date for data aggregation (format: YYYY-MM).
        end_date: End date for data aggregation (format: YYYY-MM).
        use_existing_json: Whether to use 'station_rainfall_data.json' for station markers (default: True).
    """
    if create_unified_map is None:
        return "Error: Unified mapping utility not found."
    
    output_file = "gridded_map.html"
    # Apply Defaults
    if radius_km is None and not statewide:
        radius_km = 5.0
    
    if start_date is None and end_date is None:
        start_date = '2026-01'
        end_date = '2026-12'

    try:
        # Use absolute paths for reliability
        json_path = os.path.join(HCDP_API_DIR, "station_rainfall_data.json")
        output_file_abs = os.path.join(PROJECT_ROOT, output_file)

        create_unified_map(
            json_path=json_path if use_existing_json else None,
            tiff_dir=None, # use defaults
            output_file=output_file_abs,
            center_lat=latitude,
            center_lon=longitude,
            radius_km=radius_km,
            omit_json_data=not use_existing_json,
            add_stations=add_stations,
            statewide=statewide,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date
        )
        return f"Unified {data_type} map generated successfully: {output_file_abs}"
    except Exception as e:
        return f"Error creating unified map: {str(e)}"

@tool
def query_historical_climate_data(latitude: float, longitude: float, month: str, variable: str = 'temperature') -> str:
    """
    Queries the high-performance TileDB database for exact historical historical climate data (average temperature or rainfall) 
    at a specific coordinate for a given month.
    IMPORTANT: If a location name is given (e.g. 'Honolulu'), you MUST use geocode_placename first to get latitude/longitude.
    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        month: The month to query, strictly formatted as 'YYYY-MM' (e.g. '1995-05').
        variable: The type of data to query: 'temperature' (Celsius) or 'rainfall' (mm). Defaults to 'temperature'.
    """
    try:
        from database.tiledb_access import get_metadata, get_data_for_month
        import numpy as np
        
        # Select the correct array based on the requested variable
        array_name = "temperature_array" if variable.lower() == "temperature" else "rainfall_array"
        unit = "degrees Celsius" if variable.lower() == "temperature" else "mm"
        
        db_path = os.path.join(PROJECT_ROOT, "database", array_name)
        if not os.path.exists(db_path):
            return f"Error: TileDB database for {variable} not found."
            
        meta = get_metadata(db_path)
        transform = meta["transform"] 
        a, b, c, d, e, f = transform
        
        # Calculate pixel coordinates dynamically via affine inverse for north-up raster
        col = int((longitude - c) / a)
        row = int((latitude - f) / e)
        
        if col < 0 or col >= meta["width"] or row < 0 or row >= meta["height"]:
            return f"Error: Coordinates ({latitude}, {longitude}) are outside the bounds of the Hawaii database."
            
        data = get_data_for_month(db_path, month)
        
        val = data[row, col]
        if np.isnan(val):
            return f"No {variable} data available at ({latitude}, {longitude}) for {month} (likely over ocean)."
            
        return f"The average {variable} at ({latitude}, {longitude}) for {month} was {val:.2f} {unit}."
            
    except Exception as err:
        return f"Error querying TileDB database: {str(err)}"

# 3. Simple Tool-Calling Loop & API Support
llm_with_tools = None

DEFAULT_SYSTEM_PROMPT = """You are the HCDP Assistant, a helpful AI specialized in Hawaii climate data.
Follow these constraints strictly:
1. Always be polite, concise, and professional.
2. If the user asks for weather maps, identify their location first using geocoding if coordinates aren't provided.
3. Only use the tools provided to you. If a user asks about topics completely unrelated to weather, geography, or climate in Hawaii, politely redirect them back to your specialty.
4. Only search for locations within the state of Hawaii.
5. If a place name exists outside of Hawaii, use the Hawaii one. 
6. If no date or only year is provided, default to January through December of the current year (2026).
7. Default the map radius to 5km if not specified.
8. For specific historical climate queries (temperature or rainfall), use the query_historical_climate_data tool after finding the coordinates.
9. If statewide is False, radius_km must be at least 1.0 (default 5.0).
"""

def initialize_agent():
    global llm_with_tools
    if llm_with_tools is not None:
        return
        
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
    tools = [geocode_placename, find_nearby_stations, map_nearby_stations, generate_gridded_map, query_historical_climate_data]
    llm_with_tools = llm.bind_tools(tools)
    print("[*] Agent initialized with tools.")

def chat_with_agent(user_input: str, messages: list):
    """
    Takes user_input and an existing messages list.
    Returns (assistant_reply_text, updated_messages_list, new_map_path)
    """
    if llm_with_tools is None:
        initialize_agent()
        
    # Inject system prompt if this is a fresh conversation
    if not messages:
        messages.append(SystemMessage(content=DEFAULT_SYSTEM_PROMPT))
        
    messages.append(HumanMessage(content=user_input))
    new_map_path = None
    
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
                    "generate_gridded_map": generate_gridded_map,
                    "query_historical_climate_data": query_historical_climate_data
                }

                selected_tool = tool_map[tool_call["name"]]
                
                # Execute tool
                print(f"[*] Calling tool: {tool_call['name']}({tool_call['args']})")
                tool_output = selected_tool.invoke(tool_call)
                
                # If tool created a map, extract its path for the UI
                output_str = str(tool_output)
                if "html" in output_str.lower() and os.path.exists("gridded_map.html"):
                    new_map_path = os.path.abspath("gridded_map.html")
                elif "html" in output_str.lower() and "Interactive map created" in output_str:
                    # simplistic extraction, map_nearby_stations returns path at the end
                    potential_path = output_str.split(": ")[-1].strip()
                    if os.path.exists(potential_path):
                        new_map_path = potential_path
                elif "unified map generated" in output_str.lower():
                    potential_path = output_str.split(": ")[-1].strip()
                    if os.path.exists(potential_path):
                        new_map_path = potential_path

                # Add tool result to history
                messages.append(ToolMessage(content=output_str, tool_call_id=tool_call["id"]))
            
            # Get next response from LLM (to handle tool results or multi-step tasks)
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
        return response.content, messages, new_map_path
    except Exception as e:
        print(f"\nError: {e}")
        return f"Error: {e}", messages, None

def run_agent():
    initialize_agent()
    if llm_with_tools is None:
        return
    
    # Initialize message history with the system prompt
    messages = [SystemMessage(content=DEFAULT_SYSTEM_PROMPT)]

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
                        "generate_gridded_map": generate_gridded_map,
                        "query_historical_climate_data": query_historical_climate_data
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
