---
title: GraphShield
emoji: 🔐
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---


# 🛡️ GraphShield AI — Multi-Domain Bias Detection & Fairness Platform

<div align="center">

![GraphShield](https://img.shields.io/badge/GraphShield_AI-Live-00cfff?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js_14-Frontend-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-Primary_LLM-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge)
![Fairlearn](https://img.shields.io/badge/Fairlearn-Metrics-6A0DAD?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A unified, production-grade platform for auditing AI bias across 5 modalities — structured datasets, trained ML models, unstructured documents, graph networks, and graph-based ML models.**

</div>

---

## 🌐 What is GraphShield AI?

GraphShield AI is an **enterprise-grade bias detection and fairness audit system** that covers every stage of the AI lifecycle. It provides 5 distinct audit pipelines under one platform — something no other tool offers.

Whether you're a data scientist validating models before deployment, a compliance officer generating audit trails for EU AI Act requirements, or a researcher studying structural bias in social networks, GraphShield gives you the tooling to **detect, explain, and remediate** bias at scale.

---

## ✨ Key Features

### 🔥 What Sets Us Apart

| Feature | GraphShield AI | Typical Bias Tools |
|---------|---------------|-------------------|
| Audit Modalities | **5** (Document + Tabular + ML Model + Graph Structure + Graph Model) | 1–2 |
| LLM Intelligence | **Gemini + Groq dual-provider** with auto-fallback | Single provider or none |
| AI Chat Assistant | **Conversational Q&A** about audit results via Gemini | ❌ |
| Try Demo Mode | **One-click demo** on every audit page — no uploads needed | ❌ |
| Graph Fairness | **Structural + predictive** bias in network topologies | ❌ |
| PDF Export | **One-click professional reports** | Limited |
| Real-time Analytics | **Live dashboard** with historical trends | ❌ |

---

### 📄 Module 1 — Document Bias Audit
- LLM-powered bias profiling using Gemini/Groq with spaCy NER
- Detects explicit and implicit bias across demographic groups
- Per-group intensity scoring (0–1) with text evidence

### 🗃️ Module 2 — Structured Dataset Audit
- Multi-format ingestion (CSV, JSON, SQL, XLSX)
- Groq LLaMA 3.3-70B column classification (Target/Sensitive/Proxy/Safe)
- EEOC-compliant fairness metrics (Disparate Impact, Statistical Parity)
- AI-generated explainability report with recommendations

### 🤖 Module 3 — ML Model Bias Audit
- Universal model support (sklearn, TensorFlow, PyTorch, ONNX)
- Shadow model fallback on load failures
- SHAP explainability + counterfactual analysis
- Bias scorecard with governance-ready remediation plan

### 🔗 Module 4 — Graph Structural Audit
- Multi-format graph ingestion (GML, CSV, JSON-LD)
- Structural metrics: homophily, degree disparity, PageRank disparity
- NetworkX-based topological bias detection

### 🕸️ Module 5 — Graph Model Pipeline
- End-to-end graph fairness via Fairlearn
- Universal metrics: Demographic Parity, Equalized Odds, Disparate Impact
- Structural metrics: Clustering disparity, prediction-centrality correlation
- Gemini AI narrative report with regulatory context

### 🧭 Cross-Module Capabilities
- **AI Chat Assistant** — Ask questions about your audit results in natural language (Gemini-powered)
- **Live Demo Mode** — Pre-loaded bias datasets on every audit page for instant demonstrations
- **Unified Audit Trail** — All audits persisted to SQLite with full history
- **Analytics Dashboard** — Real-time fairness trends, audit volume, status distribution
- **PDF Export** — Professional HTML reports on every results page
- **Splash Screen** — Animated landing with Lottie animation
- **Dual LLM Provider** — Gemini-first with automatic Groq fallback on rate limits

---

## 🚀 Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | Async REST API with Pydantic v2 |
| **Google Gemini 2.0 Flash** | Primary LLM — chat assistant, graph reports, explanations |
| **Groq LLaMA 3.3-70B** | Fallback LLM — column classification, bias narratives |
| **Fairlearn** | Demographic parity, equalized odds, disparate impact |
| **SHAP** | Model-agnostic feature importance |
| **spaCy** | Named entity recognition for document audit |
| **NetworkX** | Graph loading + structural metric computation |
| **SQLite (WAL)** | Persistent storage — datasets, audits, models |
| **scikit-learn** | Shadow model fallback, preprocessing |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Next.js 14** | React-based frontend with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Custom design system |
| **Framer Motion** | Animations + splash screen |
| **Lottie React** | Splash screen animation |
| **Zustand** | Client-side state management |
| **Recharts** | Fairness visualisation charts |
| **React Flow** | Graph network visualization |

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Groq API key](https://console.groq.com)
- [Google AI Studio key](https://aistudio.google.com) (Gemini)

### Docker (Recommended)

```bash
git clone https://github.com/fjiolla/GraphShield.git
cd GraphShield

docker build -t graphshield .
docker run -p 7860:7860 \
  -e GROQ_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  graphshield
```

### Local Development

**Backend:**
```bash
cd GraphShield
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Create .env with GROQ_API_KEY and GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd GraphShield/frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`, backend on `http://localhost:8000`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/audit/ingest` | Document bias audit (PDF/DOCX/TXT) |
| `POST` | `/api/v1/struct-audit/upload` | Upload dataset to vault |
| `POST` | `/api/v1/struct-audit/run-audit` | Run fairness audit on dataset |
| `GET` | `/api/v1/struct-audit/report` | Get latest dataset audit report |
| `POST` | `/api/v1/struct-model-audit/upload-and-audit` | ML model bias audit |
| `POST` | `/api/v1/graph-model-audit/analyze` | Graph model fairness pipeline |
| `POST` | `/api/v1/chat/ask` | AI Chat Assistant |
| `GET` | `/api/v1/demo/all` | Pre-computed demo results |
| `GET` | `/api/v1/demo-files/{type}` | Download demo files for Try Demo |
| `GET` | `/api/v1/export/report` | Export audit as HTML/PDF |
| `GET` | `/api/v1/system/audits` | Unified audit trail |
| `GET` | `/health` | Health check |

---

## 📊 Fairness Thresholds

| Metric | Threshold | Standard |
|--------|-----------|----------|
| Disparate Impact Ratio | < **0.8** → flagged | EEOC 4/5ths rule |
| Statistical Parity Difference | \|SPD\| > **0.1** → flagged | ±10% parity gap |
| Graph Fairness Score | < **60** → FAIL, 60–79 → WARN, ≥80 → PASS | Composite score |

---

## 🔐 Data Privacy

- All data stored locally in SQLite — nothing leaves your infrastructure
- Uploaded files deleted immediately after processing
- Only column profiles (not raw data) sent to LLMs for classification
- Audit trails contain results/metadata, not raw dataset content

---

## 📋 Regulatory Compliance

GraphShield AI helps organizations comply with:
- **EU AI Act** — Article 9 (risk management), Article 10 (data governance)
- **US EEOC Guidelines** — 4/5ths rule for disparate impact
- **India AI Regulations** — Constitutional Article 15 (prohibition of discrimination)

---

<div align="center">

**Every company deploying AI will legally need a tool like this. We built it.**

Built for the Google Solution Challenge 2025

[![GitHub](https://img.shields.io/badge/GitHub-GraphShield-181717?style=for-the-badge&logo=github)](https://github.com/fjiolla/GraphShield)

</div>
