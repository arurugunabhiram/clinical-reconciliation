import { useState } from "react";
import MedicationForm from "../components/reconcile/MedicationForm";
import ReconcileResult from "../components/reconcile/ReconcileResult";
import LoadingSpinner from "../components/shared/LoadingSpinner";
import { reconcileMedication } from "../api/client";

export default function ReconcilePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await reconcileMedication(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <MedicationForm onSubmit={handleSubmit} loading={loading} />
      {loading && <LoadingSpinner />}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}
      {result && <ReconcileResult data={result} />}
    </div>
  );
}
