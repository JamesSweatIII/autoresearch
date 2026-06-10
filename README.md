# AutoResearch — AI-Powered Research Intelligence Platform

An end-to-end platform that gathers, analyzes, and trains relevance models on
academic research papers. Built with FastAPI, Next.js 14, PyTorch, and Tailwind CSS.

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
User → Dashboard (Next.js) → API (FastAPI) → Article Retrieval (4 sources)
         ↓                        ↓                    ↓
      Results ←──── SQLite Database ←─── Semantic Ranking + Sentiment
         ↓                        ↓
   Research Groups          Autoresearch Torch Model
   (organize papers)        (gated at ≥85% accuracy)
```

### Pipeline

1. **Article Retrieval** — Search 4 academic sources in parallel (Semantic Scholar, OpenAlex, arXiv, CrossRef)
2. **Semantic Ranking** — Score articles by SentenceTransformer similarity to the query topic
3. **Sentiment Analysis** — Classify authorial sentiment (TextBlob + Bing Liu lexicon)
4. **Autoresearch Loop** — AI agent (OpenCode) iterates on a PyTorch model: edit → train → eval → keep/discard
5. **Gate & Interact** — Model unlocks at ≥85% held-out accuracy; query relevance via `/interact` page

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy, SQLite |
| Search | Semantic Scholar, OpenAlex, arXiv, CrossRef APIs |
| ML | PyTorch 2.1+, SentenceTransformers, scikit-learn |
| NLP | NLTK, TextBlob, Bing Liu sentiment lexicon |
| Frontend | Next.js 14, Tailwind CSS, Recharts |
| Agent | OpenCode (AI coding CLI via OpenRouter) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats` | Dataset statistics |
| GET | `/api/sources` | List all publication venues |
| GET | `/api/papers` | List/filter papers |
| GET | `/api/papers/{id}` | Paper detail + similar papers |
| PATCH | `/api/papers/{id}/save` | Toggle saved/bookmark status |
| GET | `/api/groups` | List research groups |
| POST | `/api/groups` | Create research group |
| GET | `/api/groups/{id}` | Get group with papers |
| DELETE | `/api/groups/{id}` | Delete group |
| POST | `/api/groups/{id}/papers` | Add paper to group |
| DELETE | `/api/groups/{id}/papers/{paper_id}` | Remove paper from group |
| GET | `/api/research/` | List research jobs |
| DELETE | `/api/research/{id}` | Delete research job |
| POST | `/api/articles/search` | Multi-source article search |
| POST | `/api/articles/save` | Save article to database |
| POST | `/api/pooler/pool` | Background article gathering |
| GET | `/api/pooler/status` | Pooler background task status |
| GET | `/api/autoresearch/status` | Model readiness gate |
| POST | `/api/autoresearch/predict` | Score a (query, doc) pair |
| POST | `/api/autoresearch/train` | Train model on gathered papers |

## Project Structure

```
autoresearch/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── database/
│   │   └── setup.py             # SQLAlchemy models (Paper, Document, ResearchJob)
│   ├── routes/
│   │   ├── article_routes.py    # POST /api/articles/search, /save
│   │   ├── autoresearch_routes.py  # GET/POST /api/autoresearch/*
│   │   ├── group_routes.py      # CRUD /api/groups, add/remove papers
│   │   ├── legacy_routes.py     # GET /api/stats, /api/papers, /api/sources
│   │   ├── pooler_routes.py     # POST /api/pooler/pool
│   │   └── research_routes.py   # GET/DELETE /api/research
│   └── services/
│       ├── article_retrieval.py # Multi-source search + semantic ranking
│       ├── article_pooler.py    # Background topic-based article gathering
│       └── local_llm.py         # SentenceTransformer ranking
├── frontend/
│   ├── pages/                   # Next.js routes (dashboard, interact, knowledge, pipeline, about)
│   ├── components/              # React components (ui/, charts/, dashboard/, layout/)
│   └── styles/
├── autoresearch/                # Autonomous experimentation module
│   ├── train_relevance.py       # PyTorch training (agent iterates on this)
│   ├── model.py                 # RelevanceNet (simple MLP)
│   ├── features.py              # 10 relational features
│   ├── infer.py                 # Inference for the backend
│   ├── build_dataset.py         # Labeled dataset builder
│   ├── plot.py                  # Accuracy progress curve
│   └── AGENT_INSTRUCTIONS.md    # Keep/discard loop for OpenCode
├── data/
│   ├── autoresearch.db          # SQLite database
│   ├── sample_documents.json.bak  # Sample papers (50 AI/ML papers)
│   ├── relevance_model.pkl      # sklearn relevance model
│   └── salex_bing.csv           # Bing Liu sentiment lexicon
├── DEMO.md
├── FINAL_REPORT.md
├── PLAN.md
├── SLIDES.md
├── DEPLOY.md
└── README.md
```

## Article Retrieval

The article retrieval system (`backend/services/article_retrieval.py`) finds relevant
academic articles by querying **4 sources in parallel**:

1. **Semantic Scholar** — Rich metadata + citation counts
2. **OpenAlex** — Large open scholarly index
3. **arXiv** — Pre-print repository
4. **CrossRef** — DOI registration agency

Results are deduplicated (by DOI then normalized title), then ranked by
**SentenceTransformer semantic similarity** (`all-MiniLM-L6-v2`) against the
user's topic. Each result includes a relevance score and explanation.

**Endpoint:** `POST /api/articles/search` — body: `{"topic": "your topic", "sources": ["semantic_scholar", "openalex", "arxiv", "crossref"]}`

No API keys required (all sources are free/public).

## Autoresearch Module

The `autoresearch/` directory implements the **autonomous experimentation loop**
that optimizes a PyTorch relevance model. An AI agent (OpenCode):

1. Edits the training config or model architecture
2. Trains and evaluates held-out accuracy
3. Keeps improvements (`git commit`) or discards regressions (`git checkout`)
4. Logs every experiment to `experiments.jsonl`
5. Produces a progress curve (`results/running_best.png`)

The model is exposed through a **gated** API — interaction unlocks only once
accuracy reaches ≥85%. Best achieved: **91.9%** held-out accuracy.

## Sample Dataset

50 influential AI/ML papers (2012–2024) from top venues:
NeurIPS, ICML, CVPR, Nature, ACL, ICLR, and more (see `data/sample_documents.json.bak`).

## License

MIT
