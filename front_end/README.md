# HCDP Agent - React Frontend

This directory contains the custom React + TypeScript frontend built to interface with the LangChain AI agent (`gemini_chat/langchain_agent.py`). It provides a sleek, modern UI for chatting with the agent and dynamically visualizing weather maps of Hawaii.

## Requirements

Before you begin, ensure you have:
1. **Node.js** and **npm** installed on your system.
2. The project's root Python virtual environment (`.venv`) fully set up.
3. Your `GOOGLE_API_KEY` defined in the root `.env` file for the LangChain agent.

## Getting Started

To fully interact with the agent through the UI, you need to run both the FastAPI backend and the Vite frontend simultaneously. 

### 1. Start the Backend Server
The backend is a FastAPI wrapper that hosts the AI agent and serves the mapped HTML files to the browser.

Open a terminal in the **root directory** (`c:\SCIPE\HCDP-data-for-AI`) and run:
```powershell
.\.venv\Scripts\python.exe -m uvicorn gemini_chat.server:app --port 8000
```
*(Leave this terminal running in the background).*

### 2. Start the Frontend Server
The frontend is built with React and Vite. It communicates with the backend on port 8000.

Open a **new terminal** in this directory (`c:\SCIPE\HCDP-data-for-AI\front_end`) and run:
```powershell
npm install   # If you haven't installed dependencies yet
npm run dev
```
*(Leave this terminal running in the background).*

### 3. Open the UI
Open your browser and navigate to the address provided by Vite (usually `http://localhost:5173/`).

## How to use the App

- **Chat Interface (Left Panel)**: Type queries such as *"Map rainfall near Honolulu"* or *"Create a gridded temperature map for Maui"*. The agent's strict behaviors are configured in `DEFAULT_SYSTEM_PROMPT` inside `gemini_chat/langchain_agent.py`.
- **Map View (Right Panel)**: Whenever the agent calls a tool that generates a map (e.g., `generate_gridded_map`), the server instantly outputs the map HTML and the right panel dynamically refreshes to display it.

## Customizing the Agent
To give the agent new rules, constraints, or to change its identity, modify the `DEFAULT_SYSTEM_PROMPT` inside `c:\SCIPE\HCDP-data-for-AI\gemini_chat\langchain_agent.py`. Any changes require you to **restart the backend server** to take effect.
