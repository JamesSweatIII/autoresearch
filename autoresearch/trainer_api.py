"""
Fast in-process training of the relevance model on a given set of papers
(e.g. the papers a live search just gathered).

This is the "trains in the background, in a short window" path: build a labeled
dataset from the papers, train the torch model to a good fixed config in a few
seconds, evaluate held-out accuracy, and save the model + meta so the app can
gate interaction on >= 0.90.

(The OpenCode keep/discard loop in train_relevance.py is the slower, iterative
"autoresearch method" that produces the progress curve; this module is the quick
per-search trainer that uses a known-good config.)
"""

import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from features import compute_pair_features, FEATURE_NAMES
from model import RelevanceNet
from build_dataset import build_rows, write_rows

HERE = Path(__file__).resolve().parent
EXP_LOG = HERE / "experiments.jsonl"
MODEL_PATH = HERE / "data" / "relevance_torch.pt"
META_PATH = HERE / "data" / "model_meta.json"
READY_THRESHOLD = 0.85
N_FEATURES = len(FEATURE_NAMES)

# Known-good fast config (reaches ~0.92 on the sample corpus in a few seconds).
DEFAULT_CONFIG = {
    "hidden_dim": 0, "dropout": 0.0, "lr": 0.05, "weight_decay": 0.0,
    "epochs": 15, "batch_size": 64, "test_frac": 0.25, "threshold": 0.5, "seed": 0,
}
MIN_PAPERS = 8


def _group_split(rows, test_frac, seed):
    idxs = sorted({r["paper_idx"] for r in rows})
    rng = np.random.RandomState(seed); rng.shuffle(idxs)
    test = set(idxs[:max(1, int(len(idxs) * test_frac))])
    tr = [r for r in rows if r["paper_idx"] not in test]
    te = [r for r in rows if r["paper_idx"] in test]
    return tr, te


def _featurize(rows):
    X = np.stack([compute_pair_features(r["query"], r["title"], r["abstract"]) for r in rows])
    y = np.array([r["label"] for r in rows], dtype=np.float32)
    return torch.from_numpy(X), torch.from_numpy(y)


def _accuracy(model, X, y, thr):
    model.eval()
    with torch.no_grad():
        preds = (torch.sigmoid(model(X)) >= thr).float()
        return (preds == y).float().mean().item()


def train_from_papers(papers, config=None, topic=""):
    """Train the relevance model on `papers`. Returns a status dict."""
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    if len(papers) < MIN_PAPERS:
        return {"ok": False, "error": f"need >= {MIN_PAPERS} papers, got {len(papers)}"}

    t0 = time.time()
    torch.manual_seed(cfg["seed"]); np.random.seed(cfg["seed"])

    rows = build_rows(papers, seed=cfg["seed"])
    write_rows(rows)  # freeze the dataset used (provenance)
    tr, te = _group_split(rows, cfg["test_frac"], cfg["seed"])
    if not tr or not te:
        return {"ok": False, "error": "not enough papers to form a held-out split"}
    Xtr, ytr = _featurize(tr); Xte, yte = _featurize(te)

    model = RelevanceNet(N_FEATURES, cfg["hidden_dim"], cfg["dropout"])
    opt = torch.optim.Adam(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    loss_fn = nn.BCEWithLogitsLoss()
    n = Xtr.shape[0]
    for _ in range(cfg["epochs"]):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, cfg["batch_size"]):
            idx = perm[i:i + cfg["batch_size"]]
            opt.zero_grad()
            loss_fn(model(Xtr[idx]), ytr[idx]).backward()
            opt.step()

    acc = _accuracy(model, Xte, yte, cfg["threshold"])
    elapsed = round(time.time() - t0, 2)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "config": cfg, "n_features": N_FEATURES}, MODEL_PATH)
    json.dump({
        "best_accuracy": round(acc, 4),
        "ready": bool(acc >= READY_THRESHOLD),
        "threshold": cfg["threshold"],
        "ready_threshold": READY_THRESHOLD,
        "feature_names": FEATURE_NAMES,
        "config": cfg,
        "topic": topic,
        "n_papers": len(papers),
        "n_pairs": len(rows),
        "trained_seconds": elapsed,
    }, open(META_PATH, "w"), indent=2)
    with open(EXP_LOG, "a") as f:
        f.write(json.dumps({"test_acc": round(acc, 4), "elapsed_s": elapsed,
                            "config": cfg, "topic": topic, "n_papers": len(papers)}) + "\n")

    return {"ok": True, "accuracy": round(acc, 4), "ready": bool(acc >= READY_THRESHOLD),
            "n_papers": len(papers), "n_pairs": len(rows), "seconds": elapsed}
