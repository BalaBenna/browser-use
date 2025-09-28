import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from master_agent import MasterAgent
from agent_session import SESSION_MANAGER
import uuid
import logging
from contextlib import asynccontextmanager
import sys

# ---
# 1. Load environment variables from .env file
# ---
from dotenv import load_dotenv
load_dotenv()

# ---
# 2. Check for the Google API key
# ---
import os
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")

# ---
# Configure logging for UTF-8
# ---
# Remove any existing handlers to prevent duplicate logs
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Configure the root logger to handle UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    # This is the key to fixing the encoding errors on Windows
    encoding='utf-8',
    errors='replace'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic here
    yield
    # Shutdown logic here
    pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("message")
            session_id = data.get("session_id") or str(uuid.uuid4())

            if not query:
                continue

            # Use the MasterAgent to handle the query
            master_agent = MasterAgent(task=query, websocket=websocket)
            final_result = await master_agent.run()
            
            await websocket.send_json({"type": "final_result", "final_result": final_result, "session_id": session_id})

    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        try:
            await websocket.close()
        except RuntimeError as e:
            # This can happen if the connection is already closed, which is fine.
            logger.info(f"WebSocket already closed: {e}")


@app.get("/", response_class=HTMLResponse)
async def chat_page():
    return FileResponse("web/index.html")

@app.post("/chat")
async def chat_api(req: ChatRequest):
    try:
        # This endpoint is no longer used by the web interface,
        # but we'll keep it for other potential clients.
        session_id = req.session_id or str(uuid.uuid4())
        master_agent = MasterAgent(task=req.message, websocket=None)
        reply = await master_agent.run()
        
        return JSONResponse({"reply": reply, "session_id": session_id})
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
