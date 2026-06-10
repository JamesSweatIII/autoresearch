# Local-first implementation plan — AutoResearch + autoresearch loop

**Objective:** make the project *functional, coherent, and rubric-compliant*
locally. S3/EC2 deployment is a later stretch goal.

## What exists (James)
Full-stack app: Next.js frontend + FastAPI backend that gathers topic-related
papers from arXiv/Crossref/Semantic Scholar/Google Scholar, runs sentiment
(TextBlob + Bing lexicon), relevance ranking (BM25 + TF-IDF), an LLM relevance
judge (Ollama), and a one-shot sklearn relevance model. SQLite persistence.

## The gap vs. the rubric
The course's **autoresearch requirement** = an AI agent that edits training
code, trains, evaluates, and **keeps good / discards bad** changes, with
**experiment logs + a progress plot**. The app did not have this — its "Train
Model" button trains once (no iteration, no metric, no gate).

## What this branch adds (`autoresearch/`)
A genuine autoresearch loop that satisfies the requirement:
- `build_dataset.py` — freezes a labeled (query, doc) relevance dataset
  (distant supervision; LLM judge optional).
- `train_relevance.py` — a small **torch** training setup with an editable
  CONFIG block, a **held-out accuracy** metric, and per-run logging — the thing
  OpenCode iterates on.
- `model.py`, `features.py`, `infer.py`, `plot.py` — model, generalizing
  features, inference for the app, progress plot.
- `AGENT_INSTRUCTIONS.md` — the edit→train→eval→keep/discard loop for OpenCode.
- Backend `/api/autoresearch/status` + `/predict` — the **≥0.90 gate** and the
  interactive prediction endpoint.

## How each rubric/autoresearch requirement is met
| Requirement | Satisfied by |
|---|---|
| Agent given a small training setup | `train_relevance.py` (CONFIG) |
| Edit → train → eval → repeat | OpenCode loop (transcript) |
| Keep good / discard bad | git commit / `git checkout` |
| Experiment logs + progress plot | `experiments.jsonl` + `running_best.png` |
| One clear metric | held-out relevance accuracy, gate ≥ 0.90 |
| Demonstrable MVP | gathered data → trained model → gated interaction |
| AI-tool transcript | OpenCode session captured |

## Status / next steps
- [x] autoresearch module coded
- [x] backend endpoints wired (graceful fallback if torch absent)
- [x] tested locally end-to-end: build_dataset → train (0.674 baseline) →
      simulated improvement (0.9194, gate flips ready) → plot → infer; endpoints
      verified over HTTP via FastAPI TestClient
- [x] frontend `/interact` page (gated on ≥0.90), `next build` passes
- [ ] push branch (needs a GitHub account with write access to the repo)
- [ ] OpenCode runs the loop to ≥ 0.90 on the VM (real curve + transcript)
- [ ] (stretch) S3 static frontend + EC2 backend + S3 model/data storage

## Verification notes
- The baseline (0.674) model outputs ~0.47 for any input — it cannot
  discriminate. This is *why* the gate exists: `/interact` stays locked until the
  autoresearch loop reaches ≥0.90, at which point predictions separate cleanly
  (relevant ≈0.90 vs irrelevant ≈0.07 in testing).

## Run order (local)
```bash
# backend deps + autoresearch deps
cd backend && pip install -r requirements.txt && cd ..
cd autoresearch && pip install -r requirements.txt
python build_dataset.py && python train_relevance.py && python plot.py
# then run the app: backend `python main.py`, frontend `npm install && npm run dev`
```
