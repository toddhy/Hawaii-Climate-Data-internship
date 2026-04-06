import os
import sys

# Add paths
PROJECT_ROOT = r"c:\SCIPE\HCDP-data-for-AI"
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "gemini_chat"))

from gemini_chat.langchain_agent import query_historical_climate_data, generate_gridded_map

def test_spi_tools():
    print("--- Testing SPI Query Tool ---")
    # Honolulu coordinates: 21.3069, -157.8583
    query_result = query_historical_climate_data.invoke({
        "latitude": 21.3069, 
        "longitude": -157.8583, 
        "month": "2024-01", 
        "variable": "spi"
    })
    print(f"Query Result: {query_result}")

    print("\n--- Testing SPI Mapping Tool (Statewide) ---")
    map_result = generate_gridded_map.invoke({
        "data_type": "spi",
        "statewide": True,
        "start_date": "2024-01",
        "end_date": "2024-01"
    })
    print(f"Map Result: {map_result}")

if __name__ == "__main__":
    test_spi_tools()
