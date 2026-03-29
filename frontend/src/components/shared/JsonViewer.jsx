import { useState } from "react";

function colorizeJson(jsonString) {
  return jsonString
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            // Key
            return `<span class="json-key">${match}</span>`;
          }
          // String value
          return `<span class="json-string">${match}</span>`;
        }
        if (/true|false|null/.test(match)) {
          return `<span class="json-bool">${match}</span>`;
        }
        // Number
        return `<span class="json-number">${match}</span>`;
      }
    );
}

export default function JsonViewer({ data }) {
  const [copied, setCopied] = useState(false);
  const jsonString = JSON.stringify(data, null, 2);
  const highlighted = colorizeJson(jsonString);

  function handleCopy() {
    navigator.clipboard.writeText(jsonString).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="relative rounded-md border border-gray-200 bg-gray-50 overflow-x-auto">
      <style>{`
        .json-key { color: #1e293b; font-weight: 500; }
        .json-string { color: #0d9488; }
        .json-number { color: #1D6FA4; }
        .json-bool { color: #7C3AED; }
      `}</style>
      <button
        type="button"
        onClick={handleCopy}
        className="absolute top-2 right-2 text-gray-400 hover:text-gray-700 bg-white border border-gray-200 rounded px-2 py-0.5 transition-colors"
        style={{ fontSize: "12px" }}
      >
        {copied ? "Copied!" : "Copy"}
      </button>
      <pre
        className="p-4 font-mono text-gray-700 overflow-x-auto"
        style={{ fontSize: "13px" }}
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  );
}
