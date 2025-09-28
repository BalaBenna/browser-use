import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle
from browser_use.tools.service import Tools
from custom_tools import CUSTOM_TOOLS
from agent_session import SESSION_MANAGER
import uuid
import logging
from contextlib import asynccontextmanager

# ---
# 1. Load environment variables from .env file
# ---
load_dotenv()

# ---
# 2. Check for the Google API key
# ---
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")

# ---
# Configure logging
# ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_agent_query(query: str, session_id: str, websocket: Optional[WebSocket] = None) -> str:
    """Runs the agent with a given query and session ID."""
    # Get the session for this request
    session = SESSION_MANAGER.get_session(session_id)

    async def step_callback(agent_state, agent_output, step_index):
        if websocket:
            step_info = {
                "step": step_index,
                "thinking": agent_output.current_state.thinking,
                "next_goal": agent_output.current_state.next_goal,
                "action": [action.model_dump_json() for action in agent_output.action]
            }
            print(f"Sending step info: {step_info}")  # Debug log
            await websocket.send_json(step_info)
        else:
            print("WebSocket is not available in step_callback")  # Debug log

    # Create an Agent with the user query as the task
    agent = Agent(
        task=query,
        llm=ChatGoogle(model='gemini-flash-latest'),
        headless=False,  # Run the browser in headless mode
        tools=Tools(),  # Create a Tools object
        # Pass the session to the agent's context
        tool_context={"session": session},
        register_new_step_callback=step_callback,
    )
    # Add custom tools to the agent
    for tool in CUSTOM_TOOLS:
        agent.tools.registry.action("Custom tool")(tool["function"])
    # Run asynchronously and get the result
    result = await agent.run()

    # Extract the final, human-readable response
    if result and result.history:
        # Find the result from the 'done' action, which is usually the last one
        for history_item in reversed(result.history):
            for action_result in history_item.result:
                if action_result.is_done:
                    return action_result.extracted_content or "No content extracted."

    # Fallback to the string representation if no 'done' action is found
    if hasattr(result, '__str__'):
        return str(result)
    return repr(result)

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

            # This is a simplified approach. For production, you'd run the agent
            # in a separate thread or process to avoid blocking.
            # For this example, we'll run it directly but use the callback to send updates.
            
            # We are not awaiting the result here, as the updates are sent via callback
            # The final result will be sent as the last message.
            final_result = await run_agent_query(query, session_id, websocket)
            
            await websocket.send_json({"final_result": final_result, "session_id": session_id})

    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
    finally:
        await websocket.close()

@app.get("/", response_class=HTMLResponse)
async def chat_page():
    return """
    <html>
    <head>
        <title>QI Chat Interface</title>
        <style>
            body { font-family: Arial; background: #181c20; color: #eee; }
            #chat { width: 500px; margin: 40px auto; background: #23272b; padding: 20px; border-radius: 8px; }
            #messages { height: 300px; overflow-y: auto; border: 1px solid #333; padding: 10px; margin-bottom: 10px; background: #1a1d21; }
            .user { color: #7ecfff; }
            .qi { color: #baff7e; }
            .step { color: #f0ad4e; border-left: 2px solid #f0ad4e; padding-left: 10px; margin-left: 5px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div id="chat">
            <h2>QI Chat</h2>
            <div id="messages"></div>
            <form id="chat-form">
                <input id="user-input" type="text" style="width: 80%;" autocomplete="off" placeholder="Type your query..." />
                <button type="submit">Send</button>
            </form>
        </div>
        <script>
            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const messages = document.getElementById('messages');
            
            const ws = new WebSocket(`ws://${location.hostname}:8001/ws`);
            let sessionId = null;

            ws.onopen = (event) => {
                console.log("WebSocket connection established.");
            };

            ws.onmessage = (event) => {
                console.log("Received message from server:", event.data);
                const data = JSON.parse(event.data);

                if (data.step) {
                    let actionDetails = '';
                    try {
                        const actions = data.action.map(a => JSON.parse(a));
                        actionDetails = actions.map(a => {
                            const actionName = Object.keys(a)[0];
                            const params = a[actionName];
                            let paramString = '';
                            if (typeof params === 'object' && params !== null) {
                                paramString = Object.entries(params)
                                    .map(([key, value]) => `<li>${key}: ${JSON.stringify(value)}</li>`)
                                    .join('');
                            } else {
                                paramString = `<li>${JSON.stringify(params)}</li>`;
                            }
                            return `<li><b>Action:</b> ${actionName}<ul>${paramString}</ul></li>`;
                        }).join('');
                    } catch (e) {
                        console.error("Error parsing action details:", e);
                        actionDetails = '<li>Could not parse action details.</li>';
                    }

                    messages.innerHTML += `<div class='step'>` +
                        `<b>Step ${data.step}</b><br/>` +
                        `<em>Thinking:</em> ${data.thinking}<br/>` +
                        `<em>Next Goal:</em> ${data.next_goal}<br/>` +
                        `<ul>${actionDetails}</ul>` +
                        `</div>`;
                } else if (data.final_result) {
                    messages.innerHTML += `<div class='qi'><b>QI:</b> ${data.final_result}</div>`;
                    sessionId = data.session_id;
                }
                messages.scrollTop = messages.scrollHeight;
            };

            ws.onerror = (error) => {
                console.error("WebSocket error:", error);
            };

            ws.onclose = (event) => {
                console.log("WebSocket connection closed:", event);
            };

            form.onsubmit = async (e) => {
                e.preventDefault();
                const msg = input.value.trim();
                if (!msg) return;
                messages.innerHTML += `<div class='user'><b>You:</b> ${msg}</div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;
                
                console.log("Sending message to server:", { message: msg, session_id: sessionId });
                ws.send(JSON.stringify({ message: msg, session_id: sessionId }));
            };
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat_api(req: ChatRequest):
    try:
        # Use the provided session_id or generate a new one
        session_id = req.session_id or str(uuid.uuid4())
        
        # Call your agent logic here, passing the session_id
        reply = await run_agent_query(req.message, session_id)
        
        return JSONResponse({"reply": reply, "session_id": session_id})
    except Exception as e:
        # ---
        # 5. Add error handling to catch and log crashes
        # ---
        print(f"ERROR: An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

if __name__ == "__main__":
    # It's important to run the app directly for the shutdown hook to work
    uvicorn.run(app, host="0.0.0.0", port=8001)
