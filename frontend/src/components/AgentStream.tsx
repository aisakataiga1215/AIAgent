import { useWebSocket } from "../hooks/useWebSocket";

export function AgentStream() {
  const { messages, connected, send } = useWebSocket();
  const statusColor = connected ? "#4ade80" : "#f87171";

  return (
    <div style={{ padding: 16, border: "1px solid #333", borderRadius: 8 }}>
      <h3>
        Agent Stream{" "}
        <span style={{ color: statusColor, fontSize: 12 }}>
          {connected ? "connected" : "disconnected"}
        </span>
      </h3>
      <button onClick={() => send("ping")} style={{ marginBottom: 8 }}>
        Ping
      </button>
      <div
        style={{
          background: "#111",
          color: "#0f0",
          padding: 12,
          borderRadius: 4,
          maxHeight: 300,
          overflowY: "auto",
          fontFamily: "monospace",
          fontSize: 13,
        }}
      >
        {messages.length === 0 && <div style={{ color: "#555" }}>Waiting for messages...</div>}
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 4 }}>
            [{m.type}] {JSON.stringify(m)}
          </div>
        ))}
      </div>
    </div>
  );
}
