import { useEffect, useState } from "react";

const SIZE = 72;
const STROKE = 6;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const CX = SIZE / 2;
const CY = SIZE / 2;

function getColor(score) {
  if (score >= 0.75) return "#059669";
  if (score >= 0.5) return "#D97706";
  return "#DC2626";
}

export default function ConfidenceRing({ score }) {
  const pct = Math.max(0, Math.min(1, score ?? 0));
  const [animPct, setAnimPct] = useState(0);
  const color = getColor(pct);
  const label = Math.round(pct * 100) + "%";

  useEffect(() => {
    const t = setTimeout(() => setAnimPct(pct), 50);
    return () => clearTimeout(t);
  }, [pct]);

  const offset = CIRCUMFERENCE * (1 - animPct);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        {/* Background track — full circle */}
        <circle cx={CX} cy={CY} r={RADIUS} fill="none" stroke="#e2e8f0" strokeWidth={STROKE} />
        {/* Progress arc — starts at top (rotate -90 around center) */}
        <circle
          cx={CX}
          cy={CY}
          r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${CX} ${CY})`}
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
        {/* Centered text — always upright */}
        <text
          x={CX}
          y={CY}
          dominantBaseline="middle"
          textAnchor="middle"
          fill={color}
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="14"
          fontWeight="600"
        >
          {label}
        </text>
      </svg>
      <span className="uppercase tracking-widest text-gray-400" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
        Confidence
      </span>
    </div>
  );
}
