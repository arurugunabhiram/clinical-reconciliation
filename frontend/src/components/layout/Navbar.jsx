import { useEffect } from "react";
import { NavLink } from "react-router-dom";

const LS_KEY = "clinical_api_key";

export default function Navbar({ apiKey, setApiKey }) {
  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) setApiKey(saved);
  }, [setApiKey]);

  function handleKeyChange(e) {
    const val = e.target.value;
    setApiKey(val);
    localStorage.setItem(LS_KEY, val);
  }

  return (
    <nav
      className="bg-white border-b"
      style={{ height: "56px", borderColor: "#e2e8f0", position: "relative" }}
    >
      <div className="max-w-[1100px] mx-auto px-6 h-full flex items-center justify-between">
        {/* Left: Logo */}
        <div className="flex items-center gap-2">
          <span
            className="bg-teal-600 rounded-sm"
            style={{ width: "8px", height: "8px", display: "inline-block" }}
          />
          <span className="font-semibold text-gray-900" style={{ fontSize: "15px" }}>
            ClinicalAI
          </span>
          <span
            className="bg-gray-200 mx-1"
            style={{ width: "1px", height: "18px", display: "inline-block" }}
          />
          <span className="text-gray-400 font-normal" style={{ fontSize: "13px" }}>
            Reconciliation Engine
          </span>
        </div>

        {/* Center: Nav tabs — absolute centered */}
        <div
          className="absolute left-1/2"
          style={{ transform: "translateX(-50%)", display: "flex", height: "56px" }}
        >
          <NavLink
            to="/reconcile"
            className={({ isActive }) =>
              `inline-flex items-center px-4 text-sm border-b-2 transition-colors ${
                isActive
                  ? "border-teal-600 text-teal-700 font-medium"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`
            }
            style={{ height: "56px" }}
          >
            Medication Reconciliation
          </NavLink>
          <NavLink
            to="/validate"
            className={({ isActive }) =>
              `inline-flex items-center px-4 text-sm border-b-2 transition-colors ${
                isActive
                  ? "border-teal-600 text-teal-700 font-medium"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`
            }
            style={{ height: "56px" }}
          >
            Data Quality Validation
          </NavLink>
        </div>

        {/* Right: API key input */}
        <div className="flex items-center gap-1.5">
          <svg
            className="text-gray-400"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <input
            type="password"
            placeholder="API Key"
            value={apiKey}
            onChange={handleKeyChange}
            className="border rounded-md text-gray-700 bg-white transition-colors"
            style={{
              width: "180px",
              height: "32px",
              fontSize: "13px",
              padding: "0 8px",
              borderColor: "#e2e8f0",
              outline: "none",
            }}
            aria-label="API Key"
          />
        </div>
      </div>
    </nav>
  );
}
