import os
import sys
import requests
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
import pandas as pd

# 1. Setup Environment and Paths
load_dotenv()

# Add project root and HCDP_API directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HCDP_API_DIR = os.path.join(PROJECT_ROOT, "HCDP_API")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

# Ensure outputs directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

for path in [PROJECT_ROOT, HCDP_API_DIR]:
    if path not in sys.path:
        sys.path.append(path)

# Import HCDP_API modules (isolated to prevent one failure from disabling all tools)
try:
    from HCDP_API.station_finder import get_nearby_stations
except ImportError as e:
    print(f"[!] Warning: Could not import station_finder ({e})")
    get_nearby_stations = None

try:
    from HCDP_API.map_HCDP_stations import create_station_map
except ImportError as e:
    print(f"[!] Warning: Could not import map_HCDP_stations ({e})")
    create_station_map = None

try:
    from HCDP_API.map_visualizer import create_unified_map
except ImportError as e:
    print(f"[!] Warning: Could not import map_visualizer ({e})")
    create_unified_map = None

try:
    # Attempt to import from the HCDP_API package
    try:
        from HCDP_API.graph_generator import create_climatogram_file
    except (ImportError, ModuleNotFoundError):
        # Fallback for different path structures
        from graph_generator import create_climatogram_file
    
    print("[*] graph_generator imported successfully.")
except Exception as e:
    print(f"[!] Warning: Could not import graph_generator. Climatogram tool will be disabled. Reason: {e}")
    create_climatogram_file = None

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
def map_nearby_stations(latitude: float, longitude: float, radius_km: float = 5.0, session_id: str = "default") -> str:
    """
    Finds weather stations within a specified kilometer radius and generates an interactive HTML map.
    Returns the file path of the generated map.
    Use this tool ONLY when the user wants a simple view of station locations WITHOUT any raster/gridded data overlays.
    """
    if create_station_map is None or get_nearby_stations is None:
        return "Error: Mapping tools not properly initialized."
    try:
        results = get_nearby_stations(latitude, longitude, radius_km)
        if results.empty:
            return f"No stations found to map within {radius_km}km of ({latitude}, {longitude})."
        
        
        # Use session_id for unique filenames
        clean_sid = "".join(x for x in str(session_id) if x.isalnum())
        output_file = f"stations_{clean_sid}.html" if clean_sid else "station_map.html"
        output_file_abs = os.path.join(OUTPUTS_DIR, output_file)
        
        map_path = create_station_map(results, output_file=output_file_abs)
        return f"Interactive map created successfully: {output_file_abs}"
    except Exception as e:
        return f"Error creating map: {str(e)}"

