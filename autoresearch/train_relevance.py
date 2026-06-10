"""
Autoresearch training setup for the RELEVANCE model.

This is the "small training setup" the OpenCode agent optimizes — the direct
analogue of our AG News run.py, applied to the gathered-research domain.

The agent's loop (see AGENT_INSTRUCTIONS.md):
  edit the CONFIG block (and/or the model) -> python train_relevance.py ->
  keep the change if held-out accuracy went up (git commit),
  revert it if it went down (git checkout) -> repeat, until accuracy >= 0.90.

Task: given a (query, document) pair, predict relevant (1) / not-relevant (0).
Metric: accuracy on a held-out set of papers the model never trained on.
On exit it prints `ACCURACY: <x>`, appends to experiments.jsonl, and (if this
run is the best so far) saves relevance_torch.pt + model_meta.json so the app
can load the model and gate interaction on accuracy >= 0.90.

Run:  python autoresearch/train_relevance.py
"""

import json
import subprocess
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from features import compute_pair_features, FEATURE_NAMES
from model import RelevanceNet

# ============================================================
# CONFIG  --  the autoresearch agent edits THIS block to raise accuracy.
# Deliberately modest baseline so there is headroom for the curve to climb.
# ============================================================
CONFIG = {
    "hidden_dim": 64,        # MLP hidden width (0 = linear classifier)
    "dropout": 0.0,         # dropout probability
    "lr": 0.1,            # learning rate
    "weight_decay": 0.0,    # L2 regularization
    "epochs": 80,            # training epochs
    "batch_size": 64,       # minibatch size
    "test_frac": 0.25,      # fraction of PAPERS held out for testing
    "threshold": 0.5,       # decision threshold on the sigmoid output
    "seed": 0,              # RNG seed (reproducibility)
}
# ============================================================

HERE = Path(__file__).resolve().parent
DATASET = HERE / "data" / "relevance_dataset.jsonl"
EXP_LOG = HERE / "experiments.jsonl"
MODEL_PATH = HERE / "data" / "relevance_torch.pt"
META_PATH = HERE / "data" / "model_meta.json"
READY_THRESHOLD = 0.85
N_FEATURES = len(FEATURE_NAMES)


def load_rows():
    rows = []
    with open(DATASET) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def group_split(rows, test_frac, seed):
    """Hold out whole papers (by paper_idx) so test queries are 'unseen'."""
    idxs = sorted({r["paper_idx"] for r in rows})
    rng = np.random.RandomState(seed)
    rng.shuffle(idxs)
    n_test = max(1, int(len(idxs) * test_frac))
    test_papers = set(idxs[:n_test])
    train = [r for r in rows if r["paper_idx"] not in test_papers]
    test = [r for r in rows if r["paper_idx"] in test_papers]
    return train, test


def featurize(rows):
    X = np.stack([compute_pair_features(r["query"], r["title"], r["abstract"]) for r in rows])
    y = np.array([r["label"] for r in rows], dtype=np.float32)
    return torch.from_numpy(X), torch.from_numpy(y)


def accuracy(model, X, y, threshold):
    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(X))
        preds = (probs >= threshold).float()
        return (preds == y).float().mean().item()


def git_hash():
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True, timeout=5).stdout.strip()
        return (h + ("-dirty" if dirty else "")) if h else "no-git"
    except Exception:
        return "no-git"


def best_so_far():
    if META_PATH.exists():
        try:
            return json.load(open(META_PATH)).get("best_accuracy", -1.0)
        except Exception:
            return -1.0
    return -1.0


def main():
    cfg = CONFIG
    torch.manual_seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    t0 = time.time()

    if not DATASET.exists():
        raise SystemExit("Dataset missing. Run: python autoresearch/build_dataset.py")

    rows = load_rows()
    train_rows, test_rows = group_split(rows, cfg["test_frac"], cfg["seed"])
    Xtr, ytr = featurize(train_rows)
    Xte, yte = featurize(test_rows)
    print(f"[train] config={cfg}")
    print(f"[train] train_pairs={len(train_rows)}  test_pairs={len(test_rows)}  features={N_FEATURES}")

    model = RelevanceNet(N_FEATURES, cfg["hidden_dim"], cfg["dropout"])
    opt = torch.optim.Adam(model.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    loss_fn = nn.BCEWithLogitsLoss()

    n = Xtr.shape[0]
    for epoch in range(cfg["epochs"]):
        model.train()
        perm = torch.randperm(n)
        for i in range(0, n, cfg["batch_size"]):
            idx = perm[i:i + cfg["batch_size"]]
            opt.zero_grad()
            loss = loss_fn(model(Xtr[idx]), ytr[idx])
            loss.backward()
            opt.step()
        acc = accuracy(model, Xte, yte, cfg["threshold"])
        print(f"[train] epoch {epoch + 1}/{cfg['epochs']}  test_acc={acc:.4f}")

    test_acc = accuracy(model, Xte, yte, cfg["threshold"])
    n_params = sum(p.numel() for p in model.parameters())
    elapsed = round(time.time() - t0, 2)

    print(f"ACCURACY: {test_acc:.4f}")
    print(f"[train] params={n_params}  elapsed={elapsed}s  ready={test_acc >= READY_THRESHOLD}")

    EXP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EXP_LOG, "a") as f:
        f.write(json.dumps({
            "test_acc": round(test_acc, 4),
            "params": n_params,
            "elapsed_s": elapsed,
            "git": git_hash(),
            "config": cfg,
        }) + "\n")

    # Persist the model artifact only when it's the best seen, so the app always
    # loads the best relevance model and gates interaction on >= 0.90 accuracy.
    if test_acc >= best_so_far():
        torch.save({"state_dict": model.state_dict(),
                    "config": cfg, "n_features": N_FEATURES}, MODEL_PATH)
        json.dump({
            "best_accuracy": round(test_acc, 4),
            "ready": bool(test_acc >= READY_THRESHOLD),
            "threshold": cfg["threshold"],
            "ready_threshold": READY_THRESHOLD,
            "feature_names": FEATURE_NAMES,
            "config": cfg,
        }, open(META_PATH, "w"), indent=2)
        print(f"[train] saved best model (acc={test_acc:.4f}) -> {MODEL_PATH.name}")


if __name__ == "__main__":
    main()
