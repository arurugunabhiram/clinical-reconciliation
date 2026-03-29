export default function InputModeToggle({ mode, onChange }) {
  return (
    <div className="inline-flex bg-gray-100 rounded-full p-1">
      {["form", "json"].map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          className={`px-3 py-1 rounded-full text-sm font-medium cursor-pointer transition-all duration-150 ${
            mode === opt
              ? "bg-white shadow-sm text-gray-900"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          {opt === "form" ? "Form Input" : "JSON Input"}
        </button>
      ))}
    </div>
  );
}