@tool
def generate_gridded_map(latitude: float = None, longitude: float = None, radius_km: float = None, data_type: str = 'rainfall', add_stations: bool = False, statewide: bool = False, start_date: str = None, end_date: str = None, use_existing_json: bool = True, session_id: str = "default") -> str:
    """
    Generates a unified map (rainfall or temperature) with a gridded raster overlay.
    IMPORTANT: If a location name is given (e.g. 'Honolulu'), you MUST use geocode_placename first to get latitude/longitude.
    Args:
        latitude, longitude: Center of the map. REQUIRED unless statewide=True.
        radius_km: Radius for clipping/masking (default is dynamic/5km).
        data_type: 'rainfall' or 'temperature' or 'spi' (default: 'rainfall').
        add_stations: Set to True if the user mentions 'stations', 'markers', 'sensors', or 'locations' on the map. (default: False).
        statewide: If True, maps the entire state of Hawaii (ignores radius/center).
        start_date: Start date for data aggregation (format: YYYY-MM or YYYY-MM-DD).
        end_date: End date for data aggregation (format: YYYY-MM or YYYY-MM-DD).
        use_existing_json: Whether to use 'station_rainfall_data.json' for station markers (default: True).
    """
    if create_unified_map is None:
        return "Error: Unified mapping utility not found."
    
    # Use session_id for unique filenames
    clean_sid = "".join(x for x in str(session_id) if x.isalnum())
    output_file = f"map_{clean_sid}.html" if clean_sid else "gridded_map.html"
    # Apply Defaults
    if radius_km is None and not statewide:
        radius_km = 5.0
    
    if start_date is None and end_date is None:
        start_date = '2026-01'
        end_date = '2026-12'

    # Auto-detect daily precision (YYYY-MM-DD vs YYYY-MM)
    is_daily = False
    if start_date and len(start_date.split('-')) == 3:
        is_daily = True
    
    if is_daily and data_type == 'rainfall':
        data_type = 'daily_rainfall'

    try:
        # Use absolute paths for reliability
        json_path = os.path.join(HCDP_API_DIR, "station_rainfall_data.json")
        output_file_abs = os.path.join(OUTPUTS_DIR, output_file)

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
        variable: The type of data to query: 'temperature' (Celsius), 'rainfall' (mm), or 'spi' (Standardized Precipitation Index). Defaults to 'temperature'.
    """
    try:
        from database.tiledb_access import get_metadata, get_data_for_month
        import numpy as np
        
        # Select the correct array based on the requested variable
        if variable.lower() == "temperature":
            array_name = "temperature_array"
            unit = "degrees Celsius"
        elif variable.lower() == "max_temp":
            array_name = "max_temp_array"
            unit = "degrees Celsius"
        elif variable.lower() == "min_temp":
            array_name = "min_temp_array"
            unit = "degrees Celsius"
        elif variable.lower() == "spi":
            array_name = "spi_array"
            unit = "units (SPI)"
        else:
            array_name = "rainfall_array"
            unit = "mm"
        
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

@tool
def query_historical_timeseries(latitude: float, longitude: float, start_date: str, end_date: str, radius_km: float = 5.0, variable: str = 'rainfall') -> str:
    """
    Queries the high-performance TileDB database for a summarized time-series of climate data over a date range.
    Use this tool when the user asks for data over multiple months or years (e.g., '2010-2015').
    IMPORTANT: If a location name is given (e.g. 'Honolulu'), you MUST use geocode_placename first.
    Args:
        latitude, longitude: Center coordinates of the area of interest.
        start_date, end_date: Strictly formatted as 'YYYY-MM' (e.g. '2008-01' to '2021-12').
        radius_km: Radius in kilometers to average the data over (default 5.0 km).
        variable: 'rainfall' (mm), 'temperature' (Celsius), or 'spi'. Defaults to 'rainfall'.
    """
    try:
        from database.tiledb_access import get_metadata, get_timeseries_for_region
        import numpy as np
        
        # Select the correct array
        if variable.lower() == "temperature":
            array_name = "temperature_array"
            unit = "Celsius"
        elif variable.lower() == "max_temp":
            array_name = "max_temp_array"
            unit = "Celsius"
        elif variable.lower() == "min_temp":
            array_name = "min_temp_array"
            unit = "Celsius"
        elif variable.lower() == "spi":
            array_name = "spi_array"
            unit = "SPI"
        else:
            array_name = "rainfall_array"
            unit = "mm"
        
        db_path = os.path.join(PROJECT_ROOT, "database", array_name)
        if not os.path.exists(db_path):
            return f"Error: TileDB database for {variable} not found."
            
        meta = get_metadata(db_path)
        a, b, c, d, e, f = meta["transform"]
        
        # Center pixel
        center_col = int((longitude - c) / a)
        center_row = int((latitude - f) / e)
        
        # Convert radius_km to degrees (approximate)
        # Hawaii approx: 1 deg lat = 111km, 1 deg lon = 104km
        deg_lat = radius_km / 111.0
        deg_lon = radius_km / 104.0
        
        # Pixel delta (taking abs because 'e' is usually negative)
        delta_col = abs(int(deg_lon / a))
        delta_row = abs(int(deg_lat / e))
        
        # Bounding box in pixels
        y_min, y_max = center_row - delta_row, center_row + delta_row
        x_min, x_max = center_col - delta_col, center_col + delta_col
        
        # Bounds check
        if x_max < 0 or x_min >= meta["width"] or y_max < 0 or y_min >= meta["height"]:
            return f"Error: The requested area at ({latitude}, {longitude}) is outside the Hawaii database bounds."
            
        series = get_timeseries_for_region(db_path, start_date, end_date, y_min, y_max, x_min, x_max)
        
        if not series:
            return f"No {variable} data found for the range {start_date} to {end_date} in this region."
            
        # Format a summary
        months = sorted(series.keys())
        values = [series[m] for m in months]
        avg_val = sum(values) / len(values)
        max_val, min_val = max(values), min(values)
        
        summary = f"Summary for {variable} near ({latitude}, {longitude}) from {start_date} to {end_date} ({radius_km}km radius):\n"
        summary += f"- Average: {avg_val:.2f} {unit}\n"
        summary += f"- Maximum: {max_val:.2f} {unit} ({months[values.index(max_val)]})\n"
        summary += f"- Minimum: {min_val:.2f} {unit} ({months[values.index(min_val)]})\n"
        summary += f"- Data Points: {len(series)} months"
        
        # If the series is short, list it. Otherwise, mention it can be plotted.
        if len(series) <= 12:
            summary += "\n\nMonthly Breakdown:\n"
            for m in months:
                summary += f"  {m}: {series[m]:.2f} {unit}\n"
        else:
            summary += "\n\n(Note: Detailed monthly data is available for all 168 months if needed.)"
                
        return summary
            
    except Exception as err:
        return f"Error in regional query: {str(err)}"

@tool
def query_rainfall_extremes(latitude: float, longitude: float, start_date: str = "1990-01-01", end_date: str = "2023-12-31", percentile: float = 99.0) -> str:
    """
    Calculates rainfall extremes (e.g., 'top 1%' or 99th percentile) for a specific coordinate.
    Analyzes daily intensity to find the threshold for heavy rainfall events.
    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        start_date: Start date for analysis (YYYY-MM-DD). Default is 1990-01-01.
        end_date: End date for analysis (YYYY-MM-DD). Default is 2023-12-31.
        percentile: Percentile to calculate (e.g., 99.0 for 'top 1%').
    """
    from database.tiledb_access import get_timeseries_for_region, get_metadata
    
    # 1. Try local daily array first (Optimized storage)
    daily_db_path = os.path.join(PROJECT_ROOT, "database", "daily_rainfall_optimized")
    if os.path.exists(daily_db_path):
        try:
            meta = get_metadata(daily_db_path)
            a, b, c, d, e, f = meta["transform"]
            col = int((longitude - c) / a)
            row = int((latitude - f) / e)
            
            # Use get_timeseries_for_region for a 1x1 pixel (single point)
            series = get_timeseries_for_region(daily_db_path, start_date, end_date, row, row, col, col)
            if series:
                values = [v for v in series.values() if v >= 0]
                if values:
                    thresh = np.percentile(values, percentile)
                    return f"The {percentile}th percentile ('top 1%') daily rainfall threshold at ({latitude}, {longitude}) from {start_date} to {end_date} is {thresh:.2f} mm/day. This represents the intensity of the heaviest rainfall events."
        except Exception as err:
            print(f"Local daily query failed, falling back to API: {err}")
            
    # 2. Fallback to HCDP API for real-time daily calculation
    token = os.getenv("HCDP_API_TOKEN")
    if not token:
        return "Error: No HCDP_API_TOKEN found for remote extremes query."
        
    url = "https://api.hcdp.ikewai.org/raster/timeseries"
    params = {
        'location': 'hawaii',
        'start': start_date,
        'end': end_date,
        'lat': latitude,
        'lng': longitude,
        'datatype': 'rainfall',
        'extent': 'statewide',
        'production': 'new',
        'period': 'day'
    }
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            values = [v for v in data.values() if v is not None and v >= 0]
            if values:
                thresh = np.percentile(values, percentile)
                return f"The {percentile}th percentile ('top 1%') daily rainfall threshold at ({latitude}, {longitude}) from {start_date} to {end_date} is {thresh:.2f} mm/day. (Calculated dynamically via HCDP API)."
        return f"Error fetching daily data from API (Status: {resp.status_code})."
    except Exception as e:
        return f"Exception during API query: {str(e)}"

@tool
def generate_climatogram(latitude: float, longitude: float, start_year: int = None, end_year: int = None, units: str = 'metric', session_id: str = "default") -> str:
    """
    Generates an interactive Climatogram (combined temperature and rainfall seasonal chart) for a location.
    Use this when the user asks for a 'climate chart', 'climatogram', or 'typical seasonal weather'.
    Args:
        latitude, longitude: Coordinates (use geocode_placename first if given a name).
        start_year, end_year: Years to average over (e.g. 2010 to 2020). If omitted, defaults to the last 10 years of data.
        units: 'metric' (default: Celsius/mm) or 'imperial' (Fahrenheit/inches).
        session_id: Unique session ID for unique filenames.
    """
    if create_climatogram_file is None:
        return "Error: Graph generator utility not found."
    
    try:
        from database.tiledb_access import get_metadata, get_timeseries_for_region
        import numpy as np
        from collections import defaultdict
        
        # 1. Determine Date Range (Default to last 10 years)
        temp_db_path = os.path.join(PROJECT_ROOT, "database", "temperature_array")
        if not os.path.exists(temp_db_path):
            return f"Error: Temperature database not found at {temp_db_path}"
            
        meta = get_metadata(temp_db_path)
        available_months = sorted(meta["time_mapping"].keys())
        latest_year = int(available_months[-1].split("-")[0])
        
        if end_year is None:
            end_year = latest_year
        if start_year is None:
            start_year = end_year - 9 # Last 10 years

        start_date = f"{start_year}-01"
        end_date = f"{end_year}-12"

        # 2. Setup Pixel Bounds (5km radius as requested)
        a, b, c, d, e, f = meta["transform"]
        radius_km = 5.0
        deg_lat = radius_km / 111.0
        deg_lon = radius_km / 104.0
        
        center_col = int((longitude - c) / a)
        center_row = int((latitude - f) / e)
        delta_col = abs(int(deg_lon / a))
        delta_row = abs(int(deg_lat / e))
        
        y_min, y_max = center_row - delta_row, center_row + delta_row
        x_min, x_max = center_col - delta_col, center_col + delta_col

        # 3. Query Data
        rain_db_path = os.path.join(PROJECT_ROOT, "database", "rainfall_array")
        
        temp_series = get_timeseries_for_region(temp_db_path, start_date, end_date, y_min, y_max, x_min, x_max)
        rain_series = get_timeseries_for_region(rain_db_path, start_date, end_date, y_min, y_max, x_min, x_max)

        if not temp_series or not rain_series:
            return f"Error: Could not retrieve enough data for a chart at ({latitude}, {longitude}) for the range {start_year}-{end_year}."

        # 4. Aggregate by Month
        monthly_temp = defaultdict(list)
        monthly_rain = defaultdict(list)

        for date_str, val in temp_series.items():
            month_idx = int(date_str.split("-")[1])
            monthly_temp[month_idx].append(val)
        
        for date_str, val in rain_series.items():
            month_idx = int(date_str.split("-")[1])
            monthly_rain[month_idx].append(val)

        # Calculate Means
        months_label = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        final_temp = [np.mean(monthly_temp[i]) if i in monthly_temp else np.nan for i in range(1, 13)]
        final_rain = [np.mean(monthly_rain[i]) if i in monthly_rain else np.nan for i in range(1, 13)]

        # 5. Handle Unit Conversion
        temp_unit = "°C"
        rain_unit = "mm"
        if units.lower() == 'imperial':
            final_temp = [(t * 9/5) + 32 for t in final_temp]
            final_rain = [r / 25.4 for r in final_rain]
            temp_unit = "°F"
            rain_unit = "inches"

        # 6. Generate Plot
        df_plot = pd.DataFrame({
            'Month': months_label,
            'Temp_C': final_temp,
            'Rainfall_mm': final_rain
        })

        clean_sid = "".join(x for x in str(session_id) if x.isalnum())
        output_file = f"climatogram_{clean_sid}.html" if clean_sid else "climatogram.html"
        output_path = os.path.join(OUTPUTS_DIR, output_file)

        chart_title = f"Climate Climatogram ({start_year}-{end_year}) - Units: {units.capitalize()}"
        abs_path = create_climatogram_file(df_plot, output_path=output_path, title=chart_title, auto_open=False)

        return f"Interactive climatogram created successfully: {abs_path}"

    except Exception as e:
        return f"Error generating climatogram: {str(e)}"

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
8. For specific historical climate queries (temperature, rainfall, or SPI):
   - Use 'query_historical_timeseries' for multi-month or multi-year ranges.
   - Use 'query_historical_climate_data' for a single specific month.
   - Use 'generate_climatogram' when the user asks for a chart, graph, or seasonal typical weather breakdown.
9. SPI stands for Standardized Precipitation Index. It is used to represent drought (negative values) or wet conditions (positive values).
10. If statewide is False, radius_km must be at least 1.0 (default 5.0).
11. When a user asks for a map and mentions 'stations', 'markers', 'sites', or 'sensors', you MUST set add_stations=True in the generate_gridded_map tool.
12. For 'generate_climatogram', always ask for a location first if not provided. Metric units are the default.
13. RAINFALL EXTREMES (Top 1%):
    - If a user asks for 'top 1%' or 'rainfall extremes', they are referring to the 99th percentile (R99P) of DAILY rainfall intensity.
    - DO NOT use SPI (Standardized Precipitation Index) as a proxy for 'top 1%' unless specifically asked for anomalies. SPI > 2.0 means 'extremely wet month', not necessarily the heaviest daily events.
    - For specific locations, use 'query_rainfall_extremes'.
    - For maps, use 'generate_gridded_map' with data_type='daily_rainfall'.
"""

