import { useState } from "react";
import PatientRecordForm from "../components/validate/PatientRecordForm";
import QualityScoreCard from "../components/validate/QualityScoreCard";
import ApproveRejectBar from "../components/shared/ApproveRejectBar";
import { validateDataQuality } from "../api/client";
import useApproval from "../hooks/useApproval";

function SkeletonLoader() {
  return (
    <div className="mt-6 bg-white rounded-lg border border-gray-200 p-5 space-y-3" style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
      <div className="h-4 rounded bg-gray-200 animate-pulse" style={{ width: "100%" }} />
      <div className="h-4 rounded bg-gray-200 animate-pulse" style={{ width: "80%" }} />
      <div className="h-4 rounded bg-gray-200 animate-pulse" style={{ width: "60%" }} />
    </div>
  );
}

export default function ValidatePage({ apiKey }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [resultKey, setResultKey] = useState(0);
  const [recordId, setRecordId] = useState(null);
  const [patientName, setPatientName] = useState(null);
  const [validatePayload, setValidatePayload] = useState(null);

  const { status, approve, reject } = useApproval(recordId, patientName, "validate", validatePayload);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    setResult(null);
    const id =
      payload?.demographics?.name
        ? `${payload.demographics.name}-${Date.now()}`
        : crypto.randomUUID();
    setRecordId(id);
    setPatientName(payload?.demographics?.name || "Unknown Patient");
    try {
      const data = await validateDataQuality(payload, apiKey);
      setResult(data);
      setValidatePayload({
        overall_score: data.overall_score,
        quality_grade: data.overall_score >= 70 ? "Good" : data.overall_score >= 40 ? "Fair" : "Poor",
        safety_status: data.overall_score >= 70 ? "passed" : "review_required",
        top_issues: (data.issues_detected || [])
          .sort((a, b) => ({ high: 0, medium: 1, low: 2 }[a.severity] - { high: 0, medium: 1, low: 2 }[b.severity]))
          .slice(0, 3)
          .map(i => ({ field: i.field, severity: i.severity, message: i.issue })),
      });
      setResultKey((k) => k + 1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      {!apiKey && (
        <div className="mb-5 flex items-center gap-3 px-4 py-3 rounded-md bg-amber-50 border border-amber-200">
          <svg className="w-4 h-4 text-amber-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <span className="text-sm text-amber-700">
            API key required — enter your key in the top-right corner
          </span>
        </div>
      )}

      <PatientRecordForm onSubmit={handleSubmit} loading={loading} />

      {loading && <SkeletonLoader />}

      {error && !loading && (
        <div className="mt-4 flex items-start gap-3 px-4 py-3 bg-white border-l-4 border-red-500 rounded-md" style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4m0 4h.01" />
          </svg>
          <span className="text-sm text-gray-700 flex-1">{error}</span>
          <button type="button" onClick={() => setError(null)} className="text-sm text-gray-400 hover:text-gray-600">Dismiss</button>
        </div>
      )}

      {result && !loading && (
        <div className="mt-6 space-y-4">
          <QualityScoreCard key={resultKey} data={result} />
          <ApproveRejectBar
            status={status}
            onApprove={() => approve(result)}
            onReject={() => reject(result)}
          />
        </div>
      )}
    </div>
  );
}
