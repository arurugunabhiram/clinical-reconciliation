import { useState, useCallback } from "react";
import { supabase } from "../lib/supabase";

export default function useApproval(recordId, patientName, page) {
  const [status, setStatus] = useState(null); // null | "approved" | "rejected"

  const approve = useCallback(async (result) => {
    setStatus("approved");
    console.log("ACTION:", { action: "approved", result });
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "approved", page });
    } catch (err) {
      console.error("Supabase insert error (approve):", err);
    }
  }, [recordId, patientName, page]);

  const reject = useCallback(async (result) => {
    setStatus("rejected");
    console.log("ACTION:", { action: "rejected", result });
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "rejected", page });
    } catch (err) {
      console.error("Supabase insert error (reject):", err);
    }
  }, [recordId, patientName, page]);

  const reset = useCallback(() => setStatus(null), []);

  return { status, approve, reject, reset };
}
