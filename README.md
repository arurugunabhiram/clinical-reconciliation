# Clinical Reconciliation Platform

A full-stack application for AI-assisted medication reconciliation and patient data quality validation. Built with FastAPI (Python) and React + Tailwind CSS.

---

## How to Run Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in ANTHROPIC_API_KEY
uvicorn main:app --reload       # runs on http://localhost:8000
```

API docs available at http://localhost:8000/docs (Swagger UI).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # defaults point to localhost:8000
npm run dev                     # runs on http://localhost:5173
```

---

## Which LLM and Why

This project uses **Anthropic's Claude** (model: `claude-sonnet-4-20250514`) via the official `anthropic` Python SDK. Claude was chosen because it excels at following structured JSON output schemas reliably, which is critical when the response feeds directly into a clinical UI. Its strong instruction-following ability means the system prompts can enforce strict scoring rubrics and safety-check logic without frequent format violations. Additionally, Claude's large context window comfortably handles multi-source medication records and full patient records in a single call.

---

## Key Design Decisions

1. **Deterministic-first, LLM-second architecture** — The reconciler and quality scorer first attempt a rule-based evaluation. The LLM is only called when sources genuinely conflict (reconciliation) or as the primary path with a deterministic fallback (validation). This reduces cost, latency, and non-determinism for straightforward cases.

2. **Structured source schema over free-text** — The input schema uses explicit fields (`source_name`, `drug_name`, `dose`, `frequency`) rather than a single `medication` string as shown in the assessment PDF. This enables per-field validation, precise confidence calibration per dimension, and avoids brittle string parsing. The `test_data/examples.json` file contains ready-to-use payloads that match the actual API schema.

3. **JSON-only prompt contracts** — Both system prompts mandate raw JSON output with an exact schema. The parser (`llm/parser.py`) strips markdown fences and validates required keys before the response reaches the frontend, preventing malformed data from surfacing to clinicians.

4. **LRU caching for reconciliation** — An in-memory LRU cache (256 entries) keyed on a hash of the input sources avoids redundant LLM calls for repeated queries during the same session. This keeps demo usage fast without needing Redis or an external cache.

5. **Approve / Reject workflow on the frontend** — Reconciliation results include Approve and Reject buttons so a human clinician always has the final say. The `useApproval` hook tracks decision state per result, reinforcing the principle that the AI assists but does not autonomously act.

6. **Four-dimension quality scoring** — Data quality is broken into Completeness, Accuracy, Timeliness, and Clinical Plausibility (25% weight each). This gives reviewers a transparent breakdown rather than a single opaque number, and the prompt rubric ensures the LLM scores on the same scale every time.

---

## Prompt Engineering Approach

Each LLM call uses a **system prompt + user prompt** pair. The system prompt defines the AI's role, mandates JSON-only output, specifies the exact response schema, and provides a scoring rubric with concrete rules (e.g., "reduce confidence if data > 6 months old", "set clinical_safety_check to WARNING if contraindicated").

Clinical context is injected into the **user prompt** at call time. For reconciliation, the user prompt is built dynamically:

```
Medication sources:
  Source 1 (pharmacy, high reliability, 2024-12-01): Metformin 1000mg twice daily
  Source 2 (patient_report, low reliability, 2024-06-15): Metformin 500mg once daily

Patient context:
  Conditions: Type 2 Diabetes, CKD Stage 3
  Allergies: Sulfa drugs
  Recent labs: eGFR 38, HbA1c 7.2

Reconcile these records and respond with the JSON object only.
```

For validation, the full patient record JSON is embedded along with today's date (for timeliness scoring). The system prompt rubric tells the LLM exactly how to score each dimension and what severity levels to assign to detected issues.

This structure — fixed rubric in the system prompt, variable data in the user prompt — keeps scoring consistent across calls while allowing any patient record to be evaluated.

---

## What I'd Improve with More Time

- **Multi-worker cache coordination** — The in-memory LRU cache is per-process. Running `uvicorn` with `--workers N` gives each worker its own isolated cache, reducing hit rate proportionally. For production, replace with Redis using the same LRU interface.

1. **Persistent storage** — Add PostgreSQL to store reconciliation decisions, quality reports, and an audit trail of Approve/Reject actions with timestamps and user identity.

2. **Streaming responses** — Use Claude's streaming API and surface partial results in the UI so clinicians see output as it generates instead of waiting for the full response.

3. **Authentication & RBAC** — Replace the single API key with JWT-based auth, role-based access (pharmacist, nurse, admin), and per-user audit logging.

4. **Comprehensive test coverage** — Add integration tests that hit the API with mock LLM responses (`httpx` + `respx`), end-to-end Playwright tests for the frontend, and property-based tests for the deterministic scorer edge cases.

5. **Prompt evaluation pipeline** — Build a dataset of labeled medication conflicts and quality records, then run automated prompt regression tests to catch scoring drift when prompts are updated.

6. **Batch processing** — Support uploading a CSV/FHIR bundle of patient records and processing them in parallel with progress tracking and downloadable reports.

7. **Observability** — Add structured logging, request tracing (OpenTelemetry), and a Grafana dashboard for LLM latency, cache hit rate, and error rate.

---

## Estimated Time Spent

| Section          | Time     |
| ---------------- | -------- |
| Backend (API, LLM, scoring) | ~4 hours |
| Frontend (React, Tailwind)  | ~3 hours |
| Tests                       | ~1.5 hours |
| Docs & README               | ~1 hour  |
| Docker & DevOps             | ~0.5 hours |
| **Total**                   | **~10 hours** |

---

## Docker

```bash
cp .env.example .env  # fill in your keys
docker-compose up --build
# backend: http://localhost:8000/docs
# frontend: http://localhost:3000
```
