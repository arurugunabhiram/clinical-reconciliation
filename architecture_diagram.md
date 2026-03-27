# Architecture Diagram

```
clinical-reconciliation/
│
├── .env.example                  # Root env template (ANTHROPIC_API_KEY, API_KEY)
├── .gitignore
├── README.md
├── docker-compose.yml            # Orchestrates backend + frontend containers
│
├── backend/                      # FastAPI (Python) — port 8000
│   ├── .env.example
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   ├── main.py                   # App entrypoint — mounts routes, CORS, middleware
│   │
│   ├── api/                      # HTTP layer
│   │   ├── middleware/
│   │   │   └── auth.py           # API key authentication middleware
│   │   └── routes/
│   │       ├── reconcile.py      # POST /api/reconcile — medication reconciliation
│   │       └── validate.py       # POST /api/validate  — patient data quality scoring
│   │
│   ├── core/                     # Business logic (deterministic-first)
│   │   ├── cache.py              # LRU cache (256 entries) for reconciliation results
│   │   ├── reconciler.py         # Rule-based reconciliation engine
│   │   └── quality_scorer.py     # 4-dimension quality scorer (deterministic fallback)
│   │
│   ├── llm/                      # LLM integration layer
│   │   ├── client.py             # Anthropic SDK client (Claude Sonnet)
│   │   ├── parser.py             # JSON extraction + validation from LLM responses
│   │   └── prompts.py            # System & user prompt templates
│   │
│   ├── schemas/                  # Pydantic request/response models
│   │   ├── reconcile.py          # MedicationSource, ReconcileRequest/Response
│   │   └── validate.py           # PatientRecord, ValidateRequest/Response
│   │
│   └── tests/                    # Pytest suite (34 tests)
│       ├── test_llm_parser.py    # Parser edge cases (fences, bad JSON, ranges)
│       ├── test_quality_scorer.py# Scoring rules, contraindications, vitals
│       └── test_reconciler.py    # Agreement, reliability, confidence, safety
│
├── frontend/                     # React + Tailwind CSS — port 3000 (prod) / 5173 (dev)
│   ├── .env.example
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf                # Production static file server config
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html                # SPA entry point
│   │
│   └── src/
│       ├── main.jsx              # React root — router setup
│       ├── App.jsx               # Route definitions (/ → Reconcile, /validate)
│       ├── index.css             # Tailwind base styles
│       │
│       ├── api/
│       │   └── client.js         # Fetch client — base URL + API key from env
│       │
│       ├── hooks/
│       │   └── useApproval.js    # Approve/Reject state management per result
│       │
│       ├── pages/
│       │   ├── ReconcilePage.jsx # Medication reconciliation workflow page
│       │   └── ValidatePage.jsx  # Patient record quality validation page
│       │
│       └── components/
│           ├── layout/
│           │   ├── Navbar.jsx        # Top navigation bar
│           │   └── PageShell.jsx     # Page wrapper with consistent layout
│           │
│           ├── reconcile/
│           │   ├── MedicationForm.jsx   # Dynamic multi-source medication input
│           │   └── ReconcileResult.jsx  # Result display + Approve/Reject buttons
│           │
│           ├── validate/
│           │   ├── PatientRecordForm.jsx # Patient record input form
│           │   └── QualityScoreCard.jsx  # 4-dimension score breakdown display
│           │
│           └── shared/
│               ├── ConfidenceBadge.jsx  # Color-coded confidence indicator
│               ├── IssueBadge.jsx       # Severity-tagged issue pill
│               ├── LoadingSpinner.jsx   # Loading state spinner
│               └── ScoreGauge.jsx       # Circular score visualization
│
└── test_data/
    └── examples.json             # 3 ready-to-use demo payloads for evaluators


========================== DATA FLOW ==========================

  ┌─────────────┐       HTTP/JSON        ┌──────────────────┐
  │   Frontend   │ ──────────────────────▶│    FastAPI App    │
  │  React SPA   │◀────────────────────── │   (main.py)      │
  └─────────────┘                        └────────┬─────────┘
                                                  │
                                       ┌──────────┴──────────┐
                                       │                     │
                                ┌──────▼──────┐      ┌───────▼──────┐
                                │  /reconcile │      │  /validate   │
                                └──────┬──────┘      └───────┬──────┘
                                       │                     │
                              ┌────────▼────────┐   ┌────────▼────────┐
                              │   Reconciler    │   │  Quality Scorer │
                              │  (rule-based)   │   │  (deterministic)│
                              └────────┬────────┘   └────────┬────────┘
                                       │                     │
                              ┌────────▼─────────────────────▼────────┐
                              │         Sources conflict?             │
                              │     or  LLM scoring requested?        │
                              └────────┬──────────────────────────────┘
                                       │ yes
                              ┌────────▼────────┐
                              │   LRU Cache     │──── hit? ──▶ return cached
                              └────────┬────────┘
                                       │ miss
                              ┌────────▼────────┐
                              │  LLM Client     │
                              │  (Claude Sonnet)│
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │  LLM Parser     │
                              │  (JSON extract   │
                              │   + validate)    │
                              └─────────────────┘
```
