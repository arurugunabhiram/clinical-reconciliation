const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "";

async function request(path, body) {
  const headers = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
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
