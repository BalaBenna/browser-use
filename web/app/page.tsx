"use client";
import { useState, useRef, useEffect } from "react";
import styles from "./chat.module.css";

interface Message {
  id: string;
  sender: "user" | "ai" | "system";
  text: string;
  timestamp: Date;
  type?: "text" | "thinking" | "action" | "result" | "delete";
  isTyping?: boolean;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: "ai",
      text: "👋 Hi! I'm your AI assistant. I can help you with tasks like booking flights, researching topics, writing content, and much more. What would you like me to help you with today?",
      timestamp: new Date(),
      type: "text"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentTask, setCurrentTask] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const ws = useRef<WebSocket | null>(null);
  const messageIdCounter = useRef<number>(1);

  // Generate unique ID for messages
  const generateUniqueId = () => {
    messageIdCounter.current += 1;
    return `msg-${Date.now()}-${messageIdCounter.current}`;
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      try {
        const wsUrl = `ws://${location.hostname}:8001/ws`;
        console.log("🔌 Attempting to connect to:", wsUrl);
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
          console.log("✅ Connected to AI server");
          setIsConnected(true);
          reconnectAttempts = 0; // Reset reconnect attempts on successful connection
          
          // Add connection status message only if not already connected
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.text.includes("Connected to AI server")) {
              return prev; // Don't add duplicate connection message
            }
            return [...prev, {
              id: generateUniqueId(),
              sender: "system",
              text: "🟢 Connected to AI server",
              timestamp: new Date(),
              type: "text"
            }];
          });
        };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📨 Received:", data);

          if (data.type === "thinking") {
            // Add thinking message
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "ai",
              text: "🤔 " + data.message,
              timestamp: new Date(),
              type: "thinking"
            }]);
          } else if (data.type === "action") {
            // Add action message
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "ai",
              text: "⚡ " + data.message,
              timestamp: new Date(),
              type: "action"
            }]);
          } else if (data.final_result) {
            // Add final result
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "ai",
              text: data.final_result,
              timestamp: new Date(),
              type: "result"
            }]);
            setSessionId(data.session_id);
            setLoading(false);
            setCurrentTask(null);
          } else if (data.type === "error") {
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "system",
              text: "❌ Error: " + data.error,
              timestamp: new Date(),
              type: "text"
            }]);
            setLoading(false);
          } else if (data.response) {
            // Handle regular responses
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "ai",
              text: data.response,
              timestamp: new Date(),
              type: "result"
            }]);
            setLoading(false);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      ws.current.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        console.error("WebSocket readyState:", ws.current?.readyState);
        console.error("WebSocket URL:", wsUrl);
        setIsConnected(false);
        
        // Don't spam error messages - only show if not already showing one
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.text.includes("Connection error")) {
            return prev; // Don't add duplicate error message
          }
          return [...prev, {
            id: generateUniqueId(),
            sender: "system",
            text: "❌ Connection error. Retrying...",
            timestamp: new Date(),
            type: "text"
          }];
        });
      };

        ws.current.onclose = (event) => {
          console.log("🔌 WebSocket closed:", event.code, event.reason);
          setIsConnected(false);
          
          // Only attempt to reconnect if we haven't exceeded max attempts
          if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000); // Exponential backoff, max 10s
            
            console.log(`🔄 Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay}ms...`);
            
            reconnectTimeout = setTimeout(() => {
              connectWebSocket();
            }, delay);
          } else {
            console.error("❌ Max reconnection attempts reached");
            setMessages(prev => [...prev, {
              id: generateUniqueId(),
              sender: "system",
              text: "❌ Connection failed. Please refresh the page.",
              timestamp: new Date(),
              type: "delete"
            }]);
          }
        };
      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, []);

  // Send message function
  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN || loading) {
      return;
    }
    
    const userMessage = input.trim();
    setInput("");
    setLoading(true);

    // Add user message
    const userMsg: Message = {
      id: generateUniqueId(),
      sender: "user",
      text: userMessage,
      timestamp: new Date(),
      type: "text"
    };
    setMessages(prev => [...prev, userMsg]);

    // Add thinking indicator
    const thinkingMsg: Message = {
      id: generateUniqueId(),
      sender: "ai",
      text: "🤔 Analyzing your request...",
      timestamp: new Date(),
      type: "thinking",
      isTyping: true
    };
    setMessages(prev => [...prev, thinkingMsg]);

    try {
      // Send message via WebSocket
      const messageData = {
        message: userMessage,
        session_id: sessionId,
        type: "user_message"
      };
      
      console.log("📤 Sending:", messageData);
      ws.current.send(JSON.stringify(messageData));
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, {
        id: generateUniqueId(),
        sender: "system",
        text: "❌ Failed to send message",
        timestamp: new Date(),
        type: "text"
      }]);
      setLoading(false);
    }
  }

  // Format timestamp
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={styles.app}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>🤖</span>
            <span className={styles.logoText}>AI Assistant</span>
          </div>
          <div className={styles.connectionStatus}>
            <div className={`${styles.statusDot} ${isConnected ? styles.connected : styles.disconnected}`}></div>
            <span className={styles.statusText}>
              {isConnected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className={styles.main}>
        <div className={styles.messages}>
          {messages.map((msg) => (
            <div key={msg.id} className={`${styles.message} ${styles[msg.sender]}`}>
              <div className={styles.messageContent}>
                <div className={styles.avatar}>
                  {msg.sender === "user" ? "👤" : msg.sender === "ai" ? "🤖" : "🔧"}
                </div>
                <div className={styles.messageBody}>
                  <div className={styles.messageText}>
                    {msg.text}
                    {msg.isTyping && <span className={styles.typingIndicator}>...</span>}
                  </div>
                  <div className={styles.messageTime}>
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {loading && (
            <div className={`${styles.message} ${styles.ai}`}>
              <div className={styles.messageContent}>
                <div className={styles.avatar}>🤖</div>
                <div className={styles.messageBody}>
                  <div className={styles.messageText}>
                    <span className={styles.typingIndicator}>AI is thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <footer className={styles.footer}>
        <form onSubmit={sendMessage} className={styles.inputForm}>
          <div className={styles.inputContainer}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className={styles.input}
              placeholder={isConnected ? "Ask me anything..." : "Connecting to server..."}
              disabled={!isConnected || loading}
              autoFocus
            />
            <button 
              type="submit" 
              disabled={!input.trim() || !isConnected || loading}
              className={styles.sendButton}
            >
              {loading ? "⏳" : "🚀"}
            </button>
          </div>
        </form>
        
        {/* Quick suggestions */}
        {isConnected && messages.length <= 2 && (
          <div className={styles.suggestions}>
            <p className={styles.suggestionsTitle}>Try asking:</p>
            <div className={styles.suggestionChips}>
              <button 
                className={styles.suggestionChip}
                onClick={() => setInput("Book me a flight from New York to London")}
              >
                ✈️ Book a flight
              </button>
              <button 
                className={styles.suggestionChip}
                onClick={() => setInput("Research the latest AI developments")}
              >
                🔍 Research AI trends
              </button>
              <button 
                className={styles.suggestionChip}
                onClick={() => setInput("Write a professional email")}
              >
                📧 Write an email
              </button>
            </div>
          </div>
        )}
      </footer>
    </div>
  );
}