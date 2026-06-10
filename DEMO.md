# Local demo — search → train relevance model → interact

The whole flow runs locally in a short window. Verified end-to-end: a live
"graph neural networks" search gathered 85 papers from 6 sources and trained a
model on them in **~14 seconds total**.

## One-time setup

**Backend (Python).** A virtualenv with the deps + NLTK data:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # fastapi, sqlalchemy, sklearn, nltk, torch, etc.
python -m nltk.downloader opinion_lexicon punkt stopwords   # needed by sentiment
```
> Note: the sentiment module calls NLTK's `opinion_lexicon` at import time, so the
> download above is required or the API won't boot. PySpark is optional (the
> pipeline falls back to local processing).

**Frontend (Node).**
```bash
cd frontend && npm install
```

## Run it (two terminals)

```bash
# Terminal 1 — API on :8000
cd backend && source .venv/bin/activate && python main.py

# Terminal 2 — UI on :3000 (proxies /api → :8000)
cd frontend && npm run dev
```
Open **http://localhost:3000**.

## The demo flow

1. **Search** — Dashboard → type a topic (e.g. *graph neural networks*) → *Start
   Research*. The pipeline gathers papers from arXiv, Crossref, Semantic Scholar,
   OpenAlex, PubMed, and Google Scholar, scores relevance + sentiment, and stores
   results (watch the live status; ~6–15 s).
2. **Train in the background** — go to **Interact** → click **"Train relevance
   model on gathered papers."** A background thread builds a labeled dataset from
   the papers the search just gathered and trains the torch model in a few
   seconds. The status card polls and updates live (accuracy vs. the 90% gate).
3. **See it gated** — interaction unlocks **only at ≥ 90% held-out accuracy**:
   - **Diverse corpus** (e.g. the default model trained on the mixed sample set):
     **91.9%** → unlocked. Type a topic + paper and get a relevance score; a
     matching paper scores ~0.99, an off-topic one ~0.00.
   - **Single-topic live search** (all papers about one topic): lands **~85–87%**
     → **stays locked**. This is the gate doing its job — a model that can't
     clearly tell the gathered papers apart is not exposed. Good talking point.

## What's real vs. illustrative
- ✅ Real: live multi-source gathering, sentiment, relevance ranking, the torch
  model trained on the gathered papers, the ≥90% gate, and prediction on unseen text.
- The **fast background trainer** uses a known-good config (seconds). The separate
  **OpenCode keep/discard loop** (`autoresearch/train_relevance.py` +
  `AGENT_INSTRUCTIONS.md`) is the iterative "autoresearch method" that produces the
  progress curve (`assets/relevance_running_best.png`, 67.4% → 91.9%).

## Reset to a clean state (optional, before recording)
```bash
# make the default model "ready" (diverse sample corpus, 91.9%)
cd backend && source .venv/bin/activate
python -c "import sys,json;sys.path.insert(0,'.');sys.path.insert(0,'../autoresearch');import trainer_api;\
p=[{'title':x['title'],'abstract':x.get('abstract',''),'keywords':x.get('keywords',[])} for x in json.load(open('../data/sample_documents.json'))];\
print(trainer_api.train_from_papers(p, topic='sample corpus'))"
```
