import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { ReviewPanel } from "./pages/ReviewPanel";
import { AgentConsole } from "./pages/AgentConsole";

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: "100vh", background: "#0d0d0d", color: "#e5e5e5" }}>
        <nav style={{ display: "flex", gap: 24, padding: "16px 32px", borderBottom: "1px solid #222", alignItems: "center" }}>
          <Link to="/" style={{ fontWeight: 700, fontSize: 18, color: "#3b82f6", textDecoration: "none" }}>
            AgentFlow
          </Link>
          <Link to="/" style={navLinkStyle}>Dashboard</Link>
          <Link to="/review" style={navLinkStyle}>Code Review</Link>
          <Link to="/console" style={navLinkStyle}>Agent Console</Link>
        </nav>
        <main style={{ padding: "32px", maxWidth: 1200, margin: "0 auto" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/review" element={<ReviewPanel />} />
            <Route path="/console" element={<AgentConsole />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

const navLinkStyle: React.CSSProperties = {
  color: "#888",
  textDecoration: "none",
  fontSize: 14,
};

export default App;
