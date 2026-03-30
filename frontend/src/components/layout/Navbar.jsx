import { useEffect, useState, useRef, useCallback } from "react";
import { NavLink } from "react-router-dom";
import { supabase } from "../../lib/supabase";
import DecisionDetailModal from "../shared/DecisionDetailModal";

const LS_KEY = "clinical_api_key";

export default function Navbar({ apiKey, setApiKey }) {
  const [counts, setCounts] = useState({ approved: 0, rejected: 0 });
  const [openDropdown, setOpenDropdown] = useState(null); // 'approved' | 'rejected' | null
  const [rows, setRows] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [loadingRows, setLoadingRows] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) setApiKey(saved);
  }, [setApiKey]);

  const fetchCounts = useCallback(async () => {
    try {
      const [{ count: a }, { count: r }] = await Promise.all([
        supabase.from("decisions").select("*", { count: "exact", head: true }).eq("decision", "approved"),
        supabase.from("decisions").select("*", { count: "exact", head: true }).eq("decision", "rejected"),
      ]);
      setCounts({ approved: a ?? 0, rejected: r ?? 0 });
    } catch (_) {
      // supabase unavailable — keep showing 0
    }
  }, []);

  useEffect(() => {
    fetchCounts();
    let channel;
    try {
      channel = supabase
        .channel("decisions-changes")
        .on("postgres_changes", { event: "INSERT", schema: "public", table: "decisions" }, fetchCounts)
        .subscribe();
    } catch (_) {}
    return () => { if (channel) supabase.removeChannel(channel); };
  }, [fetchCounts]);

  useEffect(() => {
    if (!openDropdown) { setRows([]); return; }
    setLoadingRows(true);
    supabase
      .from("decisions")
      .select("id, patient_name, page, created_at, payload")
      .eq("decision", openDropdown)
      .order("created_at", { ascending: false })
      .limit(20)
      .then(({ data }) => setRows(data ?? []))
      .catch(() => setRows([]))
      .finally(() => setLoadingRows(false));
  }, [openDropdown]);

  useEffect(() => {
    if (!openDropdown) return;
    function handleOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpenDropdown(null);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [openDropdown]);

  function handleKeyChange(e) {
    const val = e.target.value;
    setApiKey(val);
    localStorage.setItem(LS_KEY, val);
  }

  function toggleDropdown(type) {
    setOpenDropdown((prev) => (prev === type ? null : type));
  }

  function formatTime(ts) {
    try {
      return new Date(ts).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch (_) { return "—"; }
  }

  return (
    <>
    <nav className="bg-white border-b" style={{ height: "56px", borderColor: "#e2e8f0", zIndex: 40 }}>
      <div className="max-w-[1100px] mx-auto px-6 h-full" style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center" }}>

        {/* Left: Logo */}
        <div className="flex items-center gap-2">
          <span className="bg-teal-600 rounded-sm" style={{ width: "8px", height: "8px", display: "inline-block" }} />
          <span className="font-semibold text-gray-900" style={{ fontSize: "15px" }}>ClinicalAI</span>
          <span className="bg-gray-200 mx-1" style={{ width: "1px", height: "18px", display: "inline-block" }} />
          <span className="text-gray-400 font-normal" style={{ fontSize: "13px" }}>Reconciliation Engine</span>
        </div>

        {/* Center: Nav tabs */}
        <div style={{ display: "flex", height: "56px", justifyContent: "center" }}>
          <NavLink to="/reconcile" className={({ isActive }) => `inline-flex items-center px-4 text-sm border-b-2 transition-colors ${isActive ? "border-teal-600 text-teal-700 font-medium" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"}`} style={{ height: "56px" }}>
            Medication Reconciliation
          </NavLink>
          <NavLink to="/validate" className={({ isActive }) => `inline-flex items-center px-4 text-sm border-b-2 transition-colors ${isActive ? "border-teal-600 text-teal-700 font-medium" : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"}`} style={{ height: "56px" }}>
            Data Quality Validation
          </NavLink>
        </div>

        {/* Right: Pills + API key */}
        <div className="flex items-center gap-2" style={{ justifyContent: "flex-end" }}>

          {/* Pills with dropdown anchor */}
          <div ref={dropdownRef} style={{ position: "relative", display: "flex", alignItems: "center", gap: "6px" }}>

            {/* Approved pill */}
            <button
              onClick={() => toggleDropdown("approved")}
              style={{ display: "flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 500, background: openDropdown === "approved" ? "#9FE1CB" : "#E1F5EE", color: "#085041", border: "0.5px solid #5DCAA5", cursor: "pointer", transition: "background 0.15s" }}
            >
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#0F6E56", display: "inline-block" }} />
              {counts.approved} Approved
            </button>

            {/* Rejected pill */}
            <button
              onClick={() => toggleDropdown("rejected")}
              style={{ display: "flex", alignItems: "center", gap: "5px", padding: "4px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 500, background: openDropdown === "rejected" ? "#CECBF6" : "#EEEDFE", color: "#3C3489", border: "0.5px solid #AFA9EC", cursor: "pointer", transition: "background 0.15s" }}
            >
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#534AB7", display: "inline-block" }} />
              {counts.rejected} Rejected
            </button>

            {/* Dropdown panel */}
            {openDropdown && (
              <div style={{ position: "absolute", top: "calc(100% + 8px)", right: 0, width: "260px", background: "#fff", border: "0.5px solid #e2e8f0", borderRadius: "10px", boxShadow: "0 4px 16px rgba(0,0,0,0.08)", zIndex: 50, overflow: "hidden" }}>
                <div style={{ padding: "10px 14px 8px", borderBottom: "0.5px solid #f1f5f9" }}>
                  <span style={{ fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: openDropdown === "approved" ? "#0F6E56" : "#534AB7" }}>
                    {openDropdown === "approved" ? "Approved Records" : "Rejected Records"}
                  </span>
                </div>
                {loadingRows ? (
                  <div style={{ padding: "16px 14px", fontSize: "13px", color: "#94a3b8", textAlign: "center" }}>Loading…</div>
                ) : rows.length === 0 ? (
                  <div style={{ padding: "16px 14px", fontSize: "13px", color: "#94a3b8", textAlign: "center" }}>No records yet</div>
                ) : (
                  <div style={{ maxHeight: "280px", overflowY: "auto" }}>
                    {rows.map((row, i) => (
                      <div key={i} onClick={() => { setSelectedRecord(row); setOpenDropdown(null); }} style={{ padding: "9px 14px", borderBottom: i < rows.length - 1 ? "0.5px solid #f1f5f9" : "none", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", cursor: "pointer" }} onMouseEnter={(e) => e.currentTarget.style.background = "#f8fafc"} onMouseLeave={(e) => e.currentTarget.style.background = ""}>
                        <div style={{ minWidth: 0 }}>
                          <p style={{ fontSize: "13px", fontWeight: 500, color: "#1e293b", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.patient_name || "Unknown"}</p>
                          <p style={{ fontSize: "11px", color: "#94a3b8", margin: "2px 0 0" }}>{formatTime(row.created_at)}</p>
                        </div>
                        <span style={{ flexShrink: 0, fontSize: "10px", padding: "2px 7px", borderRadius: "4px", background: row.page === "validate" ? "#E1F5EE" : "#EEEDFE", color: row.page === "validate" ? "#085041" : "#3C3489", fontWeight: 500 }}>
                          {row.page}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* API key input */}
          <div className="flex items-center gap-1.5">
            <svg className="text-gray-400" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <input
              type="password" placeholder="API Key" value={apiKey} onChange={handleKeyChange}
              className="border rounded-md text-gray-700 bg-white transition-colors"
              style={{ width: "180px", height: "32px", fontSize: "13px", padding: "0 8px", borderColor: "#e2e8f0", outline: "none" }}
              aria-label="API Key"
            />
          </div>
        </div>

      </div>
    </nav>
    {selectedRecord && (
      <DecisionDetailModal
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
      />
    )}
    </>
  );
}
