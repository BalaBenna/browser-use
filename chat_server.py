import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from master_agent import MasterAgent
from super_intelligent_agent import SuperIntelligentAgent
from agent_session import SESSION_MANAGER
import uuid
import logging
from contextlib import asynccontextmanager
import sys
import asyncio

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
# Configure safe logging
# ---
from error_handler import setup_global_logging, SafeLogger

# Setup global logging configuration
setup_global_logging()

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
)

# Use safe logger
logger = SafeLogger(__name__)

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
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket connection: {e}")
        return
    
    master_agent = None
    connection_active = True
    
    try:
        while connection_active:
            try:
                # Set a timeout for receiving messages
                data = await asyncio.wait_for(websocket.receive_json(), timeout=300)  # 5 minute timeout
                query = data.get("message")
                session_id = data.get("session_id") or str(uuid.uuid4())

                if not query:
                    logger.warning("Received empty query, skipping")
                    continue

                logger.info(f"Processing query: {query[:100]}...")
                
                # Use the Master Agent for direct task execution
                master_agent = MasterAgent(task=query, websocket=websocket)
                
                try:
                    final_result = await asyncio.wait_for(master_agent.run(), timeout=180)  # 3 minute timeout
                    
                    if connection_active:
                        # Send the result directly
                        await websocket.send_json({
                            "type": "final_result", 
                            "final_result": final_result,
                            "session_id": session_id
                        })
                        
                except asyncio.TimeoutError:
                    logger.error("Task execution timed out")
                    if connection_active:
                        try:
                            await websocket.send_json({
                                "type": "error", 
                                "error": "Task timed out after 3 minutes. Please try a simpler request."
                            })
                        except Exception as send_error:
                            logger.error(f"Failed to send timeout error: {send_error}")
                except Exception as task_error:
                    logger.error(f"Task execution error: {task_error}")
                    if connection_active:
                        try:
                            await websocket.send_json({
                                "type": "error", 
                                "error": f"Task failed: {str(task_error)[:200]}..."
                            })
                        except Exception as send_error:
                            logger.error(f"Failed to send task error: {send_error}")
                
            except asyncio.TimeoutError:
                # Connection timeout - close gracefully
                connection_active = False
                logger.info("WebSocket connection timed out")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                if connection_active:
                    try:
                        await websocket.send_json({
                            "type": "error", 
                            "error": f"Connection error: {str(e)[:200]}..."
                        })
                    except Exception as send_error:
                        logger.error(f"Failed to send connection error: {send_error}")
                        connection_active = False
                        break

    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        connection_active = False
    finally:
        logger.info("WebSocket connection cleanup started")
        # Clean up resources
        if 'super_agent' in locals():
            try:
                # Super-intelligent agent handles its own cleanup
                pass
            except Exception as e:
                logger.warning(f"Error cleaning up super agent: {e}")
        
        if connection_active:
            try:
                await websocket.close()
                logger.info("WebSocket connection closed gracefully")
            except Exception as e:
                logger.info(f"WebSocket close error: {e}")


@app.get("/", response_class=HTMLResponse)
async def chat_page():
    return FileResponse("web/index.html")

@app.post("/api/agent/start")
async def start_agent(request: ChatRequest):
    """Start a new agent task"""
    try:
        super_agent = SuperIntelligentAgent(task=request.message)
        result = await super_agent.process_task()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/api/agent/resume")
async def resume_agent(request: dict):
    """Resume agent task with user input"""
    try:
        task_id = request.get("task_id")
        slot_id = request.get("slot_id")
        value = request.get("value")
        
        if not all([task_id, slot_id, value]):
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required fields: task_id, slot_id, value"}
            )
        
        # In a real implementation, you'd load the agent from storage
        # For now, we'll create a new one (this should be improved with proper state management)
        super_agent = SuperIntelligentAgent(task="Resume task")
        result = await super_agent.resume_task(slot_id, value)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error resuming agent: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

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
    uvicorn.run(app, host="0.0.0.0", port=3005)
