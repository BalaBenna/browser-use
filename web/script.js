document.addEventListener("DOMContentLoaded", () => {
    const messages = document.getElementById("messages");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    const ws = new WebSocket(`ws://${location.hostname}:8001/ws`);
    let sessionId = null;

    ws.onopen = () => {
        console.log("WebSocket connection established.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "agent_message") {
            displayMessage(data.agent, data.message);
        } else if (data.type === "final_result") {
            displayMessage("Master Agent", `Final Report: ${data.final_result}`);
        }
        
        if (data.session_id) {
            sessionId = data.session_id;
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket connection closed.");
    };

    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = userInput.value.trim();
        if (message) {
            displayMessage("You", message);
            ws.send(JSON.stringify({ message: message, session_id: sessionId }));
            userInput.value = "";
        }
    }

    function displayMessage(sender, content) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", sender === "You" ? "user-message" : "agent-message");

        const senderElement = document.createElement("div");
        senderElement.classList.add("message-sender");
        senderElement.textContent = sender;

        const contentElement = document.createElement("div");
        contentElement.classList.add("message-content");
        // Use innerHTML to render formatted text from the agent.
        contentElement.innerHTML = content.replace(/\n/g, '<br>');

        messageElement.appendChild(senderElement);
        messageElement.appendChild(contentElement);

        messages.appendChild(messageElement);
        messages.scrollTop = messages.scrollHeight;
    }
});
