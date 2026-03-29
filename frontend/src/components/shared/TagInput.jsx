import { useState, useRef } from "react";

export default function TagInput({ value = [], onChange, placeholder }) {
  const [input, setInput] = useState("");
  const inputRef = useRef(null);

  function addTag(raw) {
    const tag = raw.trim().replace(/,$/, "").trim();
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setInput("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(input);
    } else if (e.key === "Backspace" && input === "" && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  }

  function removeTag(idx) {
    onChange(value.filter((_, i) => i !== idx));
  }

  return (
    <div
      className="flex flex-wrap gap-1.5 items-center min-h-[38px] border border-gray-300 rounded-md px-2 py-1.5 bg-white cursor-text focus-within:ring-2 focus-within:ring-teal-600/20 focus-within:border-teal-600"
      onClick={() => inputRef.current?.focus()}
    >
      {value.map((tag, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 bg-gray-100 text-gray-700 rounded-full px-3 py-0.5"
          style={{ fontSize: "13px" }}
        >
          {tag}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); removeTag(i); }}
            className="text-gray-400 hover:text-gray-600 leading-none"
            aria-label={`Remove ${tag}`}
          >
            ×
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => { if (input.trim()) addTag(input); }}
        placeholder={value.length === 0 ? placeholder : ""}
        className="flex-1 min-w-[120px] outline-none text-sm bg-transparent text-gray-700 placeholder-gray-400"
        style={{ fontSize: "14px" }}
      />
    </div>
  );
}
