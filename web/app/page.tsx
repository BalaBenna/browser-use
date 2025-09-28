"use client";
import { useState, useRef, useEffect } from "react";
import styles from "./chat.module.css";

interface Message {
  sender: "user" | "qi" | "step";
  text?: string;
  step?: number;
  thinking?: string;
  next_goal?: string;
  action?: any[];
  id: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const savedMessages = localStorage.getItem("chatMessages");
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
    const savedSessionId = localStorage.getItem("sessionId");
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    if (sessionId) {
      localStorage.setItem("sessionId", sessionId);
    }
  }, [messages, sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const wsUrl = `ws://${location.hostname}:8001/ws`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("WebSocket connection established.");
    };

    ws.current.onmessage = (event) => {
      console.log("Received message from server:", event.data);
      const data = JSON.parse(event.data);

      if (data.step) {
        setMessages((msgs) => [...msgs, { sender: "step", ...data, id: Date.now().toString() }]);
      } else if (data.final_result) {
        setMessages((msgs) => [...msgs, { sender: "qi", text: data.final_result, id: Date.now().toString() }]);
        setSessionId(data.session_id);
        setLoading(false);
      }
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setMessages((msgs) => [...msgs, { sender: "qi", text: "Error: Could not connect to WebSocket.", id: Date.now().toString() }]);
      setLoading(false);
    };

    ws.current.onclose = (event) => {
      console.log("WebSocket connection closed:", event);
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;
    const userMsg = { sender: "user" as const, text: input, id: Date.now().toString() };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);

    console.log("Sending message to server:", { message: userMsg.text, session_id: sessionId });
    ws.current.send(JSON.stringify({ message: userMsg.text, session_id: sessionId }));
  }

  return (
    <main className={styles.container}>
      <header className={styles.header}>QI Chat</header>
      <div className={styles.messagesContainer}>
        {messages.map((msg) => (
          <div key={msg.id} className={`${styles.message} ${msg.sender === 'user' ? styles.userMessage : msg.sender === 'qi' ? styles.qiMessage : styles.stepMessage}`}>
            <div className={`${styles.avatar} ${msg.sender === 'user' ? styles.userAvatar : msg.sender === 'qi' ? styles.qiAvatar : styles.stepAvatar}`}>
              {msg.sender === 'user' ? 'U' : msg.sender === 'qi' ? 'QI' : 'S'}
            </div>
            {msg.sender === 'step' ? (
              <div>
                <b>Step {msg.step}</b>
                <p><em>Thinking:</em> {msg.thinking}</p>
                <p><em>Next Goal:</em> {msg.next_goal}</p>
                <ul>
                  {msg.action?.map((a, index) => {
                    const action = JSON.parse(a);
                    const actionName = Object.keys(action)[0];
                    const params = action[actionName];
                    return (
                      <li key={index}>
                        <b>Action:</b> {actionName}
                        <ul>
                          {Object.entries(params).map(([key, value]) => (
                            <li key={key}>{key}: {JSON.stringify(value)}</li>
                          ))}
                        </ul>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ) : (
              <p>{msg.text}</p>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className={styles.formContainer}>
        <form onSubmit={sendMessage} className={styles.form}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            className={styles.input}
            placeholder="Type your query..."
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading || !input.trim()} className={styles.button}>
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </main>
  );
}
