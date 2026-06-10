# autoresearch/ — the autonomous-experimentation component

This module is the **autoresearch method** applied to AutoResearch's relevance
model. It is the direct analogue of the team's AG News project: an AI coding
agent (OpenCode) iterates on a small torch training setup — editing code,
training, evaluating, keeping good changes and discarding bad ones — until the
model crosses a quality bar.

> **Important framing (for the report/presentation):** "autoresearch" here means
> the **agent-driven keep/discard optimization loop** (the Karpathy sense), NOT
> the app automatically gathering papers. Paper-gathering is the *data source*;
> this loop is the *method*.

## Pipeline

```
GATHER (app: arXiv/Crossref/SemanticScholar/Scholar)
   └─> LABEL (distant supervision; LLM judge optional) ──► FREEZE dataset
        └─> AUTORESEARCH LOOP (OpenCode iterates train_relevance.py)
             edit → train → eval held-out accuracy → keep/discard → log
             └─> GATE: accuracy ≥ 0.90 ⇒ model "ready"
                  └─> INTERACT: /api/autoresearch/predict on unseen text
```

## Files
| File | Role |
|---|---|
| `build_dataset.py` | Freezes the labeled `(query, doc)` dataset → `data/relevance_dataset.jsonl` |
| `features.py` | Relational features (generalize to unseen text) |
| `model.py` | Torch `RelevanceNet` (shared by trainer + inference) |
| `train_relevance.py` | The training setup OpenCode optimizes (CONFIG + held-out eval + logging) |
| `plot.py` | Progress curve → `results/running_best.png` |
| `infer.py` | Load best model + predict; used by the backend |
| `AGENT_INSTRUCTIONS.md` | The keep/discard loop OpenCode follows |
| `experiments.jsonl` | Append-only log of every experiment |

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build_dataset.py
python train_relevance.py        # prints ACCURACY:, writes model + meta
python plot.py                   # -> results/running_best.png
```

Then point OpenCode at this folder + `AGENT_INSTRUCTIONS.md` and let it iterate
to ≥ 0.90. The backend exposes the result at `/api/autoresearch/status` and
`/api/autoresearch/predict`.
