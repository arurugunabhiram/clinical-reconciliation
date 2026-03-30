import { useState, useCallback, useEffect, useRef } from "react";
import { supabase } from "../lib/supabase";

export default function useApproval(recordId, patientName, page, payload, resultId) {
  const [status, setStatus] = useState(null); // null | "approved" | "rejected"

  // Keep a ref to the latest payload so approve/reject don't need it as a dep
  // and are never recreated just because the payload object changed.
  const payloadRef = useRef(payload);
  useEffect(() => {
    payloadRef.current = payload;
  }, [payload]);

  useEffect(() => {
    setStatus(null);
  }, [resultId]);

  const approve = useCallback(async () => {
    setStatus("approved");
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "approved", page, payload: payloadRef.current });
    } catch (err) {
      console.error("Supabase insert error (approve):", err);
    }
  }, [recordId, patientName, page]);

  const reject = useCallback(async () => {
    setStatus("rejected");
    try {
      await supabase
        .from("decisions")
        .insert({ record_id: recordId, patient_name: patientName, decision: "rejected", page, payload: payloadRef.current });
    } catch (err) {
      console.error("Supabase insert error (reject):", err);
    }
  }, [recordId, patientName, page]);

  const reset = useCallback(() => setStatus(null), []);

  return { status, approve, reject, reset };
}
