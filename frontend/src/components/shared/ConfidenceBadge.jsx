function badgeColor(score) {
  if (score >= 0.75) return "bg-green-100 text-green-800";
  if (score >= 0.5) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export default function ConfidenceBadge({ score }) {
  const pct = Math.round(score * 100);
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeColor(score)}`}>
      {pct}% confidence
    </span>
  );
}
