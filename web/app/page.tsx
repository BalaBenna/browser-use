"use client";
import { useState, useRef, useEffect } from "react";
import styles from "./chat.module.css";

interface Message {
  sender: "user" | "qi";
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null); // Add session state
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { sender: "user" as const, text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text, session_id: sessionId }), // Send session ID
      });
      const data = await resp.json();
      setMessages((msgs) => [...msgs, { sender: "qi", text: data.reply }]);
      if (data.session_id) {
        setSessionId(data.session_id); // Store new session ID
      }
    } catch (err) {
      setMessages((msgs) => [...msgs, { sender: "qi", text: "Error: Could not reach backend." }]);
    }
    setLoading(false);
  }

  return (
    <main className={styles.container}>
      <header className={styles.header}>QI Chat</header>
      <div className={styles.messagesContainer}>
        {messages.map((msg, i) => (
          <div key={i} className={`${styles.message} ${msg.sender === 'user' ? styles.userMessage : styles.qiMessage}`}>
            <div className={`${styles.avatar} ${msg.sender === 'user' ? styles.userAvatar : styles.qiAvatar}`}>
              {msg.sender === 'user' ? 'U' : 'QI'}
            </div>
            <p>{msg.text}</p>
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
