import { useState } from "react";

const EXAMPLE_RECORD = {
  patient_id: "P-20087",
  first_name: "Jane",
  last_name: "Doe",
  date_of_birth: "1958-03-14",
  gender: "female",
  medications: [
    { drug_name: "Metformin", dose: "1000mg", frequency: "twice daily" },
    { drug_name: "Lisinopril", dose: "20mg", frequency: "once daily" },
  ],
  diagnoses: ["Type 2 Diabetes", "Hypertension", "Hypertension"],
  allergies: [],
  vital_signs: {
    heart_rate: 340,
    blood_pressure: "220/140",
    temperature: 98.6,
    respiratory_rate: 18,
    spo2: 97,
  },
  lab_results: { eGFR: "22 mL/min", HbA1c: "9.2%" },
  last_updated: "2024-04-10",
};

export default function PatientRecordForm({ onSubmit, loading }) {
  const [json, setJson] = useState("");
  const [parseError, setParseError] = useState(null);

  function loadExample() {
    setJson(JSON.stringify(EXAMPLE_RECORD, null, 2));
    setParseError(null);
  }

  function handleSubmit(e) {
    e.preventDefault();
    try {
      const record = JSON.parse(json);
      setParseError(null);
      onSubmit({ record });
    } catch {
      setParseError("Invalid JSON. Please check the record format.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">Data Quality Validation</h2>
        <button
          type="button"
          onClick={loadExample}
          className="text-sm px-3 py-1 rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200"
        >
          Load Example (implausible vitals)
        </button>
      </div>

      <p className="text-sm text-gray-500">
        Paste a patient record as JSON. The example includes implausible vital signs (HR 340, BP 220/140),
        duplicate diagnoses, missing allergies, and stale data to demonstrate validation scoring.
      </p>

      <div>
        <textarea
          required
          rows={18}
          value={json}
          onChange={(e) => { setJson(e.target.value); setParseError(null); }}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono focus:ring-indigo-500 focus:border-indigo-500"
          placeholder='{"patient_id": "P-001", "first_name": "Jane", ...}'
        />
        {parseError && (
          <p className="text-red-600 text-sm mt-1">{parseError}</p>
        )}
      </div>

      <button type="submit" disabled={loading}
        className="w-full bg-indigo-600 text-white py-2.5 rounded-md font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">
        {loading ? "Validating..." : "Validate Record"}
      </button>
    </form>
  );
}
