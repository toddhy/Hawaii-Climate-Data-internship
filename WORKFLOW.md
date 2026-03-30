# HCDP Project Workflow Visualization

This document visualizes the architecture and operational flow of the Hawaii Climate Data Portal (HCDP) AI Assistant.

## System Architecture

The following diagram illustrates how the Gemini-powered agent interacts with the HCDP API, the high-performance TileDB database, and local raster data to serve user requests.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph TD
    %% Entities
    User(["👤 <b>User</b>"])

    subgraph "🤖 AI Orchestration (LangChain)<br/>"
        Agent["<b>Gemini 2.0 Flash</b><br/>Agent"]
        Tools{"<b>LangChain</b><br/>Tool Layer"}
    end

    subgraph "🔧 Functional Tools (Python Scripts)<br/>"
        G["<b>geocode_placename</b>"]
        F["<b>find_nearby_stations</b>"]
        M["<b>generate_gridded_map</b>"]
        Q["<b>query_historical_climate_data</b>"]
    end

    subgraph "⚙️ Backend & Service Layer<br/>"
        Geo["<b>Nominatim Geocoder</b>"]
        Finder["<b>station_finder.py</b>"]
        Vis["<b>map_visualizer.py</b>"]
        TileAPI["<b>tiledb_access.py</b>"]
    end

    subgraph "🗄️ Data Storage<br/>"
        CSV["<b>Station CSV/Metadata</b>"]
        TIFFs[("<b>Local TIFF Rasters</b>")]
        TDB[("<b>TileDB Arrays</b><br/>Rainfall/Temp/SPI")]
    end

    %% Flow: Input
    User -- "<b>Natural Language Request</b>" --> Agent
    Agent -- "<b>Chains Tool Calls</b>" --> Tools

    %% Flow: Tools
    Tools --> G
    Tools --> F
    Tools --> M
    Tools --> Q

    %% Flow: Tool -> Logic
    G --> Geo
    F --> Finder
    M --> Vis
    Q --> TileAPI

    %% Flow: Logic -> Data
    Finder --> CSV
    Vis -- "<b>Aggregates</b>" --> TIFFs
    Vis -- "<b>Markers</b>" --> CSV
    TileAPI -- "<b>Slices/Queries</b>" --> TDB

    %% Flow: Output
    Vis -- "<b>Folium Render</b>" --> HTML["<b>interactive_map.html</b>"]
    TileAPI -- "<b>Data Values</b>" --> Q

    HTML -- "<b>Display</b>" --> User
    Q --> Agent
    Agent -- "<b>Text Explanation</b>" --> User

    %% Styles — deep fills, white text, bold
    classDef user        fill:#1e293b,stroke:#0f172a,color:#ffffff,font-weight:bold
    classDef orchestrate fill:#5B21B6,stroke:#2e1065,color:#ffffff,font-weight:bold
    classDef tools       fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef apis        fill:#065F46,stroke:#022c22,color:#ffffff,font-weight:bold
    classDef data        fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold
    classDef output      fill:#1D4ED8,stroke:#1e3a5f,color:#ffffff,font-weight:bold

    class User user
    class Agent,Tools orchestrate
    class G,F,M,Q tools
    class Geo,Finder,Vis,TileAPI apis
    class CSV,TIFFs,TDB data
    class HTML output
```

## Data Ingestion & Optimization Flow

The project also includes a specialized workflow for optimizing storage efficiency by converting raw TIFFs into compressed TileDB arrays.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph LR
    Raw["<b>Raw HCDP TIFFs</b>"] --> Opt["<b>optimize_storage.py</b>"]
    Opt -- "<b>Re-ingestion</b>" --> TDB_New[("<b>Optimized TileDB</b>")]
    TDB_New -- "<b>Zstd Compression</b>" --> Storage["<b>25 GB → Reduced Size</b>"]
    TDB_New -- "<b>Optimized Dimensions</b>" --> Agent["<b>LangChain Agent</b>"]

    classDef source  fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef process fill:#5B21B6,stroke:#2e1065,color:#ffffff,font-weight:bold
    classDef store   fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold
    classDef output  fill:#065F46,stroke:#022c22,color:#ffffff,font-weight:bold

    class Raw source
    class Opt process
    class TDB_New store
    class Storage,Agent output
```

> [!TIP]
> **TileDB Efficiency**: The TileDB arrays allow the agent to query a single "pixel" across 30+ years of data without loading entire TIFF files into memory, enabling near-instant response times for historical climate queries.
