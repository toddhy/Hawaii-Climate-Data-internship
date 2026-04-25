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
        C["<b>generate_climatogram</b>"]
        Q["<b>query_historical_climate_data</b>"]
        E["<b>query_rainfall_extremes</b>"]
    end

    subgraph "⚙️ Backend & Service Layer<br/>"
        Geo["<b>Nominatim Geocoder</b>"]
        Finder["<b>station_finder.py</b>"]
        Vis["<b>map_visualizer.py</b>"]
        Grapher["<b>graph_generator.py</b>"]
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
    Tools --> C
    Tools --> Q
    Tools --> E

    %% Flow: Tool -> Logic
    G --> Geo
    F --> Finder
    M --> Vis
    C --> Grapher
    Q --> TileAPI
    E --> TileAPI

    %% Flow: Logic -> Data
    Finder --> CSV
    Vis -- "<b>Aggregates</b>" --> TIFFs
    Vis -- "<b>Markers</b>" --> CSV
    Grapher -- "<b>Queries</b>" --> TileAPI
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

## Data Ingestion & Optimization Flows

The project utilizes two distinct workflows for data ingestion depending on the temporal resolution and storage requirements.

### 1. Standard Monthly Ingestion (Legacy)
Used for monthly variables (Rainfall, Temp, SPI). This flow focuses on optimizing existing large TIFF collections using lossless compression.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph LR
    Raw["<b>Raw HCDP TIFFs</b>"] --> Opt["<b>compress_tiffs.py</b>"]
    Opt -- "<b>LZW Compression</b>" --> TDB_New[("<b>Optimized TIFFs</b>")]
    TDB_New -- "<b>Ingestion</b>" --> Storage["<b>25 GB → 11 GB Total</b>"]
    Storage -- "<b>TileDB Slicing</b>" --> Agent["<b>AI Agent</b>"]

    classDef source  fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef process fill:#5B21B6,stroke:#2e1065,color:#ffffff,font-weight:bold
    classDef store   fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold
    classDef output  fill:#065F46,stroke:#022c22,color:#ffffff,font-weight:bold

    class Raw source
    class Opt process
    class TDB_New store
    class Storage,Agent output
```

### 2. High-Resolution Daily Ingestion (New)
Used for storm-level daily data. This flow bypasses intermediate disk storage entirely by streaming data from the API directly into a quantized 16-bit format.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph LR
    API["<b>HCDP API</b>"] -- "<b>HTTPS Stream</b>" --> Ingest["<b>ingest_daily_stream.py</b>"]
    Ingest -- "<b>Memory Preprocessing</b>" --> Quant["<b>Uint16 Quantization</b>"]
    Quant -- "<b>Atomic Write</b>" --> TDB[("<b>Daily TileDB Array</b>")]
    TDB -- "<b>Sub-second Query</b>" --> Agent["<b>AI Agent</b>"]

    classDef source  fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef process fill:#5B21B6,stroke:#2e1065,color:#ffffff,font-weight:bold
    classDef store   fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold
    classDef output  fill:#065F46,stroke:#022c22,color:#ffffff,font-weight:bold

    class API source
    class Ingest,Quant process
    class TDB store
    class Agent output
```

## Climatogram Generation Workflow

The following diagram illustrates the specialized process for generating high-fidelity dual-axis climatograms from the TileDB time-series data.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph LR
    UserRequest["👤 <b>User Prompt</b><br/>(e.g., 'Chart climate for Hilo')"] --> Agent["🤖 <b>AI Agent</b>"]
    Agent -- "<b>Invokes</b>" --> Tool["🛠️ <b>generate_climatogram</b>"]
    Tool -- "<b>Coordinates</b>" --> Gen["⚙️ <b>graph_generator.py</b>"]
    Gen -- "<b>Time-Series Query</b>" --> TDB["🗄️ <b>TileDB Access</b>"]
    
    TDB -- "<b>Rainfall Data</b>" --> Gen
    TDB -- "<b>Temperature Data</b>" --> Gen
    
    Gen -- "<b>Processes Plotly</b>" --> HTML["📂 <b>outputs/climate_chart.html</b>"]
    HTML -- "<b>Served via API</b>" --> UI["🖥️ <b>Web Dashboard</b>"]

    classDef proc fill:#1D4ED8,stroke:#1e3a5f,color:#ffffff,font-weight:bold
    classDef tool fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef data fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold
    
    class UserRequest,UI proc
    class Agent,Tool,Gen tool
    class TDB,HTML data
```

> [!TIP]
> **Data Density**: Unlike simple maps, the climatogram workflow retrieves and aggregates over **400 data points** per variable to provide a complete historical view of the location's climate trends.
