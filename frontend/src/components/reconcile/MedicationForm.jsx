import { useState } from "react";
import InputModeToggle from "../shared/InputModeToggle";
import JsonEditor from "../shared/JsonEditor";
import TagInput from "../shared/TagInput";

const SOURCE_BORDER_COLORS = [
  "#0d9488", "#1D6FA4", "#7C3AED", "#D97706", "#DC2626",
];

const EXAMPLE_PAYLOAD = {
  patient_context: {
    age: 67,
    conditions: ["Type 2 Diabetes", "Hypertension"],
    recent_labs: { eGFR: 45 },
  },
  sources: [
    { system: "Hospital EHR", medication: "Metformin 1000mg twice daily", last_updated: "2024-10-15", source_reliability: "high" },
    { system: "Primary Care", medication: "Metformin 500mg twice daily", last_updated: "2025-01-20", source_reliability: "high" },
    { system: "Pharmacy", medication: "Metformin 1000mg daily", last_filled: "2025-01-25", source_reliability: "medium" },
  ],
};

const RELIABILITY_DOTS = {
  high: "bg-green-500",
  medium: "bg-amber-400",
  low: "bg-red-400",
};

const EMPTY_SOURCE = {
  system: "",
  medication: "",
  dose: "",
  frequency: "",
  date_type: "last_updated",
  date_value: "",
  source_reliability: "medium",
};

function sourcesToPayload(sources) {
  return sources.map((src) => {
    const base = {
      system: src.system,
      medication: [src.medication, src.dose, src.frequency].filter(Boolean).join(" "),
      source_reliability: src.source_reliability,
    };
    base[src.date_type] = src.date_value;
    return base;
  });
}

function payloadToSources(sources) {
  return sources.map((s) => {
    const dateType = s.last_filled ? "last_filled" : "last_updated";
    return {
      system: s.system || "",
      medication: s.medication || "",
      dose: "",
      frequency: "",
      date_type: dateType,
      date_value: s.last_filled || s.last_updated || "",
      source_reliability: s.source_reliability || "medium",
    };
  });
}

