import { useEffect, useState } from "react";

function getBarColor(score) {
  if (score >= 70) return "#059669";
  if (score >= 40) return "#D97706";
  return "#DC2626";
}

export default function ScoreBar({ label, score, maxScore = 100 }) {
  const [width, setWidth] = useState(0);
  const pct = Math.round((score / maxScore) * 100);
  const color = getBarColor(score);

  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 50);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-gray-600" style={{ fontSize: "13px" }}>{label}</span>
        <span className="text-gray-900 font-medium" style={{ fontSize: "13px" }}>
          {score} / {maxScore}
        </span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
