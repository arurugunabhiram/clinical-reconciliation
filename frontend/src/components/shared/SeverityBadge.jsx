const SEVERITY_STYLES = {
  high: "bg-red-50 text-red-700 border border-red-200",
  medium: "bg-amber-50 text-amber-700 border border-amber-200",
  low: "bg-green-50 text-green-600 border border-green-200",
};

const SEVERITY_LABELS = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

export default function SeverityBadge({ severity }) {
  const key = (severity || "low").toLowerCase();
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full font-medium ${SEVERITY_STYLES[key] || SEVERITY_STYLES.low}`}
      style={{ fontSize: "11px" }}
    >
      {SEVERITY_LABELS[key] || severity}
    </span>
  );
}
