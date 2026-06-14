---
title: GraphShield
emoji: 🔐
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---


# 🛡️ GraphShield — Multi-Domain AI Fairness & Bias Audit Platform

<div align="center">

![GraphShield](https://img.shields.io/badge/GraphShield-Live-00cfff?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge)
![Fairlearn](https://img.shields.io/badge/Fairlearn-Metrics-6A0DAD?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A unified, production-grade platform for auditing AI bias across structured datasets, trained ML models, unstructured documents, and graph-based networks — all in one place.**

</div>

---

## 🌐 What is GraphShield?

GraphShield is a **multi-domain AI bias detection and fairness audit system** built for real-world ML pipelines. It provides a 4-module audit framework that covers every stage of the AI lifecycle — from raw data ingestion to model predictions to graph-structured networks to document text.

Whether you're a data scientist looking to validate your model before deployment, a compliance officer generating audit trails, or a researcher studying structural bias in social networks, GraphShield gives you the tooling to detect, explain, and remediate bias at scale.

---

## ✨ Features

### 🗃️ Module 1 — Structured Dataset Audit
- **Multi-Format Ingestion** — Accepts CSV, JSON, SQL (PostgreSQL → SQLite transpiled), and XLSX with MIME-based format detection and auto-encoding correction
- **Hybrid Column Intelligence** — Groq LLaMA 3.3-70B classifies every column as `Target`, `Sensitive`, `Proxy`, or `Safe` using semantic reasoning over sampled row profiles
- **EEOC-Compliant Fairness Metrics** — Computes Disparate Impact Ratio (DIR < 0.8) and Statistical Parity Difference (|SPD| > 0.1) across all sensitive × target column combinations on the full dataset
- **AI-Generated Explainability Report** — Groq synthesises an executive summary, per-column bias risk explanations, dataset-specific recommendations, and research-grounded citations (Mehrabi et al., 2021)
- **Looker Studio–Ready Output** — All reports export as structured JSON with `looker_studio_ready: true`

### 🤖 Module 2 — ML Model Bias Audit
- **Universal Model Support** — Loads scikit-learn (`.pkl`, `.joblib`), TensorFlow/Keras (`.h5`, `.keras`), PyTorch (`.pt`, `.pth`), and ONNX models via a unified `StructModelAdapter`
- **Shadow Model Fallback** — If a model fails to load (version mismatch, missing dependency), automatically trains a LogisticRegression shadow model to continue the audit without interruption
- **SHAP Explainability** — Model-agnostic black-box SHAP values via `shap.Explainer`, surfacing top 5 features by mean |SHAP| value
- **Counterfactual Analysis** — Iteratively perturbs numeric features ±10% to find the decision boundary and identify minimum-change scenarios that flip a prediction
- **GROQ AI Compliance Narrative** — Structured 5-section audit report (Verdict → Impact → Root Cause → Data vs. Model → Remediation) with exponential backoff retry and local fallback
- **Bias Scorecard & Governance** — Per-group fairness scores, overall fairness score (0–100), audit trail UUID, and a tiered remediation plan (HIGH/MEDIUM/LOW priority)

### 📄 Module 3 — Document Bias Analysis
- **LLM-Powered Bias Profiling** — Extracts explicit and implicit bias from uploaded text using Groq LLaMA 3.3-70B with spaCy NER pre-processing (`en_core_web_sm`)
- **Group-Level Granularity** — Identifies demographic groups (gender, ethnicity, age, profession, religion, etc.), assigns bias category, sentiment, intensity (0–1), and provides text evidence
- **Bias Intensity Scoring** — Per-group float score (0 = no bias, 1 = extreme bias) with document-level overall bias classification (Low / Medium / High)

### 🔗 Module 4 — Graph Network Bias Audit
- **Multi-Format Graph Ingestion** — Parses GML, CSV (nodes + edges), and JSON-LD graph formats
- **Structural Fairness Metrics** — Computes homophily ratio, degree disparity, PageRank disparity, and neighbourhood representation across protected attribute groups
- **Universal Fairness Metrics** — Demographic parity, equalized odds, disparate impact, and predictive parity via Fairlearn, normalised to 0–100 scores with PASS/WARN/FAIL status
- **Graph Explainability** — Global structural explanation of why bias manifests in the graph topology
- **Gemini AI Bias Report** — LLM-synthesised natural language report contextualised to the graph domain

### 🧭 Cross-Module Capabilities
- **Unified Audit Trail** — All audit runs (dataset, model, document) are persisted to SQLite with UUIDs, timestamps, and result JSON; queryable across the full history
- **Analytics Dashboard** — Aggregated view of all historical audits with bias status (Pass/Warn/Fail) and fairness scores
- **Fully Dockerised** — One-command deployment with `docker build` + `docker run`

---

## 🚀 Tech Stack

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | **FastAPI** | Async REST API with Pydantic v2 validation |
| LLM | **LLaMA 3.3-70B via Groq** | Column classification, bias narratives, report generation |
| LLM | **Gemini Pro (Google AI)** | Graph bias report generation |
| Fairness | **Fairlearn** | Demographic parity, equalized odds, disparate impact |
| Explainability | **SHAP** | Model-agnostic black-box feature importance |
| NLP | **spaCy `en_core_web_sm`** | Named entity recognition for document bias profiling |
| Storage | **SQLite (WAL mode)** | Local dataset vault, audit sessions, model audit trails |
| Data | **pandas + NumPy** | DataFrame manipulation, fairness metric computation |
| Graph | **NetworkX** | Graph loading, structural metric computation |
| ML | **scikit-learn** | Shadow model, label encoding, logistic regression fallback |
| Document Parsing | **PyMuPDF, python-docx, pytesseract** | Multi-format document ingestion |
| Runtime | **Python 3.10+ / uvicorn** | ASGI server |

### Frontend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | **Next.js** | React-based frontend with SSR |
| Language | **TypeScript** | Type-safe component development |
| Styling | **Tailwind CSS** | Utility-first dark theme UI |
| State | **Zustand stores** | Client-side audit state management |
| Charts | Recharts / custom components | Fairness metrics visualisation |

---

## 📂 Project Structure

```
GraphShield/
├── Dockerfile
├── requirements.txt
│
├── app/                              # FastAPI backend
│   ├── main.py                       # App entry point + CORS middleware
│   │
│   ├── api/v1/
│   │   ├── api.py                    # Router aggregation
│   │   └── endpoints/
│   │       ├── audit.py              # Document bias audit endpoint
│   │       ├── connections.py        # Health / connectivity
│   │       ├── graph_audit.py        # /analyze-bias — graph pipeline
│   │       ├── graph_model_audit.py  # Graph model audit endpoint
│   │       ├── model_audit.py        # General model audit
│   │       ├── struct_audit_api.py   # Module 1: /upload, /run-audit, /report
│   │       ├── struct_model_audit_api.py  # Module 2: /upload-and-audit
│   │       └── system.py             # /audits — unified audit trail
│   │
│   ├── core/
│   │   ├── config.py                 # App settings, API keys
│   │   ├── security.py               # Auth helpers
│   │   └── struct_local_config.py    # SQLite paths, Groq client factory
│   │
│   ├── graph_model/                  # Module 4: Graph bias pipeline
│   │   ├── pipeline.py               # Master 7-stage pipeline orchestrator
│   │   ├── csv_graph_parser.py       # CSV → NetworkX graph
│   │   ├── gml_parser.py             # GML → NetworkX graph
│   │   ├── jsonld_parser.py          # JSON-LD → NetworkX graph
│   │   ├── graph_validator.py        # Graph validation + protected attr check
│   │   ├── prediction_resolver.py    # Prediction source resolution
│   │   ├── universal_fairness.py     # Fairlearn fairness metrics
│   │   ├── structural_fairness.py    # Homophily, degree/PageRank disparity
│   │   ├── explainability.py         # Graph global explanation
│   │   ├── scorecard_builder.py      # Normalised 0–100 scorecard
│   │   ├── gemini_reporter.py        # Gemini AI narrative generation
│   │   ├── model_loader.py           # ML model loading for graph predictions
│   │   ├── audit_trail.py            # Run ID generation + audit record saving
│   │   └── constants.py              # Fairness thresholds, model extensions
│   │
│   ├── services/                     # Modules 1, 2 & 3 services
│   │   ├── struct_ingestion.py       # Module 1: Multi-format data ingestion
│   │   ├── struct_intelligence.py    # Module 1: Groq column classification
│   │   ├── struct_statistics.py      # Module 1: DIR + SPD fairness metrics
│   │   ├── struct_reporting.py       # Module 1: Groq explainability report
│   │   ├── struct_model_auditor.py   # Module 2: 11-step model audit pipeline
│   │   ├── struct_model_adapter.py   # Module 2: Universal model loader
│   │   ├── struct_explainability.py  # Module 2: SHAP + counterfactual + Groq narrative
│   │   ├── analysis.py               # Module 3: Document bias profiling (Groq + spaCy)
│   │   ├── extraction.py             # Module 3: Text extraction
│   │   ├── localextraction.py        # Module 3: Local file text extraction
│   │   ├── remediation.py            # Module 3: Remediation suggestions
│   │   └── vector_audit.py           # Vector / embedding audit utilities
│   │
│   ├── schemas/                      # Pydantic v2 models
│   │   └── struct_model_audit_schema.py
│   │
│   └── utils/                        # Shared utilities
│       ├── struct_bias_metrics.py    # Bias verdict, fairness score computation
│       ├── struct_format_utils.py    # MIME detection, encoding, sanitization
│       └── struct_sql_transpiler.py  # PostgreSQL → SQLite transpilation
│
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                      # Next.js App Router pages
│   │   ├── components/
│   │   │   ├── charts/               # Fairness metric visualisation charts
│   │   │   ├── fairness/             # Fairness result display components
│   │   │   ├── graph/                # Graph visualisation components
│   │   │   ├── layout/               # Navigation, sidebar, layout
│   │   │   └── ui/                   # Shared UI primitives
│   │   ├── stores/                   # Zustand state stores
│   │   ├── types/                    # TypeScript type definitions
│   │   └── utils/                    # Frontend utilities + API clients
│   ├── tailwind.config.ts
│   ├── next.config.mjs
│   └── package.json
│
└── audit_logs/                       # Persisted audit trail records
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com)
- A [Google AI Studio key](https://aistudio.google.com) (for graph module Gemini reports)

### Option A — Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/fjiolla/GraphShield.git
cd GraphShield

# Build the Docker image
docker build -t graphshield .

# Run the container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_groq_key_here \
  -e GEMINI_API_KEY=your_gemini_key_here \
  graphshield
```

The API will be available at `http://localhost:8000`.

---

### Option B — Local Development

#### Backend

```bash
# Clone the repository
git clone https://github.com/fjiolla/GraphShield.git
cd GraphShield

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set environment variables
cp .env.example .env
# Edit .env and add:
# GROQ_API_KEY=your_groq_key_here
# GEMINI_API_KEY=your_gemini_key_here

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd GraphShield/frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend runs on `http://localhost:3000` and expects the backend at `http://localhost:8000`.

---

## 🔁 How the Pipelines Work

### Module 1 — Structured Dataset Audit Pipeline

```
File Upload (CSV / JSON / SQL / XLSX)
        │
        ▼
Format Detection  ──  MIME + extension routing
(CSV → chardet encoding | JSON → flatten nested | SQL → transpile PostgreSQL → SQLite | XLSX → serial date handling)
        │
        ▼
SQLite Ingestion  ──  local_vault.db (WAL mode)
        │
        ▼
Hybrid Column Classification  ──  Groq LLaMA 3.3-70B
(Target | Sensitive | Proxy | Safe — per column with reasoning)
        │
        ▼
Fairness Metric Computation  ──  Full dataset (not sampled)
(DIR per group vs. privileged | SPD per group | Missing rate analysis)
        │
        ▼
Groq Explainability Report  ──  LLaMA 3.3-70B
(Executive summary | Column risk explanations | Specific recommendations | Research grounding)
        │
        ▼
Output: Looker Studio–ready JSON + Audit Session persisted to SQLite
```

### Module 2 — ML Model Bias Audit Pipeline

```
Model Upload (.pkl / .joblib / .h5 / .pt / .onnx) + Dataset Upload
        │
        ▼
Dataset Ingestion + Column Classification  ──  Reuses Module 1 pipeline
        │
        ▼
Model Loading  ──  StructModelAdapter
(Auto-detect format | Smoke test on 3 rows | Shadow LR fallback on failure)
        │
        ▼
Predictions  ──  Unified predict(X) interface across all frameworks
        │
        ├── Disparate Impact Ratio + Parity Gap per group
        ├── Bias Verdict  ──  FAIR / MARGINAL / BIASED (+ Confidence)
        ├── SHAP Values  ──  Black-box explainer (top 5 features)
        ├── Counterfactual  ──  ±10% perturbation, up to 20 iterations
        └── GROQ Narrative  ──  5-section compliance audit report
                │
                ▼
        Governance Output  ──  Fairness scorecard | Audit trail | Remediation plan
```

### Module 4 — Graph Bias Audit Pipeline

```
Graph Upload (GML / CSV nodes+edges / JSON-LD)
        │
        ▼
Stage 1: Load Graph  ──  NetworkX graph construction
Stage 2: Validate    ──  Protected attribute presence + structural checks
Stage 3: Predictions  ──  CSV predictions / ML model / column-based
        │
        ▼
Stage 4: Fairness Metrics
        ├── Universal (via Fairlearn):  Demographic Parity | Equalized Odds | Disparate Impact | Predictive Parity
        └── Structural:  Homophily ratio | Degree disparity | PageRank disparity | Neighbourhood representation
        │
        ▼
Stage 5: Explainability  ──  Global structural bias explanation
Stage 6: Scorecard  ──  Normalised 0–100 composite fairness score
Stage 7: Gemini Report  ──  Domain-contextualised AI narrative + Audit Trail
```

---

## 📡 API Endpoints

### Module 1 — Dataset Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/struct/upload` | Upload and ingest a dataset (CSV/JSON/SQL/XLSX) |
| `POST` | `/api/v1/struct/run-audit` | Run column classification + fairness audit + report |
| `GET`  | `/api/v1/struct/report` | Retrieve the latest audit report |
| `GET`  | `/api/v1/struct/tables` | List all ingested tables in the vault |

### Module 2 — Model Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/model/upload-and-audit` | Upload model + dataset, run full bias audit pipeline |

### Module 3 — Document Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/audit/document` | Upload a document and run LLM-powered bias profiling |

### Module 4 — Graph Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/graph/analyze-bias` | Upload graph file, run full graph bias pipeline |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/system/audits` | Retrieve unified audit trail (all modules) |
| `GET`  | `/health` | Health check |

---

## 📊 Scoring & Thresholds Explained

### Fairness Thresholds (EEOC-aligned)
| Metric | Threshold | Standard |
|--------|-----------|----------|
| Disparate Impact Ratio | DIR < **0.8** → flagged | EEOC 4/5ths rule |
| Statistical Parity Difference | \|SPD\| > **0.1** → flagged | ±10% parity gap |
| Minimum Group Size | < **10 rows** → unreliable warning | Statistical reliability |

### Model Bias Verdict
| Verdict | Condition | Confidence |
|---------|-----------|-----------|
| `FAIR` | All group DIRs ≥ 0.8 | HIGH / MEDIUM |
| `MARGINAL` | Any DIR between 0.7–0.8 | MEDIUM |
| `BIASED` | Any DIR < 0.8 (80% rule violated) | HIGH |

### Graph Fairness Score (0–100)
| Score Range | Status | Meaning |
|-------------|--------|---------|
| ≥ 80 | **PASS** | Within acceptable fairness bounds |
| 60–79 | **WARN** | Approaching bias thresholds |
| < 60 | **FAIL** | Significant fairness violation detected |

---

## 🔐 Data Privacy

GraphShield is designed for **local-first, privacy-preserving** operation:
- All ingested datasets are stored in a local SQLite database (`local_vault.db`) — no data leaves your infrastructure
- Uploaded model and dataset files are deleted from disk immediately after ingestion and auditing
- Only column profiles (dtype, unique count, 3 sample values) are sent to Groq for classification — not raw data rows
- Audit trails contain results and metadata, not raw dataset content

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request. For major changes, open a discussion first.

```bash
# Run the backend in development mode
uvicorn app.main:app --reload

# Run frontend in development mode
cd frontend && npm run dev
```

---

## 📝 License

This project is open source under the [MIT License](LICENSE).

---

<div align="center">

**⭐ If GraphShield helped you build fairer AI, give it a star!**

Built with ❤️ for responsible, auditable AI

[![GitHub](https://img.shields.io/badge/GitHub-GraphShield-181717?style=for-the-badge&logo=github)](https://github.com/fjiolla/GraphShield)
[![FastAPI Docs](https://img.shields.io/badge/API_Docs-Swagger_UI-009688?style=for-the-badge&logo=fastapi)](http://localhost:8000/docs)

</div>