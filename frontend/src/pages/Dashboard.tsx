import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { listAgents } from "../api/client";

interface AgentInfo {
  name: string;
  status: string;
  type: string;
  tools: number;
}

export function Dashboard() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAgents()
      .then((data) => setAgents(data.agents))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>DevFlow Dashboard</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16, marginTop: 16 }}>
        <Link to="/review" style={{ textDecoration: "none" }}>
          <div style={cardStyle}>
            <h3>Code Review</h3>
            <p>Run automated code review on any repository</p>
            <span style={{ color: "#4ade80" }}>Available</span>
          </div>
        </Link>

        <Link to="/console" style={{ textDecoration: "none" }}>
          <div style={cardStyle}>
            <h3>Agent Console</h3>
            <p>Interactive agent debugging & live stream</p>
            <span style={{ color: "#4ade80" }}>Available</span>
          </div>
        </Link>
      </div>

      <h3 style={{ marginTop: 32 }}>Agents</h3>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
          <thead>
            <tr>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Type</th>
              <th style={thStyle}>Tools</th>
              <th style={thStyle}>Status</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.name}>
                <td style={tdStyle}>{a.name}</td>
                <td style={tdStyle}>{a.type}</td>
                <td style={tdStyle}>{a.tools}</td>
                <td style={tdStyle}>
                  <span style={{ color: a.status === "idle" ? "#4ade80" : "#fbbf24" }}>{a.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid #333",
  borderRadius: 8,
  padding: 20,
  background: "#1a1a1a",
  cursor: "pointer",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "8px 12px",
  borderBottom: "1px solid #333",
};

const tdStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderBottom: "1px solid #222",
};
