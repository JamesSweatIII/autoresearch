"""
Build (and FREEZE) the labeled relevance dataset that the autoresearch loop
trains on.

Why freeze? The autoresearch agent must optimize against a STABLE metric. If
labels were regenerated every iteration, the accuracy would drift and the
keep/discard decisions would be meaningless. So we generate the labeled
(query, document) pairs once, write them to a file, and the trainer reads that
fixed file on every run — exactly like a fixed train/test dataset.

Label source (distant supervision, no external LLM required):
  - POSITIVE: a query derived from a paper (its title / a keyword / an abstract
    phrase) is relevant to that same paper            -> label 1
  - NEGATIVE: the same query vs. a different random paper -> label 0
This produces real, non-circular relevance labels offline and reproducibly.
(The LLM judge in backend/services/llm_relevance.py can replace this labeler
later for higher-quality labels; the file format is identical.)

Each row also carries `paper_idx` so the trainer can do a GROUP split — test
queries come from papers unseen in training, which tests generalization to
documents the model was never trained on.

Run:  python autoresearch/build_dataset.py
"""

import ast
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SAMPLE_PATH = REPO / "data" / "sample_documents.json"
OUT_PATH = HERE / "data" / "relevance_dataset.jsonl"

SEED = 0
NEG_PER_QUERY = 2          # random irrelevant papers per query
MAX_KEYWORD_QUERIES = 4    # keyword-derived queries per paper
ABSTRACT_PHRASE_QUERIES = 2


def _as_list(val):
    """keywords may be a real list or a stringified list like "['a','b']"."""
    if isinstance(val, list):
        return [str(k) for k in val if k]
    if isinstance(val, str) and val.strip():
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(k) for k in parsed if k]
        except Exception:
            pass
        return [val]
    return []


def _abstract_phrases(abstract: str, rng: random.Random, n: int):
    words = (abstract or "").split()
    phrases = []
    for _ in range(n):
        if len(words) < 4:
            break
        start = rng.randint(0, max(0, len(words) - 4))
        length = rng.randint(2, 4)
        phrase = " ".join(words[start:start + length])
        if len(phrase) > 5:
            phrases.append(phrase)
    return phrases


def build_rows(papers, seed=SEED):
    """Build labeled (query, doc) rows from ANY list of paper dicts.

    Each paper dict needs `title`, `abstract` (or `content`), optional
    `keywords`. Used for both the seeded sample corpus and the papers a live
    search just gathered.
    """
    rng = random.Random(seed)
    n = len(papers)
    rows = []
    for i, p in enumerate(papers):
        title = (p.get("title") or "").strip()
        abstract = (p.get("abstract") or p.get("content") or "").strip()
        keywords = _as_list(p.get("keywords"))

        queries = []
        if title:
            queries.append(title)
        for kw in keywords[:MAX_KEYWORD_QUERIES]:
            if 0 < len(kw.split()) <= 5:
                queries.append(kw)
        queries += _abstract_phrases(abstract, rng, ABSTRACT_PHRASE_QUERIES)

        for q in queries:
            q = q.strip()
            if not q:
                continue
            rows.append({"query": q, "title": title, "abstract": abstract,
                         "label": 1, "paper_idx": i})
            others = [j for j in range(n) if j != i]
            for j in rng.sample(others, min(NEG_PER_QUERY, len(others))):
                d = papers[j]
                rows.append({
                    "query": q,
                    "title": (d.get("title") or "").strip(),
                    "abstract": (d.get("abstract") or d.get("content") or "").strip(),
                    "label": 0,
                    "paper_idx": i,
                })
    return rows


def write_rows(rows, out_path=OUT_PATH):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def build():
    papers = json.load(open(SAMPLE_PATH))
    rows = build_rows(papers)
    write_rows(rows)
    pos = sum(r["label"] for r in rows)
    print(f"[build_dataset] papers={len(papers)}  rows={len(rows)}  "
          f"positives={pos}  negatives={len(rows) - pos}")
    print(f"[build_dataset] wrote {OUT_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    build()
