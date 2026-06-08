# AutoResearch — AI-Powered Research Intelligence Platform

An end-to-end platform that ingests, analyzes, and summarizes research documents using PySpark, NLP, and AI. Built with FastAPI, Next.js, and Tailwind CSS.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`.

## Architecture

```
User → Dashboard (Next.js) → API (FastAPI) → Pipeline (PySpark/Local)
         ↓                        ↓                    ↓
      Results Page ←──── SQLite Database ←─── NLP Analysis + Summarization
```

### Pipeline Stages

1. **Ingestion** — Load documents from sample data (50 AI/ML papers)
2. **Filtering** — Score documents by query-relevance using term overlap
3. **Processing** — PySpark (if available) or in-memory Python fallback
4. **NLP Analysis** — Keyword extraction, sentiment classification, relevance scoring
5. **Theme Detection** — Cluster keywords into research themes
6. **Summarization** — Generate executive summary, identify research gaps

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| Big Data | PySpark (optional, graceful fallback) |
| NLP | NLTK, regex-based keyword extraction |
| Frontend | Next.js 14, Tailwind CSS, Recharts |
| Processing | Multi-threaded background jobs |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Dataset statistics (50 docs, sources, years) |
| GET | `/api/sources` | List all publication venues |
| POST | `/api/research/` | Create a new research job |
| GET | `/api/research/` | List recent jobs |
| GET | `/api/research/{id}` | Get job results + summary |
| GET | `/api/research/{id}/documents` | Get ranked documents |

## Sample Dataset

50 influential AI/ML papers (2012–2024) from top venues:
NeurIPS, ICML, CVPR, Nature, ACL, ICLR, and more.

## Project Structure

```
autoreaserch/
├── backend/
│   ├── main.py
│   ├── routes/                  # API route handlers
│   ├── services/                # NLP, filtering, scoring
│   ├── models/                  # Pydantic schemas
│   ├── database/                # SQLAlchemy models
│   └── pipeline/                # PySpark / local processing
├── frontend/
│   ├── pages/                   # Next.js routes
│   ├── components/              # React components
│   │   ├── ui/                  # Base UI (Card, etc.)
│   │   ├── charts/              # Recharts visualizations
│   │   ├── dashboard/           # Dashboard widgets
│   │   └── layout/              # Navbar, Layout
│   └── styles/
├── data/
│   └── sample_documents.json
└── README.md
```

## License

MIT
