# AutoResearch — Slide Deck Material

Drop-in lines for a **6–8 minute lightning talk** (16:9). Each slide has: a
**title**, **bullets** to paste, and a **say-this** speaker note. Expanded past
the 5 required slides — use what fits your timing (target ~10–12 slides ≈ 40 s
each). ★ = the 5 core slides you asked for.

Verified facts you can quote anywhere:
- 4 certified sources gather papers (Semantic Scholar, OpenAlex, arXiv, CrossRef)
  in **~6–14 s**.
- Relevance model: **67.4% → 91.9%** held-out via the autoresearch loop (47 experiments).
- Method validation on AG News: **51.85% → 90.85%**, 7 kept / 24 discarded.
- Gate: **≥ 85%** unlocks interaction.

---

## 1 — Title
**AutoResearch: From a Search Box to a Trained Relevance Model**
- Sub: *An AI agent that gathers research, then trains and gates its own model*
- James Sweat, Emmett Hannam, Steve Ferenzi · DS 5110 Big Data Systems · Summer 2026
- *Say-this:* "We turn a single typed concept into gathered papers and a model you can actually query."

## 2 — The problem / motivation
- Research volume outpaces anyone's ability to read it.
- Two manual bottlenecks: **finding** the relevant papers, and **tuning** a model to use them.
- Existing tools stop at search; they don't hand you a *trained, quality-checked* model for your topic.
- *Say-this:* "We attack both — the search *and* the model-building — and automate the model-building with an AI agent."

## 3 — Objective ★
- **Type a concept → gather relevant papers → train a model that scores each paper's relevance → (stretch) a summary 'expert' that describes a paper on click.**
- Make the model **trustworthy**: it's only exposed once it clears an accuracy gate (**≥ 85%**).
- Do the model-tuning **autonomously** with an AI coding agent (the "autoresearch" method).
- *Say-this:* "Objective in one line: search in, gathered + scored + queryable model out — with the agent doing the tuning."

## 4 — Key idea: two senses of "auto-research" (avoid confusion)
- **Data source:** the app *automatically researches* a topic — gathers papers from 6 sources.
- **Method:** *autoresearch* (Karpathy sense) — an AI agent **edits code → trains → evaluates → keeps good / discards bad**, looping until the metric clears a bar.
- One feeds the other: gathering builds the data; the loop optimizes the model.
- *Say-this:* "Important distinction: gathering is the data; the agent loop is the method. Both live in our system."

## 5 — System design ★
- **Frontend (S3-ready static site):** Next.js dashboard, results, knowledge base, and **/interact**.
- **Backend (FastAPI on EC2):** search → analyze → train → serve, with SQLite + background jobs.
- **Pipeline:** `gather (6 sources) → relevance rank + sentiment → train torch model → ≥85% gate → interact`.
- *(diagram suggestion: 4 boxes left→right: Search · Gather+Analyze · Autoresearch train · Gate+Interact)*
- *Say-this:* "Static UI up front, compute on EC2, object storage for models — clean separation of cheap UI and on-demand training."

## 6 — Data gathering & analysis
- 4 certified sources in parallel: **arXiv, Crossref, Semantic Scholar, OpenAlex**.
- Dedup (by DOI then normalized title) + **SentenceTransformer semantic ranking**.
- Each paper gets: **relevance score** (cosine similarity) with explanation, and **author sentiment** (TextBlob + Bing lexicon).
- Results returned in **~6–14 s**.
- *Say-this:* "One query fans out to six scholarly APIs; we merge, dedup, and enrich."

## 7 — The relevance model: what it does
- Input: a **(query, paper)** pair → output **0–1 relevance score** ("how on-topic is this paper?").
- Learns from **10 relational features** (query↔paper word/phrase overlap, coverage, title match…).
- Relational ⇒ **generalizes to papers it never saw** (and arbitrary pasted text).
- Honest scope: **lexical** relevance (term overlap), not deep semantics.
- *Say-this:* "It scores how well a paper matches what you asked for — and because the features are relational, it works on unseen papers."

