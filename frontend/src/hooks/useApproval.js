import { useState, useCallback, useEffect } from "react";
import { supabase } from "../lib/supabase";

export default function useApproval(recordId, patientName, page, payload, resultId) {
  const [status, setStatus] = useState(null); // null | "approved" | "rejected"

  useEffect(() => {
    setStatus(null);
  }, [resultId]);

  const approve = useCallback(async () => {
    setStatus("approved");
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "approved", page, payload });
    } catch (err) {
      console.error("Supabase insert error (approve):", err);
    }
  }, [recordId, patientName, page, payload]);

  const reject = useCallback(async () => {
    setStatus("rejected");
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "rejected", page, payload });
    } catch (err) {
      console.error("Supabase insert error (reject):", err);
    }
  }, [recordId, patientName, page, payload]);

  const reset = useCallback(() => setStatus(null), []);

  return { status, approve, reject, reset };
}