export default function MedicationForm({ onSubmit, loading }) {
  const [inputMode, setInputMode] = useState("form");
  const [sources, setSources] = useState([{ ...EMPTY_SOURCE }, { ...EMPTY_SOURCE }]);
  const [contextOpen, setContextOpen] = useState(false);
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [labRows, setLabRows] = useState([{ key: "eGFR", value: "" }]);
  const [jsonValue, setJsonValue] = useState(JSON.stringify(EXAMPLE_PAYLOAD, null, 2));
  const [error, setError] = useState(null);
  const [modeVisible, setModeVisible] = useState(true);

  function updateSource(i, field, val) {
    setSources((prev) => { const c = [...prev]; c[i] = { ...c[i], [field]: val }; return c; });
  }

  function addSource() {
    setSources((prev) => [...prev, { ...EMPTY_SOURCE }]);
  }

  function removeSource(i) {
    if (sources.length <= 2) return;
    setSources((prev) => prev.filter((_, idx) => idx !== i));
  }

  function buildFormPayload() {
    const labs = {};
    labRows.forEach(({ key, value }) => {
      if (key.trim() && value.trim()) {
        const num = parseFloat(value);
        labs[key.trim()] = isFinite(num) ? num : value.trim();
      }
    });
    return {
      patient_context: age || conditions.length || Object.keys(labs).length
        ? { age: age ? Number(age) : undefined, gender: gender || undefined, conditions, recent_labs: labs }
        : undefined,
      sources: sourcesToPayload(sources),
    };
  }

  function switchMode(newMode) {
    if (newMode === inputMode) return;
    if (newMode === "json") {
      // Form → JSON
      try {
        const payload = buildFormPayload();
        setJsonValue(JSON.stringify(payload, null, 2));
      } catch {/* keep existing */}
    } else {
      // JSON → Form
      try {
        const parsed = JSON.parse(jsonValue);
        if (parsed.sources) setSources(payloadToSources(parsed.sources));
        const ctx = parsed.patient_context;
        if (ctx) {
          if (ctx.age) setAge(String(ctx.age));
          if (ctx.conditions) setConditions(ctx.conditions);
          if (ctx.recent_labs) {
            setLabRows(Object.entries(ctx.recent_labs).map(([k, v]) => ({ key: k, value: String(v) })));
          }
          setContextOpen(true);
        }
      } catch {
        setError("Cannot parse JSON to populate form. Stay in JSON mode.");
        return;
      }
    }
    setModeVisible(false);
    setTimeout(() => { setInputMode(newMode); setModeVisible(true); }, 150);
  }

  function loadExample() {
    setJsonValue(JSON.stringify(EXAMPLE_PAYLOAD, null, 2));
    setSources(payloadToSources(EXAMPLE_PAYLOAD.sources));
    setAge("67");
    setConditions(EXAMPLE_PAYLOAD.patient_context.conditions);
    setLabRows([{ key: "eGFR", value: "45" }]);
    setContextOpen(true);
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (inputMode === "form") {
      const filledSources = sources.filter((s) => s.medication.trim());
      if (filledSources.length < 2) {
        setError("At least 2 sources must have a medication entered before reconciling.");
        return;
      }
    }
    try {
      const payload = inputMode === "json" ? JSON.parse(jsonValue) : buildFormPayload();
      if (!payload.sources || payload.sources.length < 1) {
        setError("At least 1 source is required.");
        return;
      }
      onSubmit(payload);
    } catch {
      setError("Invalid JSON. Please check your input.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold uppercase tracking-widest text-gray-500" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
            Medication Sources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={loadExample}
            className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-3 py-1 rounded transition-colors"
            style={{ fontSize: "14px" }}
          >
            Load Example
          </button>
          <InputModeToggle mode={inputMode} onChange={switchMode} />
        </div>
      </div>

      {/* Content area with fade transition */}
      <div style={{ opacity: modeVisible ? 1 : 0, transition: "opacity 150ms ease" }}>
        {inputMode === "form" ? (
          <div className="space-y-3">
            {sources.map((src, i) => (
              <div
                key={i}
                className="bg-white rounded-lg border border-gray-200 p-4"
                style={{
                  boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
                  borderLeft: `3px solid ${SOURCE_BORDER_COLORS[i % SOURCE_BORDER_COLORS.length]}`,
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-flex items-center justify-center rounded-full text-white font-semibold"
                      style={{
                        width: "20px",
                        height: "20px",
                        fontSize: "11px",
                        backgroundColor: SOURCE_BORDER_COLORS[i % SOURCE_BORDER_COLORS.length],
                      }}
                    >
                      {i + 1}
                    </span>
                    <span className="text-sm font-medium text-gray-700">
                      {src.system || `Source ${i + 1}`}
                    </span>
                  </div>
                  {sources.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeSource(i)}
                      className="text-gray-400 hover:text-gray-600 text-lg leading-none"
                      aria-label="Remove source"
                    >
                      ×
                    </button>
                  )}
                </div>

                {/* Row 1: System, Date, Reliability */}
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      System
                    </label>
                    <input
                      required
                      value={src.system}
                      onChange={(e) => updateSource(i, "system", e.target.value)}
                      placeholder="Hospital EHR"
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px", fontSize: "14px" }}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Last Updated
                    </label>
                    <input
                      type="date"
                      value={src.date_value}
                      onChange={(e) => updateSource(i, "date_value", e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px", fontSize: "14px" }}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Reliability
                    </label>
                    <div className="relative">
                      <select
                        value={src.source_reliability}
                        onChange={(e) => updateSource(i, "source_reliability", e.target.value)}
                        className="w-full border border-gray-300 rounded-md pl-7 pr-3 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:border-teal-600"
                        style={{ height: "38px", fontSize: "14px" }}
                      >
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                      <span
                        className={`absolute left-2.5 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${RELIABILITY_DOTS[src.source_reliability]}`}
                      />
                    </div>
                  </div>
                </div>

                {/* Row 2: Medication (prominent), Dose, Frequency */}
                <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 100px 1fr" }}>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Medication
                    </label>
                    <input
                      required
                      value={src.medication}
                      onChange={(e) => updateSource(i, "medication", e.target.value)}
                      placeholder="Metformin"
                      className="w-full border border-gray-300 rounded-md px-3 font-medium text-gray-900 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px", fontSize: "15px" }}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Dose
                    </label>
                    <input
                      value={src.dose}
                      onChange={(e) => updateSource(i, "dose", e.target.value)}
                      placeholder="500mg"
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px", fontSize: "14px" }}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Frequency
                    </label>
                    <input
                      value={src.frequency}
                      onChange={(e) => updateSource(i, "frequency", e.target.value)}
                      placeholder="twice daily"
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px", fontSize: "14px" }}
                    />
                  </div>
                </div>
              </div>
            ))}

            <button
              type="button"
              onClick={addSource}
              className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-3 py-1.5 rounded transition-colors"
              style={{ fontSize: "14px" }}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Add Another Source
            </button>

            {/* Patient Context — collapsible */}
            <div
              className="bg-white rounded-lg border border-gray-200 overflow-hidden"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)" }}
            >
              <button
                type="button"
                onClick={() => setContextOpen((o) => !o)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold uppercase tracking-widest text-gray-500" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                  Patient Context
                </span>
                <svg
                  className={`w-4 h-4 text-gray-400 transition-transform ${contextOpen ? "rotate-180" : ""}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {contextOpen && (
                <div className="px-4 pb-4 border-t border-gray-100 grid grid-cols-2 gap-4 pt-4">
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                      Age
                    </label>
                    <input
                      type="number"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="67"
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px" }}
                    />
                  </div>
                  <div>
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                      Gender
                    </label>
                    <select
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                      style={{ height: "38px" }}
                    >
                      <option value="">Select</option>
                      <option value="M">M</option>
                      <option value="F">F</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                      Conditions
                    </label>
                    <TagInput
                      value={conditions}
                      onChange={setConditions}
                      placeholder="Type 2 Diabetes, Hypertension…"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px" }}>
                      Lab Values
                    </label>
                    <div className="space-y-2">
                      {labRows.map((row, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <input
                            value={row.key}
                            onChange={(e) => setLabRows((prev) => prev.map((r, ri) => ri === idx ? { ...r, key: e.target.value } : r))}
                            placeholder="eGFR"
                            className="border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                            style={{ width: "120px", height: "34px" }}
                          />
                          <span className="text-gray-400 text-sm">=</span>
                          <input
                            value={row.value}
                            onChange={(e) => setLabRows((prev) => prev.map((r, ri) => ri === idx ? { ...r, value: e.target.value } : r))}
                            placeholder="45"
                            className="border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                            style={{ width: "100px", height: "34px" }}
                          />
                          {labRows.length > 1 && (
                            <button type="button" onClick={() => setLabRows((prev) => prev.filter((_, ri) => ri !== idx))} className="text-gray-400 hover:text-gray-600">×</button>
                          )}
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => setLabRows((prev) => [...prev, { key: "", value: "" }])}
                        className="text-gray-500 hover:text-gray-700 text-sm"
                      >
                        + Add lab value
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <JsonEditor
            value={jsonValue}
            onChange={setJsonValue}
            placeholder='{"patient_context": {...}, "sources": [...]}'
            minHeight={280}
          />
        )}
      </div>

      {error && (
        <div className="flex items-start gap-3 px-4 py-3 bg-white border-l-4 border-red-500 rounded-md" style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
          </svg>
          <span className="text-sm text-gray-700 flex-1">{error}</span>
          <button type="button" onClick={() => setError(null)} className="text-sm text-gray-400 hover:text-gray-600">
            Dismiss
          </button>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 text-white font-medium rounded-md transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ height: "44px", backgroundColor: loading ? "#0f766e" : "#0d9488", fontSize: "15px" }}
        onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#0f766e"; }}
        onMouseLeave={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#0d9488"; }}
      >
        {loading && (
          <svg className="w-4 h-4 animate-spin text-white/70" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {loading ? "Analyzing sources…" : "Reconcile Medication"}
      </button>
    </form>
  );
}
