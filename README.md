# NEUROVOX-SME02 — IntelliQuote: AI Sales Decision Engine

> A production-grade, full-stack AI platform for intelligent RFP (Request for Proposal) processing. Built on a **multi-agent architecture** with RAG (Retrieval-Augmented Generation), real-time global sourcing analysis, dynamic geo-aware pricing, and professional PDF quotation generation — powered by **Google Gemini 2.0 Flash**.

---

## 🚀 Key Features

- **Multi-Agent Pipeline** — 6 specialized AI agents orchestrated by FastAPI (RFP Parser → Pricing → Competitor → Knowledge → Strategy → Sourcing → Drafting)
- **RAG Knowledge Base (SME01)** — FAISS-powered vector store with sentence-transformer embeddings for semantic product and pricing lookups
- **Decision Memory (SME02)** — Persistent case-based reasoning that learns from past quote outcomes to improve future recommendations
- **3 Pricing Strategies** — Aggressive, Balanced, Premium — computed in parallel and compared side-by-side
- **Global Sourcing Engine** — Evaluates manufacturer regions, import duties, lead times, and logistics costs across countries
- **Geo-Aware Pricing** — Auto-detects client country from RFP text; applies region-specific tax logic (GST for India, VAT, import duties for 50+ countries)
- **Multi-Currency Support** — Real-time currency conversion with live exchange rates for international quotes
- **Outcome Feedback Loop** — Win/loss tracking tied back to Decision Memory for continuous strategy refinement
- **PDF Quotation Generation** — Professional branded proposals via ReportLab
- **Dark Glassmorphism Dashboard** — React 18 + Vite frontend with animated sidebar, live pipeline visualization, and quote history

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.11+ · FastAPI 0.115 · Uvicorn (ASGI) |
| **AI / LLM** | Google Gemini 2.0 Flash (`google-generativeai`) |
| **Fallback LLM** | Meta LLaMA 3.3 70B via Groq API |
| **Vector DB** | FAISS CPU · `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **Data Processing** | pandas · pdfplumber · openpyxl · PyPDF2 |
| **PDF Generation** | ReportLab |
| **Validation** | Pydantic v2 |
| **Frontend** | React 18 · Vite 5 · React Router v6 |
| **UI Components** | Lucide React · Recharts |
| **Styling** | Vanilla CSS (Dark Glassmorphism Design System) |
| **API Client** | Native `fetch` with Vite proxy |

---

## 📂 Project Structure

```
intelliquote/
├── backend/
│   ├── agents/                        ← AI Agent modules
│   │   ├── rfp_parser.py              ← Extracts product, client, quantity, country from RFP text
│   │   ├── pricing_agent.py           ← Internal cost lookup + base price computation
│   │   ├── competitor_agent.py        ← Competitor price benchmarking
│   │   ├── knowledge_agent.py         ← RAG-powered knowledge retrieval (SME01)
│   │   ├── strategy_agent.py          ← LLM-driven strategic pricing decision (Aggressive/Balanced/Premium)
│   │   ├── sourcing_agent.py          ← Global sourcing analysis: regions, duties, lead times
│   │   └── drafting_agent.py          ← PDF quotation proposal generation
│   │
│   ├── rag/                           ← Retrieval-Augmented Generation stack
│   │   ├── embeddings.py              ← Sentence-transformer embedding generation
│   │   ├── ingestion.py               ← Document chunking & indexing pipeline
│   │   ├── vector_store.py            ← FAISS index build/load/save
│   │   ├── retriever.py               ← Semantic search over knowledge base
│   │   ├── conflict_detector.py       ← Detects contradictory info across sources
│   │   └── decision_memory.py         ← Case-based memory: save & recall past decisions (SME02)
│   │
│   ├── services/                      ← Business logic services
│   │   ├── currency_service.py        ← Multi-currency conversion (50+ currencies)
│   │   ├── tax_service.py             ← Region-specific tax rules (GST, VAT, duties)
│   │   ├── llm_service.py             ← Gemini / Groq LLM abstraction layer
│   │   └── feedback_service.py        ← Win/loss outcome tracking & statistics
│   │
│   ├── data/
│   │   └── documents/                 ← Knowledge base documents (PDF, XLSX, TXT)
│   ├── faiss_index/                   ← Auto-generated FAISS vector index (gitignored)
│   ├── outputs/                       ← Generated PDF proposals (gitignored)
│   ├── main.py                        ← FastAPI app + all API route orchestration
│   ├── models.py                      ← Pydantic data models (QuoteOutput, StrategiesComparison, etc.)
│   ├── config.py                      ← Environment configuration (API keys, paths)
│   └── requirements.txt               ← Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── pages/                     ← Full-page React views
│   │   │   ├── DashboardPage.jsx      ← KPI overview, win rate, memory stats
│   │   │   ├── RFPProcessorPage.jsx   ← Main RFP submission + live pipeline + results
│   │   │   ├── SourcingPage.jsx       ← Standalone global sourcing analysis tool
│   │   │   ├── KnowledgeBasePage.jsx  ← SME01 Q&A chat + document upload
│   │   │   ├── QuoteHistoryPage.jsx   ← All generated quotes with PDF download
│   │   │   └── SettingsPage.jsx       ← API key & configuration panel
│   │   │
│   │   ├── components/                ← Reusable UI components
│   │   │   ├── Sidebar.jsx            ← Animated navigation sidebar
│   │   │   ├── TopBar.jsx             ← Page header with status indicators
│   │   │   ├── SourcingTable.jsx      ← Global sourcing results table
│   │   │   ├── StrategyComparisonTable.jsx  ← Side-by-side strategy analysis
│   │   │   ├── FeedbackModal.jsx      ← Win/loss outcome submission modal
│   │   │   └── NegotiationPanel.jsx   ← Negotiation tactics display
│   │   │
│   │   ├── services/
│   │   │   └── api.js                 ← API client functions (all backend calls)
│   │   │
│   │   ├── App.jsx                    ← Root component with React Router setup
│   │   ├── main.jsx                   ← React entry point
│   │   └── index.css                  ← Dark glassmorphism design system (CSS variables, animations)
│   │
│   ├── index.html                     ← HTML shell with meta tags
│   ├── vite.config.js                 ← Vite config with /api proxy to backend
│   ├── eslint.config.js
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Run

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API key → [Get one here](https://aistudio.google.com/app/apikey)
- *(Optional)* Groq API key for LLaMA fallback → [Get one here](https://console.groq.com)

---

### 1. Clone the Repository

```bash
git clone https://github.com/Mohxmd-01/NEUROVOX-SME02.git
cd NEUROVOX-SME02
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and fill in your API keys (see Environment Variables section)

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will automatically:
- Build the FAISS knowledge index from documents in `data/documents/`
- Initialize Decision Memory (SME02) for learning from past quotes

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Open **http://localhost:5173** 🎉  
Swagger API Docs: **http://localhost:8000/docs**

---

## 🔌 API Endpoints

### Core Pipeline
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/process-rfp` | Full pipeline: RFP text → parse → price → compete → strategy → quote |
| `POST` | `/api/strategies` | Get all 3 strategy variants side-by-side for a given RFP |
| `POST` | `/api/simulate` | What-if price simulation across margin/win-probability scenarios |

### Quotes & History
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/quotes` | List all generated quotes |
| `GET` | `/api/quotes/{id}` | Get full details for a specific quote |
| `POST` | `/api/generate-pdf/{id}` | Generate PDF proposal for a quote |
| `GET` | `/api/download-pdf/{id}` | Download the generated PDF |

### Global Sourcing
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/sourcing` | Standalone sourcing analysis (regions, duties, lead times) |

### Knowledge Base (SME01)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/knowledge/chat` | Conversational Q&A over knowledge base with source citations |
| `POST` | `/api/knowledge/upload` | Upload document and re-index |
| `GET` | `/api/knowledge/status` | FAISS index stats |

### Outcome Feedback & Memory (SME02)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/feedback/{id}` | Record win/loss outcome for a quote |
| `GET` | `/api/feedback/{id}` | Retrieve feedback for a specific quote |
| `GET` | `/api/feedback/stats` | Overall win/loss statistics |
| `GET` | `/api/memory-stats` | Decision memory statistics |

### Geo & Catalog
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/countries` | All supported countries with tax/currency info |
| `GET` | `/api/tax-rate` | Tax rate for a specific country+product |
| `GET` | `/api/products` | Full product catalog |
| `POST` | `/api/extract-pdf` | Extract raw text from uploaded PDF |
| `GET` | `/api/health` | System health check |

---

## 🤖 Multi-Agent Pipeline

```
RFP Text / PDF Upload
        ↓
[Agent 1: RFP Parser]        ← Extracts product, client, quantity, country, requirements
        ↓
[Agent 2: Knowledge Agent]   ← RAG lookup over SME knowledge base (FAISS + Gemini)
        ↓
[Agent 3: Pricing Agent]     ← Internal cost calculation + base price from catalog
        ↓
[Agent 4: Competitor Agent]  ← Competitive benchmarking (market avg, low, high prices)
        ↓
[Agent 4b: Sourcing Agent]   ← Global supplier analysis (region, duty, lead time, savings)
        ↓
[Agent 5: Strategy Agent]    ← LLM-driven decision: Aggressive / Balanced / Premium
        ↓
[Tax & Currency Services]    ← Apply GST/VAT + convert to client's currency
        ↓
[Agent 6: Drafting Agent]    ← Generate professional PDF proposal (ReportLab)
        ↓
[Decision Memory (SME02)]    ← Save case for future learning
```

### Pricing Strategies

| Strategy | Logic | Best For |
|---|---|---|
| **Aggressive** | ~15% below competitor price | High-volume, price-sensitive bids |
| **Balanced** | ~5-10% below competitor | Standard enterprise deals |
| **Premium** | Value-based pricing at or above market | Specialized/high-margin products |

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required: Google Gemini LLM
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Groq fallback LLM (LLaMA 3.3 70B)
GROQ_API_KEY=your_groq_api_key_here
```

---

## 🌍 Global Sourcing & Geo-Pricing

IntelliQuote automatically:
1. **Detects client country** from RFP text (e.g., "shipping to Germany")
2. **Applies correct tax** — GST (India), VAT (EU/UK), Sales Tax (USA), etc.
3. **Converts prices** to the client's currency (EUR, USD, GBP, AED, etc.)
4. **Analyzes sourcing regions** — compares manufacturing in India, China, Vietnam, Germany, USA to find the best cost+logistics combination
5. **Shows import duties** and customs costs for cross-border shipments

---

## 📚 Knowledge Base (SME01) & Decision Memory (SME02)

### SME01 — Knowledge Base
- Drop any PDF, XLSX, or TXT file into `backend/data/documents/`
- The system auto-ingests, chunks, and indexes documents on startup
- The Knowledge Base agent retrieves the top-3 semantically relevant chunks for every RFP

### SME02 — Decision Memory
- Every processed quote is saved as a case (product, quantity, strategy, outcome)
- Similar past cases are recalled and shown in the RFP result panel
- Win/loss feedback updates the memory, improving future strategy recommendations

---

## 🏗 Built With

- **Google Gemini 2.0 Flash** — Core LLM for all agent reasoning
- **FAISS** — High-performance vector similarity search
- **FastAPI** — Modern async Python API framework
- **React 18 + Vite** — Lightning-fast frontend tooling
- **ReportLab** — PDF generation engine
- **sentence-transformers** — Local embedding model (`all-MiniLM-L6-v2`)

---

© 2026 NEUROVOX · IntelliQuote — AI Sales Decision Engine
