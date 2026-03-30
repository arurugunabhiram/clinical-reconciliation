import { useState, useEffect } from "react";
import useApproval from "../../hooks/useApproval";
import ConfidenceRing from "../shared/ConfidenceRing";
import OutputModeToggle from "../shared/OutputModeToggle";
import JsonViewer from "../shared/JsonViewer";
import ApproveRejectBar from "../shared/ApproveRejectBar";

function SafetyBadge({ value }) {
  const passed = value === "PASSED";
  const isReview = value === "REVIEW_REQUIRED";
  if (passed) {
    return (
      <span className="inline-flex items-center gap-2 px-4 py-3 rounded-lg bg-green-50 border border-green-200 text-green-700 font-medium" style={{ fontSize: "15px" }}>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Passed
      </span>
    );
  }
  if (isReview) {
    return (
      <span className="inline-flex items-center gap-2 px-4 py-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 font-medium" style={{ fontSize: "15px" }}>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        </svg>
        Review Required
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-700 font-medium" style={{ fontSize: "15px" }}>
      Action Required
    </span>
  );
}

export default function ReconcileResult({ data, resultId }) {
  const [outputMode, setOutputMode] = useState("visual");
  const [visible, setVisible] = useState(false);
  const recordId = data.reconciled_medication?.slice(0, 30);
  const patientName = data.reconciled_medication?.split(" ").slice(0, 3).join(" ");
  const reconcilePayload = {
    reconciled_medication: data.reconciled_medication,
    confidence: data.confidence_score,
    safety_status: data.clinical_safety_check,
    clinical_reasoning: data.reasoning,
    recommended_actions: data.recommended_actions,
  };
  const { status, approve, reject } = useApproval(recordId, patientName, "reconcile", reconcilePayload, resultId);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 30);
    return () => clearTimeout(t);
  }, []);

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
        {/* Result header strip */}
        <div className="px-5 py-4 border-b border-gray-100 flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="font-semibold uppercase tracking-widest text-gray-500 mb-2" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
              Reconciled Medication
            </p>
            <span
              className="inline-block px-4 py-2 rounded-md text-white font-semibold"
              style={{ backgroundColor: "#0d9488", fontSize: "15px" }}
            >
              {data.reconciled_medication || "—"}
            </span>
            <p className="mt-2 text-gray-400" style={{ fontSize: "12px" }}>
              AI-assisted reconciliation
            </p>
          </div>
          <ConfidenceRing score={data.confidence_score ?? 0} />
        </div>

        {/* Output mode toggle */}
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="font-semibold uppercase tracking-widest text-gray-400" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
            Results
          </span>
          <OutputModeToggle mode={outputMode} onChange={setOutputMode} />
        </div>

        <div className="p-5">
          {outputMode === "visual" ? (
            <div className="grid gap-6" style={{ gridTemplateColumns: "2fr 1fr" }}>
              {/* Left column */}
              <div className="space-y-6">
                {/* Clinical Reasoning */}
                <div>
                  <p className="font-semibold uppercase tracking-widest mb-3" style={{ fontSize: "11px", letterSpacing: "0.08em", color: "#0d9488" }}>
                    Clinical Reasoning
                  </p>
                  <div
                    className="bg-white rounded-md px-4 py-3 border border-gray-100"
                    style={{ borderLeft: "3px solid #99f6e4", lineHeight: "1.7", fontSize: "15px", color: "#334155" }}
                  >
                    {data.reasoning || "No reasoning provided."}
                  </div>
                </div>

                {/* Recommended Actions */}
                {data.recommended_actions && data.recommended_actions.length > 0 && (
                  <div>
                    <p className="font-semibold uppercase tracking-widest text-gray-500 mb-3" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                      Recommended Actions
                    </p>
                    <ol className="space-y-2">
                      {data.recommended_actions.map((action, i) => (
                        <li key={i} className="flex items-start gap-3">
                          <span
                            className="flex-shrink-0 inline-flex items-center justify-center rounded-full font-medium"
                            style={{
                              width: "20px",
                              height: "20px",
                              fontSize: "12px",
                              backgroundColor: "#f0fdfa",
                              color: "#0d9488",
                            }}
                          >
                            {i + 1}
                          </span>
                          <span className="text-gray-700" style={{ fontSize: "14px" }}>{action}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>

              {/* Right column */}
              <div className="space-y-4">
                <div
                  className="bg-white rounded-lg border border-gray-200 p-4"
                  style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}
                >
                  <p className="font-semibold uppercase tracking-widest text-gray-500 mb-3 text-center" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
                    Safety Status
                  </p>
                  <div className="flex justify-center">
                    <SafetyBadge value={data.clinical_safety_check} />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <JsonViewer data={data} />
          )}

          {/* Approve/Reject bar */}
          <div className="mt-6 pt-5 border-t border-gray-100">
            <ApproveRejectBar
              status={status}
              onApprove={() => approve(data)}
              onReject={() => reject(data)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
