const BASE = "/api/v1";

export async function triggerReview(repo: string, target: string) {
  const res = await fetch(`${BASE}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo, target }),
  });
  if (!res.ok) throw new Error(`Review failed: ${res.statusText}`);
  return res.json();
}

export async function runWorkflow(name: string, repo: string, target: string) {
  const res = await fetch(`${BASE}/workflow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, repo, target }),
  });
  if (!res.ok) throw new Error(`Workflow failed: ${res.statusText}`);
  return res.json();
}

export async function listAgents() {
  const res = await fetch(`${BASE}/agent/list`);
  return res.json();
}

export async function ingestCodebase(repo: string, reset = false) {
  const res = await fetch(`${BASE}/knowledge/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo, reset }),
  });
  return res.json();
}

export async function searchKnowledge(query: string, topK = 5) {
  const res = await fetch(`${BASE}/knowledge/search?query=${encodeURIComponent(query)}&top_k=${topK}`);
  return res.json();
}
