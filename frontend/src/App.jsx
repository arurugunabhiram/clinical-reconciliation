import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import PageShell from "./components/layout/PageShell";
import ReconcilePage from "./pages/ReconcilePage";
import ValidatePage from "./pages/ValidatePage";

export default function App() {
  const [apiKey, setApiKey] = useState(import.meta.env.VITE_API_KEY || "");

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar apiKey={apiKey} setApiKey={setApiKey} />
      <PageShell>
        <Routes>
          <Route path="/reconcile" element={<ReconcilePage apiKey={apiKey} />} />
          <Route path="/validate" element={<ValidatePage apiKey={apiKey} />} />
          <Route path="*" element={<Navigate to="/reconcile" replace />} />
        </Routes>
      </PageShell>
    </div>
  );
}
