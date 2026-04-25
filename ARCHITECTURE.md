# System Architecture

The following diagram illustrates the interaction between the React frontend, FastAPI backend, LangChain AI agent, and the TileDB climate database.

```mermaid
%%{init: {'theme': 'neutral', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'trebuchet ms', 'primaryTextColor': '#111111', 'lineColor': '#444444', 'subgraphTitleSize': '22px'}}}%%
graph TD
    subgraph "🖥️ Frontend (React / Vite)<br/>"
        UI["<b>Chat Interface</b><br/>(App.tsx)"]
        Map["<b>Map Viewer</b><br/>(Iframe)"]
        Client["<b>API Client</b><br/>(api.ts)"]
    end
    subgraph "⚙️ Backend (FastAPI)<br/>"
        Srv["<b>Server</b><br/>(server.py)"]
    end
    subgraph "🤖 AI Agent (LangChain)<br/>"
        Agent["<b>LangChain Agent</b><br/>(langchain_agent.py)"]
        LLM["<b>Gemini 3.1 Flash</b>"]
    end
    subgraph "🔧 Tools & Utilities (HCDP API)<br/>"
        Finder["<b>Station Finder</b>"]
        Mapper["<b>Map Visualizer</b>"]
        Grapher["<b>Graph Generator</b>"]
    end
    subgraph "🗄️ Data Layer (TileDB)<br/>"
        TDB_Access["<b>TileDB Access</b><br/>(tiledb_access.py)"]
        Rainfall[("<b>Monthly Rainfall</b><br/>Array")]
        DailyRainfall[("<b>Daily Rainfall</b><br/>(Quantized)")]
        Temp[("<b>Temperature</b><br/>Arrays (Mean/Max/Min)")]
        SPI[("<b>SPI</b><br/>Array")]
    end
    UI --> Client
    Client -- "<b>POST /chat</b>" --> Srv
    Srv -- "<b>Invoke</b>" --> Agent
    Agent -- "<b>Prompts</b>" --> LLM
    Agent -- "<b>Calls</b>" --> Finder
    Agent -- "<b>Calls</b>" --> Mapper
    Agent -- "<b>Calls</b>" --> Grapher
    Finder -- "<b>Queries</b>" --> TDB_Access
    Mapper -- "<b>Queries</b>" --> TDB_Access
    Grapher -- "<b>Queries</b>" --> TDB_Access
    Agent -- "<b>Queries</b>" --> TDB_Access
    TDB_Access --> Rainfall
    TDB_Access --> DailyRainfall
    TDB_Access --> Temp
    TDB_Access --> SPI
    
    Mapper -- "<b>Generates</b>" --> OutDir["<b>outputs/</b>"]
    Grapher -- "<b>Generates</b>" --> OutDir
    OutDir --> MapHTML["<b>Map/Graph HTML</b>"]
    Srv -- "<b>Serves Static</b>" --> OutDir
    MapHTML --> Map

    %% Styles per layer — deeper fills, white text for strong contrast
    classDef frontend fill:#1D4ED8,stroke:#1e3a5f,color:#ffffff,font-weight:bold
    classDef backend  fill:#065F46,stroke:#022c22,color:#ffffff,font-weight:bold
    classDef agent    fill:#5B21B6,stroke:#2e1065,color:#ffffff,font-weight:bold
    classDef tools    fill:#B45309,stroke:#7c3700,color:#ffffff,font-weight:bold
    classDef data     fill:#334155,stroke:#0f172a,color:#ffffff,font-weight:bold

    class UI,Map,Client frontend
    class Srv,DB_Sess,Cleanup backend
    class Agent,LLM agent
    class Finder,Mapper,Grapher tools
    class TDB_Access,Rainfall,DailyRainfall,Temp,SPI,OutDir,MapHTML data
```

## Component Breakdown

1.  **React Frontend**: Provides a premium chat interface where users can ask natural language questions. It displays the assistant's text responses and renders generated interactive maps in an iframe.
2.  **FastAPI Backend**: Acts as the bridge between the frontend and the AI. It manages conversation sessions, serves generated HTML from a dedicated `outputs/` directory, and orchestrates an automated **Cleanup Manager** to prune stale files.
3.  **LangChain Agent**: The "brain" of the application. It uses Gemini 3.1 Flash to understand intent and decides which local tools to call (geocoding, data querying, mapping, or climatogram generation).
4.  **HCDP API Tools**: Specialized Python scripts for coordinate resolution, spatial searches, precision climate data querying, and visual generation (Leaflet/Folium maps and Plotly climatograms).
5.  **TileDB Data Layer**: A high-performance spatial database storing over 30 years of climate data. It includes:
    - **Monthly Variables**: Rainfall, Temperature (Mean/Min/Max), and SPI.
    - **Daily Variables**: High-resolution rainfall (1990–Present) optimized with **16-bit Integer Quantization**.
    - **Efficiency**: Total footprint reduced from ~450GB (raw TIFF) to **~36GB** (TileDB) using Zstd compression and unit-scaling.
6.  **Daily Data Optimization**: To handle the massive volume of daily data (3.5 million pixels per day), rainfall is stored as `uint16` (millimeters * 10). This "No-Disk" ingestion approach bypasses standard TIFF storage by streaming data directly from the HCDP API into memory-resident TileDB buffers.
