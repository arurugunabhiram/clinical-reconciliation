import { useEffect } from "react";
import ConfidenceRing from "../shared/ConfidenceRing";
import SeverityBadge from "../shared/SeverityBadge";

function SafetyBadge({ value }) {
  const passed = value === "PASSED" || value === "passed";
  return passed ? (
    <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-green-50 border border-green-200 text-green-700 font-medium" style={{ fontSize: "14px" }}>
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
      Passed
    </span>
  ) : (
    <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 font-medium" style={{ fontSize: "14px" }}>
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
      Review Required
    </span>
  );
}

function PagePill({ page }) {
  const isTeal = page === "reconcile";
  return (
    <span
      className="inline-block px-2 py-0.5 rounded-full font-medium"
      style={{
        fontSize: "11px",
        backgroundColor: isTeal ? "#f0fdfa" : "#f5f3ff",
        color: isTeal ? "#0d9488" : "#7c3aed",
        border: `1px solid ${isTeal ? "#99f6e4" : "#ddd6fe"}`,
      }}
    >
      {page}
    </span>
  );
}

function ReconcileDetail({ payload }) {
  return (
    <div className="space-y-5">
      {/* Reconciled medication pill */}
      <div>
        <p className="font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
          Reconciled Medication
        </p>
        <span
          className="inline-block px-4 py-2 rounded-md text-white font-semibold"
          style={{ backgroundColor: "#0d9488", fontSize: "14px" }}
        >
          {payload.reconciled_medication || "—"}
        </span>
      </div>

      {/* Confidence ring */}
      <div className="flex items-center gap-4">
        <ConfidenceRing score={payload.confidence ?? 0} />
      </div>

      {/* Clinical reasoning */}
      <div>
        <p className="font-semibold uppercase tracking-widest mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em", color: "#0d9488" }}>
          Clinical Reasoning
        </p>
        <div
          className="bg-white rounded-md px-4 py-3 border border-gray-100"
          style={{ borderLeft: "3px solid #99f6e4", lineHeight: "1.7", fontSize: "14px", color: "#334155" }}
        >
          {payload.clinical_reasoning || "No reasoning provided."}
        </div>
      </div>

      {/* Safety status */}
      <div>
        <p className="font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
          Safety Status
        </p>
        <SafetyBadge value={payload.safety_status} />
      </div>
    </div>
  );
}

function getScoreColor(score) {
  if (score >= 70) return "#059669";
  if (score >= 40) return "#D97706";
  return "#DC2626";
}

function getScoreLabel(score) {
  if (score >= 70) return "Good";
  if (score >= 40) return "Fair";
  return "Poor";
}

function ValidateDetail({ payload }) {
  const score = payload.overall_score ?? 0;
  const color = getScoreColor(score);
  const label = payload.quality_grade || getScoreLabel(score);
  const issues = payload.top_issues || [];

  return (
    <div className="space-y-5">
      {/* Overall score */}
      <div className="flex items-center gap-4">
        <span className="font-bold" style={{ fontSize: "48px", color, lineHeight: 1 }}>{score}</span>
        <div>
          <p className="text-gray-500" style={{ fontSize: "13px" }}>Overall Quality Score</p>
          <span
            className="inline-block px-2 py-0.5 rounded-full font-medium mt-1"
            style={{
              fontSize: "12px",
              backgroundColor: score >= 70 ? "#ECFDF5" : score >= 40 ? "#FFFBEB" : "#FEF2F2",
              color,
              border: `1px solid ${score >= 70 ? "#A7F3D0" : score >= 40 ? "#FDE68A" : "#FECACA"}`,
            }}
          >
            {label}
          </span>
        </div>
      </div>

      {/* Top issues */}
      <div>
        <p className="font-semibold uppercase tracking-widest mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em", color: "#7c3aed" }}>
          Top Issues
        </p>
        {issues.length === 0 ? (
          <p className="text-gray-400" style={{ fontSize: "14px" }}>No issues recorded.</p>
        ) : (
          <div className="space-y-2">
            {issues.map((issue, i) => {
              const borderColor = issue.severity === "high" ? "#DC2626" : issue.severity === "medium" ? "#D97706" : "#059669";
              return (
                <div
                  key={i}
                  className="bg-white rounded-md border border-gray-200 p-3"
                  style={{ borderLeft: `3px solid ${borderColor}`, boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-gray-500" style={{ fontSize: "13px" }}>{issue.field}</span>
                    <SeverityBadge severity={issue.severity} />
                  </div>
                  <p className="text-gray-700" style={{ fontSize: "14px" }}>{issue.message}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Safety status */}
      <div>
        <p className="font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
          Safety Status
        </p>
        <SafetyBadge value={payload.safety_status} />
      </div>
    </div>
  );
}

export default function DecisionDetailModal({ record, onClose }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.35)" }}
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-lg bg-white rounded-lg border border-gray-200 shadow-xl"
        style={{ maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-semibold text-gray-800 truncate" style={{ fontSize: "15px" }}>
              {record.patient_name || "Unknown Patient"}
            </span>
            <PagePill page={record.page} />
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            style={{ fontSize: "20px", lineHeight: 1 }}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5">
          {!record.payload ? (
            <p className="text-gray-400" style={{ fontSize: "14px" }}>No detail data saved for this record.</p>
          ) : record.page === "reconcile" ? (
            <ReconcileDetail payload={record.payload} />
          ) : (
            <ValidateDetail payload={record.payload} />
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-md bg-gray-100 text-gray-700 font-medium hover:bg-gray-200 transition-colors"
            style={{ fontSize: "14px" }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
