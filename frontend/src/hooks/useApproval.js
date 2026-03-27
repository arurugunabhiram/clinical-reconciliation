import { useState, useCallback } from "react";

export default function useApproval() {
  const [status, setStatus] = useState(null); // null | "approved" | "rejected"

  const approve = useCallback((result) => {
    setStatus("approved");
    console.log("ACTION:", { action: "approved", result });
  }, []);

  const reject = useCallback((result) => {
    setStatus("rejected");
    console.log("ACTION:", { action: "rejected", result });
  }, []);

  const reset = useCallback(() => setStatus(null), []);

  return { status, approve, reject, reset };
}
