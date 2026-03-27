import { useState } from "react";
import ScoreGauge from "../shared/ScoreGauge";
import IssueBadge from "../shared/IssueBadge";

function overallColor(score) {
  if (score >= 75) return "text-green-700 bg-green-50 border-green-200";
  if (score >= 50) return "text-yellow-700 bg-yellow-50 border-yellow-200";
  return "text-red-700 bg-red-50 border-red-200";
}

export default function QualityScoreCard({ data }) {
  const { quality, patient_id, llm_used } = data;
  const { overall_score, breakdown, issues_detected, grade } = quality;
  const [copied, setCopied] = useState(false);

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-6 bg-white rounded-lg shadow border border-gray-200 divide-y divide-gray-100">
      {/* Overall score header */}
      <div className="px-6 py-5 flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-1">
            Patient {patient_id || "N/A"}
            {llm_used && (
              <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-purple-100 text-purple-700">
                LLM
              </span>
            )}
          </p>
          <h3 className="text-lg font-semibold text-gray-900">Data Quality Report</h3>
        </div>
        <div className={`flex flex-col items-center px-4 py-2 rounded-lg border ${overallColor(overall_score)}`}>
          <span className="text-3xl font-bold">{overall_score}</span>
          <span className="text-xs font-medium">Grade {grade}</span>
        </div>
      </div>

      {/* Breakdown gauges */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Score Breakdown</h4>
        <ScoreGauge label="Completeness" score={breakdown.completeness} />
        <ScoreGauge label="Accuracy" score={breakdown.accuracy} />
        <ScoreGauge label="Timeliness" score={breakdown.timeliness} />
        <ScoreGauge label="Clinical Plausibility" score={breakdown.clinical_plausibility} />
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

      {/* Issues */}
      {issues_detected.length > 0 && (
        <div className="px-6 py-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Issues Detected ({issues_detected.length})
          </h4>
          <div className="space-y-2">
            {issues_detected.map((issue, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <IssueBadge severity={issue.severity} />
                <div>
                  <span className="font-medium text-gray-800">{issue.field}</span>
                  <span className="text-gray-500 mx-1">&mdash;</span>
                  <span className="text-gray-600">{issue.issue}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
