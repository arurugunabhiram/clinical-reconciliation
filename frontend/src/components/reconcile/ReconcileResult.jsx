import { useState } from "react";
import ConfidenceBadge from "../shared/ConfidenceBadge";
import useApproval from "../../hooks/useApproval";

const safetyColors = {
  PASSED: "bg-green-100 text-green-800 border-green-300",
  WARNING: "bg-yellow-100 text-yellow-800 border-yellow-300",
  FAILED: "bg-red-100 text-red-800 border-red-300",
};

export default function ReconcileResult({ data }) {
  const { result, patient_id, source_count, llm_used } = data;
  const { status, approve, reject } = useApproval();
  const [copied, setCopied] = useState(false);

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-6 bg-white rounded-lg shadow border border-gray-200 divide-y divide-gray-100">
      {/* Header */}
      <div className="px-6 py-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {result.reconciled_medication}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Patient {patient_id} &middot; {source_count} sources compared
            {llm_used && (
              <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-purple-100 text-purple-700">
                LLM
              </span>
            )}
          </p>
        </div>
        <ConfidenceBadge score={result.confidence_score} />
      </div>

      {/* Confidence bar */}
      <div className="px-6 py-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Confidence</span>
          <span>{Math.round(result.confidence_score * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              result.confidence_score >= 0.75
                ? "bg-green-500"
                : result.confidence_score >= 0.5
                ? "bg-yellow-500"
                : "bg-red-500"
            }`}
            style={{ width: `${result.confidence_score * 100}%` }}
          />
        </div>
      </div>

      {/* Safety check */}
      <div className="px-6 py-3">
        <span className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium border ${safetyColors[result.clinical_safety_check] || ""}`}>
          Safety: {result.clinical_safety_check}
        </span>
      </div>

      {/* Reasoning */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-700 mb-1">Reasoning</h4>
        <p className="text-sm text-gray-600 leading-relaxed">{result.reasoning}</p>
      </div>

      {/* Recommended actions */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended Actions</h4>
        <ul className="list-disc list-inside space-y-1">
          {result.recommended_actions.map((action, i) => (
            <li key={i} className="text-sm text-gray-600">{action}</li>
          ))}
        </ul>
      </div>

      {/* Copy JSON */}
      <div className="px-6 py-3 flex justify-end">
        <button
          onClick={copyJson}
          className="px-3 py-1.5 text-xs font-medium rounded-md border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          {copied ? "Copied!" : "Copy JSON"}
        </button>
      </div>

      {/* Approve / Reject */}
      <div className="px-6 py-4">
        {status === null ? (
          <div className="flex gap-3">
            <button
              onClick={() => approve(result)}
              className="flex-1 bg-green-600 text-white py-2 rounded-md font-medium hover:bg-green-700 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => reject(result)}
              className="flex-1 bg-red-600 text-white py-2 rounded-md font-medium hover:bg-red-700 transition-colors"
            >
              Reject
            </button>
          </div>
        ) : (
          <div
            className={`text-center py-2 rounded-md font-medium ${
              status === "approved"
                ? "bg-green-50 text-green-700 border border-green-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {status === "approved" ? "Approved" : "Rejected"}
          </div>
        )}
      </div>
    </div>
  );
}
