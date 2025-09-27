import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from browser_use import Agent, ChatGoogle

def run_agent_query(query: str) -> str:
    # Create an Agent with the user query as the task
    agent = Agent(
        task=query,
        llm=ChatGoogle(model='gemini-flash-latest'),
    )
    # Run synchronously and get the result
    result = agent.run_sync()
    # Try to extract a user-friendly response
    if hasattr(result, '__str__'):
        return str(result)
    return repr(result)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

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
            form.onsubmit = async (e) => {
                e.preventDefault();
                const msg = input.value.trim();
                if (!msg) return;
                messages.innerHTML += `<div class='user'><b>You:</b> ${msg}</div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg })
                });
                const data = await resp.json();
                messages.innerHTML += `<div class='qi'><b>QI:</b> ${data.reply}</div>`;
                messages.scrollTop = messages.scrollHeight;
            };
        </script>
    </body>
    </html>
    """

@app.post("/chat")
async def chat_api(req: ChatRequest):
    # Call your agent logic here
    reply = await asyncio.to_thread(run_agent_query, req.message)
    return JSONResponse({"reply": reply})

if __name__ == "__main__":
    uvicorn.run("chat_server:app", host="0.0.0.0", port=8000, reload=True)
