import { useState } from "react";
import { triggerReview } from "../api/client";

export function ReviewPanel() {
  const [repo, setRepo] = useState(".");
  const [target, setTarget] = useState("HEAD~1");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReview = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await triggerReview(repo, target);
      setResult(data.content);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Code Review</h2>
      <div style={{ display: "flex", gap: 12, marginTop: 16, marginBottom: 16 }}>
        <input
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          placeholder="Repo path"
          style={inputStyle}
        />
        <input
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="Git target (branch/commit)"
          style={inputStyle}
        />
        <button onClick={handleReview} disabled={loading} style={btnStyle}>
          {loading ? "Reviewing..." : "Run Review"}
        </button>
      </div>

      {error && <div style={{ color: "#f87171", marginBottom: 12 }}>Error: {error}</div>}

      {result && (
        <div style={{ background: "#1a1a1a", border: "1px solid #333", borderRadius: 8, padding: 20 }}>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 14, lineHeight: 1.6 }}>
            {result}
          </pre>
        </div>
      )}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "8px 12px",
  background: "#111",
  border: "1px solid #333",
  borderRadius: 4,
  color: "#fff",
  flex: 1,
};

const btnStyle: React.CSSProperties = {
  padding: "8px 20px",
  background: "#3b82f6",
  border: "none",
  borderRadius: 4,
  color: "#fff",
  cursor: "pointer",
};
