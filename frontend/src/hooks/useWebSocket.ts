import { useEffect, useRef, useState } from "react";

interface WSMessage {
  type: string;
  [key: string]: unknown;
}

export function useWebSocket(url: string = "ws://localhost:8000/api/v1/ws") {
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setMessages((prev) => [...prev.slice(-50), msg]);
      } catch {
        // ignore non-JSON
      }
    };

    return () => ws.close();
  }, [url]);

  const send = (action: string, data: Record<string, unknown> = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    }
  };

  return { messages, connected, send };
}
