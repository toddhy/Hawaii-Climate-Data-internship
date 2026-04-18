import os
import sys
import signal
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

# Add project root to path so we can import langchain_agent
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from gemini_chat.langchain_agent import chat_with_agent, initialize_agent, normalize_content
from gemini_chat.cleanup_manager import cleanup_outputs

app = FastAPI(title="HCDP Agent API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for dev)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static files (where Maps and Graphs are saved)
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")

# Request / Response Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatResponse(BaseModel):
    response: str
    map_url: Optional[str] = None
    messages: List[ChatMessage]

# In-memory store for conversational state across API calls
session_store = {}

@app.on_event("startup")
async def startup_event():
    # Warm up the agent (initialize model, geocoder, tools)
    initialize_agent()
    # Initial cleanup of old files on start
    cleanup_outputs(max_age_hours=24)
    print("[*] API Backend initialized.")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    print(f"[*] Incoming request for session: '{req.session_id}'")
    # Retrieve or create session history
    if req.session_id not in session_store:
        session_store[req.session_id] = []
        
    messages = session_store[req.session_id]
    
    # Run the agent
    reply, new_messages, generated_map = chat_with_agent(req.message, messages, req.session_id)
    
    # Schedule cleanup in the background after the response is sent
    background_tasks.add_task(cleanup_outputs, max_age_hours=24)
    
    # Update the internal session store reference
    session_store[req.session_id] = new_messages
    
    # Convert Langchain messages to simple dict for API response
    serializable_msgs = []
    for m in new_messages:
        role = "user" if m.__class__.__name__ == "HumanMessage" else "agent"
        # ToolMessages might also exist, but the main textual response is AIMessage
        if m.__class__.__name__ == "AIMessage":
            role = "agent"
        elif m.__class__.__name__ == "ToolMessage":
            role = "tool"
        
        # We'll mostly just pass the text back for display, though React side can filter
        serializable_msgs.append(ChatMessage(role=role, content=normalize_content(m.content)))
        
    # Return response payload
    map_url = None
    if generated_map:
        # We serve from /outputs/ which points to the outputs directory
        filename = os.path.basename(generated_map)
        map_url = f"/outputs/{filename}"
        
    return ChatResponse(
        response=reply,
        map_url=map_url,
        messages=serializable_msgs
    )
    
if __name__ == "__main__":
    import uvicorn

    # Use reload only in development. Set HCDP_ENV=production to disable.
    is_production = os.getenv("HCDP_ENV", "development").lower() == "production"
    use_reload = not is_production

    # Ensure Ctrl+C (SIGINT) and SIGTERM cause a clean exit
    def handle_shutdown(signum, frame):
        print("\n[*] Shutdown signal received. Stopping server...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    uvicorn.run("gemini_chat.server:app", host="0.0.0.0", port=8000, reload=use_reload)