def normalize_content(content):
    """
    Normalizes message content to a string.
    Newer Gemini models (via LangChain) can return content as a list of dictionaries.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and 'text' in part:
                text_parts.append(part['text'])
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts)
    return str(content)


def initialize_agent():
    global llm_with_tools
    if llm_with_tools is not None:
        return
        
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[!] ERROR: GOOGLE_API_KEY not found.")
        return

    # Initialize Gemini 3 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=api_key,
        temperature=0
    )

    # Bind tools to the LLM
    tools = [geocode_placename, find_nearby_stations, map_nearby_stations, generate_gridded_map, query_historical_climate_data, query_historical_timeseries, generate_climatogram, query_rainfall_extremes]
    llm_with_tools = llm.bind_tools(tools)
    print("[*] Agent initialized with tools.")

def chat_with_agent(user_input: str, messages: list, session_id: str = "default"):
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
                    "query_historical_climate_data": query_historical_climate_data,
                    "query_historical_timeseries": query_historical_timeseries,
                    "generate_climatogram": generate_climatogram,
                    "query_rainfall_extremes": query_rainfall_extremes
                }

                selected_tool = tool_map[tool_call["name"]]
                
                # Execute tool
                print(f"[*] Calling tool: {tool_call['name']}({tool_call['args']})")
                
                # Pass session_id to the tool if it supports it
                args = tool_call['args']
                if tool_call['name'] in ["generate_gridded_map", "map_nearby_stations", "generate_climatogram"]:
                    args['session_id'] = session_id
                
                tool_output = selected_tool.invoke(args)
                
                # If tool created a map, extract its path for the UI
                output_str = str(tool_output)
                if "successfully:" in output_str.lower():
                    # Robust cross-platform extraction: find the path after "successfully:"
                    try:
                        marker = "successfully:"
                        start_idx = output_str.lower().find(marker) + len(marker)
                        potential_path = output_str[start_idx:].strip()
                        if os.path.exists(potential_path):
                            new_map_path = os.path.abspath(potential_path)
                    except Exception:
                        pass
                
                # Fallback for old/legacy hardcoded names if they still exist
                if not new_map_path:
                    if "html" in output_str.lower() and os.path.exists("gridded_map.html"):
                        new_map_path = os.path.abspath("gridded_map.html")
                    elif "html" in output_str.lower() and os.path.exists("station_map.html"):
                        new_map_path = os.path.abspath("station_map.html")

                # Add tool result to history
                messages.append(ToolMessage(content=output_str, tool_call_id=tool_call["id"]))
            
            # Get next response from LLM (to handle tool results or multi-step tasks)
            response = llm_with_tools.invoke(messages)
            messages.append(response)
            
        return normalize_content(response.content), messages, new_map_path
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
                        "query_historical_climate_data": query_historical_climate_data,
                        "query_historical_timeseries": query_historical_timeseries,
                        "generate_climatogram": generate_climatogram
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
