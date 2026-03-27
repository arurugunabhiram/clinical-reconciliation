import { useState } from "react";

const EMPTY_SOURCE = {
  source_name: "",
  drug_name: "",
  dose: "",
  frequency: "",
  last_updated: "",
  reliability: "medium",
};

const EXAMPLE_PAYLOAD = {
  patient_id: "P-10042",
  sources: [
    {
      source_name: "Hospital EHR",
      drug_name: "Metformin",
      dose: "1000mg",
      frequency: "twice daily",
      last_updated: "2025-12-01",
      reliability: "high",
    },
    {
      source_name: "Community Pharmacy",
      drug_name: "Metformin",
      dose: "500mg",
      frequency: "once daily",
      last_updated: "2025-06-15",
      reliability: "medium",
    },
    {
      source_name: "Patient Self-Report",
      drug_name: "Metformin",
      dose: "500mg",
      frequency: "twice daily",
      last_updated: "2025-11-20",
      reliability: "low",
    },
  ],
  patient_context: {
    age: 62,
    conditions: ["Type 2 Diabetes", "CKD Stage 3"],
    allergies: ["Penicillin"],
    lab_values: { eGFR: "38 mL/min" },
  },
};

export default function MedicationForm({ onSubmit, loading }) {
  const [patientId, setPatientId] = useState("");
  const [sources, setSources] = useState([{ ...EMPTY_SOURCE }, { ...EMPTY_SOURCE }]);
  const [age, setAge] = useState("");
  const [conditions, setConditions] = useState("");
  const [allergies, setAllergies] = useState("");
  const [labValues, setLabValues] = useState("");

  function updateSource(i, field, value) {
    setSources((prev) => {
      const copy = [...prev];
      copy[i] = { ...copy[i], [field]: value };
      return copy;
    });
  }

  function addSource() {
    setSources((prev) => [...prev, { ...EMPTY_SOURCE }]);
  }

  function removeSource(i) {
    if (sources.length <= 2) return;
    setSources((prev) => prev.filter((_, idx) => idx !== i));
  }

  function loadExample() {
    setPatientId(EXAMPLE_PAYLOAD.patient_id);
    setSources(EXAMPLE_PAYLOAD.sources.map((s) => ({ ...s })));
    setAge(String(EXAMPLE_PAYLOAD.patient_context.age));
    setConditions(EXAMPLE_PAYLOAD.patient_context.conditions.join(", "));
    setAllergies(EXAMPLE_PAYLOAD.patient_context.allergies.join(", "));
    setLabValues(
      Object.entries(EXAMPLE_PAYLOAD.patient_context.lab_values)
        .map(([k, v]) => `${k}=${v}`)
        .join(", ")
    );
  }

  function handleSubmit(e) {
    e.preventDefault();
    const labObj = {};
    if (labValues.trim()) {
      labValues.split(",").forEach((pair) => {
        const [k, ...rest] = pair.split("=");
        if (k && rest.length) labObj[k.trim()] = rest.join("=").trim();
      });
    }
    onSubmit({
      patient_id: patientId,
      sources,
      patient_context: {
        age: age ? Number(age) : null,
        conditions: conditions ? conditions.split(",").map((s) => s.trim()).filter(Boolean) : [],
        allergies: allergies ? allergies.split(",").map((s) => s.trim()).filter(Boolean) : [],
        lab_values: labObj,
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">Medication Reconciliation</h2>
        <button
          type="button"
          onClick={loadExample}
          className="text-sm px-3 py-1 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
        >
          Load Example
        </button>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Patient ID</label>
        <input
          required
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="e.g. P-10042"
        />
      </div>

      <fieldset className="border border-gray-200 rounded-lg p-4">
        <legend className="text-sm font-medium text-gray-700 px-1">Medication Sources (min 2)</legend>
        {sources.map((src, i) => (
          <div key={i} className="grid grid-cols-6 gap-2 mb-3 items-end">
            <div>
              <label className="block text-xs text-gray-500">Source Name</label>
              <input required value={src.source_name} onChange={(e) => updateSource(i, "source_name", e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="Hospital EHR" />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Drug Name</label>
              <input required value={src.drug_name} onChange={(e) => updateSource(i, "drug_name", e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="Metformin" />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Dose</label>
              <input required value={src.dose} onChange={(e) => updateSource(i, "dose", e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="500mg" />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Frequency</label>
              <input required value={src.frequency} onChange={(e) => updateSource(i, "frequency", e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="twice daily" />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Last Updated</label>
              <input required type="date" value={src.last_updated} onChange={(e) => updateSource(i, "last_updated", e.target.value)}
                className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
            </div>
            <div className="flex gap-1">
              <div className="flex-1">
                <label className="block text-xs text-gray-500">Reliability</label>
                <select value={src.reliability} onChange={(e) => updateSource(i, "reliability", e.target.value)}
                  className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              {sources.length > 2 && (
                <button type="button" onClick={() => removeSource(i)}
                  className="self-end text-red-500 hover:text-red-700 text-lg px-1 pb-1"
                  title="Remove source">&times;</button>
              )}
            </div>
          </div>
        ))}
        <button type="button" onClick={addSource}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium">
          + Add Source
        </button>
      </fieldset>

      <fieldset className="border border-gray-200 rounded-lg p-4">
        <legend className="text-sm font-medium text-gray-700 px-1">Patient Context (optional)</legend>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Age</label>
            <input type="number" value={age} onChange={(e) => setAge(e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="62" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Conditions (comma-separated)</label>
            <input value={conditions} onChange={(e) => setConditions(e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="Type 2 Diabetes, CKD Stage 3" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Allergies (comma-separated)</label>
            <input value={allergies} onChange={(e) => setAllergies(e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="Penicillin" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Lab Values (key=value, comma-separated)</label>
            <input value={labValues} onChange={(e) => setLabValues(e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" placeholder="eGFR=38 mL/min" />
          </div>
        </div>
      </fieldset>

      <button type="submit" disabled={loading}
        className="w-full bg-indigo-600 text-white py-2.5 rounded-md font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">
        {loading ? "Reconciling..." : "Reconcile Medication"}
      </button>
    </form>
  );
}
