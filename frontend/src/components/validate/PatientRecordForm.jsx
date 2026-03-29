import { useState } from "react";
import InputModeToggle from "../shared/InputModeToggle";
import JsonEditor from "../shared/JsonEditor";
import TagInput from "../shared/TagInput";

const EXAMPLE_RECORD = {
  demographics: { name: "John Doe", dob: "1955-03-15", gender: "M" },
  medications: ["Metformin 500mg", "Lisinopril 10mg"],
  allergies: [],
  conditions: ["Type 2 Diabetes"],
  vital_signs: { blood_pressure: "340/180", heart_rate: 72 },
  last_updated: "2024-06-15",
};

function parseBP(val) {
  const parts = val.split("/");
  if (parts.length === 2) {
    const sys = parseInt(parts[0], 10);
    return isFinite(sys) ? sys : null;
  }
  return null;
}

export default function PatientRecordForm({ onSubmit, loading }) {
  const [inputMode, setInputMode] = useState("form");
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [medications, setMedications] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [bp, setBp] = useState("");
  const [hr, setHr] = useState("");
  const [temp, setTemp] = useState("");
  const [spo2, setSpo2] = useState("");
  const [jsonValue, setJsonValue] = useState(JSON.stringify(EXAMPLE_RECORD, null, 2));
  const [error, setError] = useState(null);
  const [modeVisible, setModeVisible] = useState(true);

  const bpSystolic = bp ? parseBP(bp) : null;
  const bpWarning = bpSystolic !== null && bpSystolic > 300;
  const hrNum = hr ? parseInt(hr, 10) : null;
  const hrWarning = hrNum !== null && (hrNum > 250 || hrNum < 20);

  function buildFormPayload() {
    const vitalSigns = {};
    if (bp.trim()) vitalSigns.blood_pressure = bp.trim();
    if (hr.trim()) vitalSigns.heart_rate = parseInt(hr, 10);
    if (temp.trim()) vitalSigns.temperature = parseFloat(temp);
    if (spo2.trim()) vitalSigns.spo2 = parseFloat(spo2);

    return {
      demographics: {
        name: name || undefined,
        dob: dob || undefined,
        gender: gender || undefined,
      },
      medications,
      allergies,
      conditions,
      vital_signs: Object.keys(vitalSigns).length ? vitalSigns : undefined,
      last_updated: lastUpdated || undefined,
    };
  }

  function populateFormFromJson(parsed) {
    const d = parsed.demographics || {};
    setName(d.name || "");
    setDob(d.dob || "");
    setGender(d.gender || "");
    setMedications(parsed.medications || []);
    setAllergies(parsed.allergies || []);
    setConditions(parsed.conditions || []);
    const vs = parsed.vital_signs || {};
    setBp(vs.blood_pressure || "");
    setHr(vs.heart_rate !== undefined ? String(vs.heart_rate) : "");
    setTemp(vs.temperature !== undefined ? String(vs.temperature) : "");
    setSpo2(vs.spo2 !== undefined ? String(vs.spo2) : "");
    setLastUpdated(parsed.last_updated || "");
  }

  function switchMode(newMode) {
    if (newMode === inputMode) return;
    if (newMode === "json") {
      try {
        setJsonValue(JSON.stringify(buildFormPayload(), null, 2));
      } catch {/* keep existing */}
    } else {
      try {
        populateFormFromJson(JSON.parse(jsonValue));
      } catch {
        setError("Cannot parse JSON to populate form. Stay in JSON mode.");
        return;
      }
    }
    setModeVisible(false);
    setTimeout(() => { setInputMode(newMode); setModeVisible(true); }, 150);
  }

  function loadExample() {
    setJsonValue(JSON.stringify(EXAMPLE_RECORD, null, 2));
    populateFormFromJson(EXAMPLE_RECORD);
  }

  function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      const payload = inputMode === "json" ? JSON.parse(jsonValue) : buildFormPayload();
      onSubmit(payload);
    } catch {
      setError("Invalid JSON. Please check your input.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <p className="font-semibold uppercase tracking-widest text-gray-500" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
          Patient Record
        </p>
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

      {/* Content */}
      <div style={{ opacity: modeVisible ? 1 : 0, transition: "opacity 150ms ease" }}>
        {inputMode === "form" ? (
          <div className="space-y-5">
            {/* Section 1: Demographics */}
            <div
              className="bg-white rounded-lg border border-gray-200 p-4 space-y-4"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <p className="font-semibold uppercase tracking-widest text-gray-500" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                Demographics
              </p>
              <div className="grid grid-cols-4 gap-3 items-end">
                <div className="col-span-2">
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    Full Name
                  </label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                    style={{ height: "38px" }}
                  />
                </div>
                <div>
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
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
                    className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white appearance-none focus:outline-none focus:ring-2 focus:border-teal-600"
                    style={{ height: "38px" }}
                  >
                    <option value="">Select</option>
                    <option value="M">M</option>
                    <option value="F">F</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                  Record Date
                  <span className="ml-2 normal-case text-gray-400 font-normal" style={{ fontSize: "11px" }}>
                    — used for timeliness scoring
                  </span>
                </label>
                <input
                  type="date"
                  value={lastUpdated}
                  onChange={(e) => setLastUpdated(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                  style={{ height: "38px", width: "200px" }}
                />
              </div>
            </div>

            {/* Section 2: Medications */}
            <div
              className="bg-white rounded-lg border border-gray-200 p-4"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                Current Medications
              </label>
              <TagInput
                value={medications}
                onChange={setMedications}
                placeholder="Type medication and press Enter, e.g. Metformin 500mg"
              />
            </div>

            {/* Section 3: Conditions & Allergies */}
            <div
              className="bg-white rounded-lg border border-gray-200 p-4 grid grid-cols-2 gap-4"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <div>
                <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                  Diagnoses
                </label>
                <TagInput
                  value={conditions}
                  onChange={setConditions}
                  placeholder="e.g. Type 2 Diabetes"
                />
              </div>
              <div>
                <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                  Allergies
                </label>
                <TagInput
                  value={allergies}
                  onChange={setAllergies}
                  placeholder="e.g. Penicillin"
                />
                <p className="mt-1 text-gray-400" style={{ fontSize: "11px" }}>
                  Empty allergies list will flag as incomplete
                </p>
              </div>
            </div>

            {/* Section 4: Vital Signs */}
            <div
              className="bg-white rounded-lg border border-gray-200 p-4"
              style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
            >
              <p className="font-semibold uppercase tracking-widest text-gray-500 mb-3" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                Vital Signs
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    Blood Pressure
                  </label>
                  <input
                    value={bp}
                    onChange={(e) => setBp(e.target.value)}
                    placeholder="120/80"
                    className={`w-full border rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600 ${bpWarning ? "border-amber-400" : "border-gray-300"}`}
                    style={{ height: "38px" }}
                  />
                  {bpWarning && (
                    <p className="mt-1 text-amber-600 flex items-center gap-1" style={{ fontSize: "12px" }}>
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      </svg>
                      Physiologically implausible — will flag as high severity issue
                    </p>
                  )}
                </div>
                <div>
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    value={hr}
                    onChange={(e) => setHr(e.target.value)}
                    placeholder="72"
                    className={`w-full border rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600 ${hrWarning ? "border-amber-400" : "border-gray-300"}`}
                    style={{ height: "38px" }}
                  />
                  {hrWarning && (
                    <p className="mt-1 text-amber-600 flex items-center gap-1" style={{ fontSize: "12px" }}>
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      </svg>
                      Physiologically implausible — will flag as high severity issue
                    </p>
                  )}
                </div>
                <div>
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    Temperature (°C) <span className="text-gray-400 font-normal normal-case">optional</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={temp}
                    onChange={(e) => setTemp(e.target.value)}
                    placeholder="37.0"
                    className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                    style={{ height: "38px" }}
                  />
                </div>
                <div>
                  <label className="block font-semibold uppercase tracking-widest text-gray-500 mb-1" style={{ fontSize: "11px" }}>
                    SpO2 (%) <span className="text-gray-400 font-normal normal-case">optional</span>
                  </label>
                  <input
                    type="number"
                    value={spo2}
                    onChange={(e) => setSpo2(e.target.value)}
                    placeholder="98"
                    className="w-full border border-gray-300 rounded-md px-3 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:border-teal-600"
                    style={{ height: "38px" }}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <JsonEditor
            value={jsonValue}
            onChange={setJsonValue}
            placeholder='{"demographics": {...}, "medications": [...], ...}'
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
          <button type="button" onClick={() => setError(null)} className="text-sm text-gray-400 hover:text-gray-600">Dismiss</button>
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
        {loading ? "Analyzing…" : "Validate Record Quality"}
      </button>
    </form>
  );
}
