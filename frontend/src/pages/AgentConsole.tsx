import { AgentStream } from "../components/AgentStream";

export function AgentConsole() {
  return (
    <div>
      <h2>Agent Console</h2>
      <p style={{ color: "#888", marginTop: 8 }}>
        Real-time WebSocket connection to the DevFlow agent system.
      </p>
      <div style={{ marginTop: 24 }}>
        <AgentStream />
      </div>
    </div>
  );
}
