import { useState, useEffect } from "react";
import OutputModeToggle from "../shared/OutputModeToggle";
import JsonViewer from "../shared/JsonViewer";
import ScoreBar from "../shared/ScoreBar";
import SeverityBadge from "../shared/SeverityBadge";

const LARGE_SIZE = 96;
const LARGE_STROKE = 8;
const LARGE_RADIUS = (LARGE_SIZE - LARGE_STROKE) / 2;
const LARGE_CIRC = 2 * Math.PI * LARGE_RADIUS;

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

function ScoreRing({ score }) {
  const [animPct, setAnimPct] = useState(0);
  const pct = Math.max(0, Math.min(100, score));
  const color = getScoreColor(pct);
  const cx = LARGE_SIZE / 2;
  const cy = LARGE_SIZE / 2;

  useEffect(() => {
    const t = setTimeout(() => setAnimPct(pct), 50);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={LARGE_SIZE} height={LARGE_SIZE} viewBox={`0 0 ${LARGE_SIZE} ${LARGE_SIZE}`}>
        <circle cx={cx} cy={cy} r={LARGE_RADIUS} fill="none" stroke="#e2e8f0" strokeWidth={LARGE_STROKE} />
        <circle
          cx={cx} cy={cy} r={LARGE_RADIUS}
          fill="none" stroke={color} strokeWidth={LARGE_STROKE}
          strokeDasharray={LARGE_CIRC}
          strokeDashoffset={LARGE_CIRC * (1 - animPct / 100)}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text
          x={cx} y={cy}
          dominantBaseline="middle" textAnchor="middle"
          fill={color}
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="24"
          fontWeight="600"
        >
          {score}
        </text>
      </svg>
      <div className="text-center">
        <p className="text-gray-500" style={{ fontSize: "13px" }}>Overall Quality Score</p>
        <span
          className="inline-block px-2 py-0.5 rounded-full font-medium mt-1"
          style={{
            fontSize: "12px",
            backgroundColor: pct >= 70 ? "#ECFDF5" : pct >= 40 ? "#FFFBEB" : "#FEF2F2",
            color: getScoreColor(pct),
            border: `1px solid ${pct >= 70 ? "#A7F3D0" : pct >= 40 ? "#FDE68A" : "#FECACA"}`,
          }}
        >
          {getScoreLabel(pct)}
        </span>
      </div>
    </div>
  );
}

function sortIssues(issues) {
  const order = { high: 0, medium: 1, low: 2 };
  return [...issues].sort((a, b) => (order[a.severity] ?? 3) - (order[b.severity] ?? 3));
}

export default function QualityScoreCard({ data }) {
  const { overall_score, breakdown, issues_detected = [] } = data;
  const [outputMode, setOutputMode] = useState("visual");
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 30);
    return () => clearTimeout(t);
  }, []);

  const sorted = sortIssues(issues_detected);

  return (
    <div
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(12px)",
        transition: "opacity 200ms ease, transform 200ms ease",
      }}
    >
      <div
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)" }}
      >
        {/* Header */}
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="font-semibold uppercase tracking-widest text-gray-400" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
            Quality Assessment
          </span>
          <OutputModeToggle mode={outputMode} onChange={setOutputMode} />
        </div>

        <div className="p-5">
          {outputMode === "visual" ? (
            <div className="space-y-6">
              {/* Score hero + breakdown */}
              <div className="flex items-start gap-8">
                <ScoreRing score={overall_score ?? 0} />
                <div className="flex-1">
                  <div
                    className="bg-white rounded-lg border border-gray-200 p-4"
                    style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
                  >
                    <p className="font-semibold uppercase tracking-widest text-gray-500 mb-4" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Score Breakdown
                    </p>
                    <div className="space-y-4">
                      <ScoreBar label="Completeness" score={breakdown?.completeness ?? 0} />
                      <ScoreBar label="Accuracy" score={breakdown?.accuracy ?? 0} />
                      <ScoreBar label="Timeliness" score={breakdown?.timeliness ?? 0} />
                      <ScoreBar label="Clinical Plausibility" score={breakdown?.clinical_plausibility ?? 0} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Issues */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <p className="font-semibold uppercase tracking-widest text-gray-500" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                    Issues Detected
                  </p>
                  {sorted.length > 0 && (
                    <span
                      className="inline-flex items-center justify-center rounded-full bg-gray-100 text-gray-600 font-medium"
                      style={{ width: "20px", height: "20px", fontSize: "11px" }}
                    >
                      {sorted.length}
                    </span>
                  )}
                </div>

                {sorted.length === 0 ? (
                  <div className="flex items-center gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-lg">
                    <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm text-green-700">No issues detected — record meets quality standards</span>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {sorted.map((issue, i) => {
                      const borderColor = issue.severity === "high" ? "#DC2626" : issue.severity === "medium" ? "#D97706" : "#059669";
                      return (
                        <div
                          key={i}
                          className="bg-white rounded-md border border-gray-200 p-3"
                          style={{ borderLeft: `3px solid ${borderColor}`, boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-mono text-gray-500" style={{ fontSize: "13px" }}>
                              {issue.field}
                            </span>
                            <SeverityBadge severity={issue.severity} />
                          </div>
                          <p className="text-gray-700" style={{ fontSize: "14px" }}>{issue.issue}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <JsonViewer data={data} />
          )}
        </div>
      </div>
    </div>
  );
}