## 8 — The autoresearch loop (the method) ★ (part 1 of implementation)
- Agent (OpenCode, via OpenRouter key, on EC2) is given a small **torch** training script.
- Loop: **edit CONFIG/model → train → eval held-out accuracy → `git commit` (keep) or `git checkout` (discard) → repeat.**
- Every experiment logged; a **progress curve** shows the climb.
- *Say-this:* "The agent does the boring part — try a change, measure, keep it only if it helped."

## 9 — Implementation details ★ (part 2)
- **EC2** runs the FastAPI backend + the training; **S3** hosts the static frontend (+ stores models/corpora).
- **OpenRouter** key powers the OpenCode agent; **NLTK/sklearn/torch** in the worker.
- Per-search **fast trainer** (seconds) trains on the gathered papers in a background thread; **/interact** polls and unlocks at **≥ 85%**.
- Optional-dependency design: PySpark, the LLM judge, and PDF extraction all degrade gracefully.
- *Say-this:* "Static site on S3, compute on EC2, agent via OpenRouter — and the model gates itself before users touch it."

## 10 — Results & key findings
- **Relevance model: 67.4% → 91.9%** held-out (unseen papers, 47 experiments).
- **Method validated on AG News: 51.85% → 90.85%** (7 kept / 24 discarded changes).
- Finding #1: the big wins were **fixing under-training + more data**, *not* fancier models.
- Finding #2: **automatic rejection** of bad changes is what creates the gains (a small, cheap agent suffices).
- Finding #3: **same-topic corpora are harder** (~85–87%) than diverse ones (91.9%) — which is *why* a gate matters.
- *(figure: `autoresearch/results/running_best.png` — the climbing curve crossing the gate)*

## 11 — Demo ★
- Live (or recorded): **search → "Train on gathered papers" → watch accuracy climb → gate unlocks → query a paper.**
- Show a matching paper scoring **~0.99 (relevant)** and an off-topic one **~0.00**.
- Whole loop runs in a **short window (seconds)**.
- Backup: link to the recorded demo video in the slides.
- *Say-this:* "Type a topic, click train, and in seconds you've got a gated model you can ask about any paper."

## 12 — Summary 'expert' (planned extension)
- On clicking a paper, a **summary engine** describes it in plain language — an on-demand "expert."
- Reuses the gathered abstract/PDF intro + an LLM (OpenRouter) to generate a short brief + why it's relevant.
- Turns the relevance score into an **explanation**, not just a number.
- *Say-this:* "Next step: don't just score a paper — explain it."

## 13 — Limitations & future work
- Lexical (not semantic) relevance; distant-supervision labels (no gold labels).
- Single-node training; multi-agent fan-out, S3 model storage, and a self-improving model copy are designed, not built.
- Summary engine is a prototype direction.
- *Say-this:* "Honest about scope — here's what's real and what's next."

## 14 — Conclusion ★
- We turned a **search box into a trained, self-gated relevance model** — gathering + analysis + an agent-tuned model.
- Implication for AI/data systems: **autonomous experimentation is a tracked, reproducible, scalable workload**; the load-bearing idea is **automatic evaluation gating**, not model size.
- Clean cloud split: cheap S3 UI + on-demand EC2 training + object-stored models.
- *Say-this:* "The agent and the gate matter more than the model — that's the takeaway."

## 15 — (Backup) AI-use & citation
- Tools: **OpenCode** (agent, via OpenRouter) tuned the model; **Claude** assisted design/scaffolding/report.
- Full chat logs in `chats/` per policy; data sources cited (arXiv, Crossref, Semantic Scholar, OpenAlex, PubMed, Scholar).

---

### Timing guide (≈7 min)
Title(10s) · Problem(30s) · Objective(40s) · Key idea(40s) · Design(50s) ·
Gather(40s) · Model(40s) · Loop(40s) · Implementation(40s) · Results(60s) ·
**Demo(90s)** · Conclusion(30s). Drop slides 4, 12, 13 first if you're long.

### Visual suggestions
- Slide 5: the 4-box pipeline diagram.
- Slide 10: the `relevance_running_best.png` curve (and optionally the AG News curve side-by-side).
- Slide 11: a 20-second screen capture GIF of search → train → unlock → query.
