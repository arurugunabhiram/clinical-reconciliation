function colorClass(score) {
  if (score >= 75) return "bg-green-500";
  if (score >= 50) return "bg-yellow-500";
  return "bg-red-500";
}

function textColor(score) {
  if (score >= 75) return "text-green-700";
  if (score >= 50) return "text-yellow-700";
  return "text-red-700";
}

export default function ScoreGauge({ label, score, max = 100 }) {
  const pct = Math.round((score / max) * 100);
  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className={`font-semibold ${textColor(pct)}`}>{score}/{max}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all ${colorClass(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
