import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import PageShell from "./components/layout/PageShell";
import ReconcilePage from "./pages/ReconcilePage";
import ValidatePage from "./pages/ValidatePage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <PageShell>
        <Routes>
          <Route path="/reconcile" element={<ReconcilePage />} />
          <Route path="/validate" element={<ValidatePage />} />
          <Route path="*" element={<Navigate to="/reconcile" replace />} />
        </Routes>
      </PageShell>
    </div>
  );
}
