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

## Article Retrieval Pipeline

The article retrieval system (`backend/services/article_retrieval.py`) finds relevant academic articles by:

1. **Query Expansion** — Generates 6–10 academic queries from a user topic (surveys, keyword combinations, phased variants).
2. **Multi-Source Search** — Queries **Semantic Scholar**, **OpenAlex**, and **arXiv** in parallel via their public APIs.
3. **Normalization** — Each source's response is mapped to a `ResearchArticle` dataclass (title, authors, year, abstract, DOI, citation count, URL).
4. **Deduplication** — Removes duplicates by DOI first, then by normalized title.
5. **Ranking** — Scores each article using the weighted formula:

   | Component | Weight | Description |
   |-----------|--------|-------------|
   | Semantic similarity | 0.45 | Keyword overlap (swappable with dense embeddings) |
   | Title keyword match | 0.20 | Fraction of topic keywords in the title |
   | Abstract keyword match | 0.15 | Fraction of topic keywords in the abstract |
   | Citation count | 0.10 | Log-normalized citation count |
   | Recency | 0.10 | Exponential decay from current year |

   Each result includes a `reasonSelected` field explaining its ranking.

6. **Top 10** — The highest-scoring unique articles are returned.

**Endpoint:** `POST /api/articles/search` — body: `{"topic": "your research topic"}`

**API Keys:** Semantic Scholar and arXiv do not require keys. OpenAlex is rate-limited but free. No configuration needed.

## License

MIT
