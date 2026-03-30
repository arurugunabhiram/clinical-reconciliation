# Architecture Diagram

```
clinical-reconciliation/
│
├── .env.example                  # Root env template (ANTHROPIC_API_KEY, API_KEY, PORT)
├── .gitignore
├── README.md
├── architecture_diagram.md
├── docker-compose.yml            # Orchestrates backend + frontend on a shared bridge network
│
├── backend/                      # FastAPI (Python 3.11) — port 8080
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── main.py                   # App entrypoint — CORS, exception handlers, router mount, /health
│   ├── config.py                 # Env var loading + startup validation (fails fast if keys missing)
│   │
│   ├── api/                      # HTTP layer
│   │   ├── __init__.py           # Mounts /api prefix
│   │   ├── middleware/
│   │   │   └── auth.py           # X-API-Key header check — 401 if missing or wrong
│   │   └── routes/
│   │       ├── reconcile.py      # POST /api/reconcile/medication
│   │       └── validate.py       # POST /api/validate/data-quality
│   │
│   ├── core/                     # Business logic (deterministic-first)
│   │   ├── cache.py              # SHA-256-keyed dict cache, 5-min TTL, max 256 entries
│   │   ├── reconciler.py         # Rule-based reconciliation (reliability + recency ranking,
│   │   │                         #   confidence calibration, safety checks, conflict detection)
│   │   └── quality_scorer.py     # 4-dimension deterministic scorer (completeness, accuracy,
│   │                             #   timeliness, clinical plausibility) — LLM fallback
│   │
│   ├── llm/                      # LLM integration layer
│   │   ├── client.py             # Anthropic AsyncAnthropic client (claude-sonnet-4-20250514)
│   │   │                         #   retry on 429: 1s → 2s → 4s, raises AIServiceError
│   │   ├── parser.py             # JSON extraction from LLM text (strips fences, validates schema)
│   │   └── prompts.py            # System + user prompt templates with clinical scoring rubrics
│   │
│   ├── schemas/                  # Pydantic v2 request/response models
│   │   ├── reconcile.py          # ReconcileRequest, ReconcileResponse
│   │   │                         #   (reconciled_medication, confidence_score, reasoning,
│   │   │                         #    sources_analyzed, conflicts_found, recommended_actions,
│   │   │                         #    clinical_safety_check)
│   │   └── validate.py           # PatientRecord, ValidateResponse
│   │                             #   (overall_score, breakdown, issues_detected)
│   │
│   └── tests/                    # Pytest suite — 34 tests
│       ├── test_auth.py          # Missing key, wrong key, valid key
│       ├── test_cache.py         # Cache hit/miss, TTL expiry, key isolation
│       ├── test_llm_client.py    # Retry logic, rate limit, connection error
│       ├── test_llm_parser.py    # Malformed JSON, markdown fences, missing keys
│       ├── test_quality_scorer.py# Scoring rules, impossible vitals, drug-disease checks
│       ├── test_reconcile.py     # Endpoint validation (missing sources, empty array)
│       ├── test_reconciler.py    # Reliability ranking, confidence calibration, safety flags
│       ├── test_routes.py        # Integration tests with mocked LLM responses
│       └── test_validate.py      # Endpoint validation, score range checks
│
├── frontend/                     # React 18 + Tailwind CSS — port 3000 (prod) / 5173 (dev)
│   ├── .env.example              # VITE_API_BASE_URL, VITE_API_KEY,
│   │                             # VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
│   ├── Dockerfile                # Vite build → nginx static server
│   ├── .dockerignore
│   ├── nginx.conf                # Serves /dist, proxies /api/* to backend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html                # SPA entry point
│   │
│   └── src/
│       ├── main.jsx              # React root — BrowserRouter setup
│       ├── App.jsx               # Route definitions (/ → /reconcile, /validate)
│       ├── index.css             # Tailwind base styles
│       │
│       ├── lib/
│       │   └── supabase.js       # Supabase client (createClient with noop fallback
│       │                         #   if env vars absent — prevents startup crash)
│       │
│       ├── api/
│       │   └── client.js         # Fetch wrapper — injects X-API-Key, formats errors
│       │
│       ├── hooks/
│       │   └── useApproval.js    # Approve/Reject state + Supabase insert to decisions table
│       │                         #   signature: useApproval(recordId, patientName, page, payload)
│       │
│       ├── pages/
│       │   ├── ReconcilePage.jsx # Medication reconciliation workflow
│       │   └── ValidatePage.jsx  # Patient record quality validation + approve/reject
│       │
│       └── components/
│           ├── layout/
│           │   ├── Navbar.jsx        # Logo, nav tabs (grid layout), Approved/Rejected pill
│           │   │                     # counters with clickable dropdowns (Supabase real-time),
│           │   │                     # clicking a row opens DecisionDetailModal, API key input
│           │   └── PageShell.jsx     # Page wrapper with consistent max-width layout
│           │
│           ├── reconcile/
│           │   ├── MedicationForm.jsx   # Dynamic multi-source medication input (form + JSON)
│           │   └── ReconcileResult.jsx  # Result card: confidence ring, reasoning, actions,
│           │                            # safety badge, Approve/Reject bar
│           │
│           ├── validate/
│           │   ├── PatientRecordForm.jsx # Patient record input (form + JSON mode)
│           │   └── QualityScoreCard.jsx  # Score ring, 4 dimension bars, issues table
│           │
│           └── shared/
│               ├── ApproveRejectBar.jsx      # Approve / Reject / Undo buttons
│               ├── ConfidenceRing.jsx        # Animated SVG ring (green ≥0.80, yellow 0.60–0.79,
│               │                             #   red <0.60)
│               ├── DecisionDetailModal.jsx   # Modal popup showing full decision payload;
│               │                             #   reconcile view (medication, confidence ring,
│               │                             #   reasoning, safety) or validate view (score,
│               │                             #   top issues, safety); closes on Escape/outside click
│               ├── InputModeToggle.jsx       # Form ↔ JSON input switcher
│               ├── JsonEditor.jsx            # Editable JSON textarea with syntax hint
│               ├── JsonViewer.jsx            # Read-only formatted JSON display
│               ├── OutputModeToggle.jsx      # Visual ↔ JSON output switcher
│               ├── ScoreBar.jsx              # Labelled progress bar for dimension scores
│               ├── SeverityBadge.jsx         # high (red) / medium (amber) / low (green) pill
│               └── TagInput.jsx              # Chip-style multi-value text input
│
└── test_data/
    └── examples.json             # Ready-to-use demo payloads for evaluators


========================== DATA FLOW ==========================

  ┌──────────────────────────────────────────────────────────┐
  │                     React SPA (Frontend)                  │
  │  ReconcilePage          ValidatePage                      │
  │  MedicationForm         PatientRecordForm                 │
  │  ReconcileResult        QualityScoreCard                  │
  │  useApproval (w/ payload) ────────────────────────────▶ Supabase
  │  (decisions table)      Navbar (real-time counts,  ◀──── decisions
  │                          row click → DetailModal)
  └───────────────────┬─────────────────────────────────────┘
                      │  POST /api/reconcile/medication
                      │  POST /api/validate/data-quality
                      │  Header: X-API-Key
                      ▼
  ┌───────────────────────────────────────────────────────────┐
  │                   FastAPI Backend                          │
  │                                                            │
  │  Auth Middleware (verify_api_key)                          │
  │       │ 401 if missing/wrong key                           │
  │       ▼                                                    │
  │  ┌────────────────────┐   ┌────────────────────────┐      │
  │  │ /reconcile/        │   │ /validate/             │      │
  │  │  medication        │   │  data-quality          │      │
  │  └────────┬───────────┘   └───────────┬────────────┘      │
  │           │                           │                    │
  │           ▼                           ▼                    │
  │  ┌────────────────┐        ┌──────────────────────┐       │
  │  │  LRU Cache     │        │  LRU Cache           │       │
  │  │  (SHA-256 key) │        │  (SHA-256 key)       │       │
  │  └───┬───────┬────┘        └────┬────────┬────────┘       │
  │   hit│    miss│             hit │      miss│               │
  │      │       ▼                  │          ▼               │
  │      │  ┌──────────────┐        │  ┌─────────────────┐    │
  │      │  │  Reconciler  │        │  │  Quality Scorer │    │
  │      │  │ (rule-based) │        │  │ (deterministic) │    │
  │      │  └──────┬───────┘        │  └───────┬─────────┘    │
  │      │         │ sources        │          │ always try    │
  │      │         │ conflict?      │          │ LLM first     │
  │      │         ▼ yes            │          ▼               │
  │      │  ┌──────────────┐        │  ┌─────────────────┐    │
  │      │  │  LLM Client  │        │  │  LLM Client     │    │
  │      │  │  (Claude     │        │  │  (Claude        │    │
  │      │  │   Sonnet)    │        │  │   Sonnet)       │    │
  │      │  │  retry ×3    │        │  │  retry ×3       │    │
  │      │  └──────┬───────┘        │  └───────┬─────────┘    │
  │      │         │ LLM parse      │          │ LLM parse    │
  │      │         │ + fallback     │          │ + fallback   │
  │      │         ▼ to det.result  │          ▼ to det.result│
  │      │  sources_analyzed +      │  cache result           │
  │      │  conflicts_found stamped │                         │
  │      │  from request            │                         │
  │      │  cache result            │                         │
  │      │                          │                         │
  │      ▼                          ▼                         │
  │            JSON response to frontend                      │
  └───────────────────────────────────────────────────────────┘


======================== KEY DESIGN RULES ======================

  Deterministic-first:  Rule engine runs before every LLM call.
                        LLM only called when sources conflict (reconcile)
                        or as primary scorer (validate, with det. fallback).

  Cache-before-LLM:     Cache is checked before any computation.
                        Hit → return immediately, no LLM cost.

  LLM failure is safe:  AIServiceError / LLMParseError → fall back to
                        deterministic result, never a 500 to the client
                        (unless det. also fails).

  sources_analyzed /    Always stamped from the request body in the route
  conflicts_found:      handler — correct for both LLM and det. paths.

  Auth is middleware:   verify_api_key runs before every route handler
                        via FastAPI Depends — no per-route repetition.
```
