import { useState } from "react";

export default function JsonEditor({ value, onChange, placeholder, minHeight = 200 }) {
  const [formatError, setFormatError] = useState(null);

  function handleFormat() {
    try {
      const parsed = JSON.parse(value);
      onChange(JSON.stringify(parsed, null, 2));
      setFormatError(null);
    } catch {
      setFormatError("Invalid JSON");
      setTimeout(() => setFormatError(null), 2000);
    }
  }

  return (
    <div className="rounded-md border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-200">
        <span className="font-semibold text-gray-400 tracking-widest uppercase" style={{ fontSize: "11px", letterSpacing: "0.08em" }}>
          JSON
        </span>
        <button
          type="button"
          onClick={handleFormat}
          className="text-gray-500 hover:text-gray-800 hover:bg-gray-100 px-2 py-0.5 rounded transition-colors"
          style={{ fontSize: "12px" }}
        >
          Format
        </button>
      </div>
      <textarea
        value={value}
        onChange={(e) => { onChange(e.target.value); }}
        placeholder={placeholder}
        spellCheck={false}
        className="w-full font-mono bg-gray-50 p-3 resize-y outline-none text-gray-700 placeholder-gray-400"
        style={{ fontSize: "13px", minHeight: `${minHeight}px`, display: "block" }}
      />
      {formatError && (
        <p className="px-3 py-1 text-red-500 bg-red-50 border-t border-red-100" style={{ fontSize: "12px" }}>
          {formatError}
        </p>
      )}
    </div>
  );
}
