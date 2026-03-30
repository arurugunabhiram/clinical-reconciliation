function formatApiError(err, status) {
  const detail = err?.detail;

  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const path = Array.isArray(d?.loc) ? d.loc.join(".") : "request";
        const msg = d?.msg || "Invalid value";
        return `${path}: ${msg}`;
      })
      .join("; ");
  }

  return err?.detail?.error?.message || detail || `HTTP ${status}`;
}

async function request(path, body, apiKey) {
  const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (!rawBaseUrl || !rawBaseUrl.trim()) {
    throw new Error(
      "VITE_API_BASE_URL is not defined. Set it in the frontend environment before running the app."
    );
  }
  const BASE_URL = rawBaseUrl.trim();
  if (!apiKey) {
    throw new Error("Please enter your API key above before submitting");
  }
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(body),
    });
  } catch (_networkErr) {
    throw new Error(
      `Cannot reach API at ${BASE_URL}. ` +
        "Make sure the backend is running."
    );
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err, res.status));
  }
  return res.json();
}

export function reconcileMedication(payload, apiKey) {
  return request("/api/reconcile/medication", payload, apiKey);
}

export function validateDataQuality(payload, apiKey) {
  return request("/api/validate/data-quality", payload, apiKey);
}
