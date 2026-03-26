import { NavLink } from "react-router-dom";

const link = ({ isActive }) =>
  `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
    isActive
      ? "bg-indigo-600 text-white"
      : "text-gray-600 hover:bg-gray-200"
  }`;

export default function Navbar() {
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <span className="text-lg font-bold text-indigo-700">
          Clinical Reconciliation Engine
        </span>
        <div className="flex gap-2">
          <NavLink to="/reconcile" className={link}>
            Reconcile
          </NavLink>
          <NavLink to="/validate" className={link}>
            Validate
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
