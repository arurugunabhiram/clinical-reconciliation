export default function ApproveRejectBar({ status, onApprove, onReject }) {
  if (status === "approved") {
    return (
      <div className="flex items-center gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-md">
        <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm text-green-700 font-medium flex-1">
          Suggestion approved — pending save to EHR
        </span>
      </div>
    );
  }

  if (status === "rejected") {
    return (
      <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 border border-gray-200 rounded-md">
        <span className="text-sm text-gray-600 flex-1">Suggestion rejected</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        onClick={onApprove}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-green-600 text-white font-medium text-sm hover:bg-green-700 transition-colors"
        aria-label="Approve suggestion"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
        Approve Suggestion
      </button>
      <button
        type="button"
        onClick={onReject}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-white text-gray-700 border border-gray-300 font-medium text-sm hover:bg-gray-50 transition-colors"
        aria-label="Reject suggestion"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
        Reject
      </button>
    </div>
  );
}
