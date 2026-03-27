async function request(path, body) {
  const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").trim();
  const API_KEY = (import.meta.env.VITE_API_KEY || "").trim();
  if (!API_KEY) {
    throw new Error("VITE_API_KEY is not set. Add it to frontend/.env and restart.");
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err?.detail?.error?.message || err?.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function reconcileMedication(payload) {
  return request("/api/reconcile/medication", payload);
}

export function validateDataQuality(payload) {
  return request("/api/validate/data-quality", payload);
}
