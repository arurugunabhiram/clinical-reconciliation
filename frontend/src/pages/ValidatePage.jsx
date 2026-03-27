import { useState } from "react";
import PatientRecordForm from "../components/validate/PatientRecordForm";
import QualityScoreCard from "../components/validate/QualityScoreCard";
import LoadingSpinner from "../components/shared/LoadingSpinner";
import { validateDataQuality } from "../api/client";

export default function ValidatePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await validateDataQuality(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PatientRecordForm onSubmit={handleSubmit} loading={loading} />
      {loading && <LoadingSpinner />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}
      {result && <QualityScoreCard data={result} />}
    </div>
  );
}
