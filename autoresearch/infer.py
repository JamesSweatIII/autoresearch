"""
Inference + status helper for the autoresearch relevance model.

The FastAPI backend imports this to (a) report whether the model is "ready"
(held-out accuracy >= 0.90) and (b) score new (query, document) pairs the
model was never trained on.
"""

import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from features import compute_pair_features, FEATURE_NAMES
from model import RelevanceNet

HERE = Path(__file__).resolve().parent
MODEL_PATH = HERE / "data" / "relevance_torch.pt"
META_PATH = HERE / "data" / "model_meta.json"

_model: Optional[RelevanceNet] = None
_threshold = 0.5


def status() -> dict:
    """Model readiness for the gate. ready=True only when accuracy >= 0.90."""
    if META_PATH.exists():
        meta = json.load(open(META_PATH))
        meta["model_exists"] = MODEL_PATH.exists()
        return meta
    return {"best_accuracy": None, "ready": False, "model_exists": MODEL_PATH.exists()}


def _load() -> Optional[RelevanceNet]:
    global _model, _threshold
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        return None
    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    cfg = ckpt.get("config", {})
    net = RelevanceNet(ckpt.get("n_features", len(FEATURE_NAMES)),
                       cfg.get("hidden_dim", 0), cfg.get("dropout", 0.0))
    net.load_state_dict(ckpt["state_dict"])
    net.eval()
    _model = net
    _threshold = cfg.get("threshold", 0.5)
    return _model


def predict(query: str, title: str, abstract: str = "") -> dict:
    """Return {score, relevant} for an unseen (query, document) pair."""
    net = _load()
    if net is None:
        return {"score": 0.0, "relevant": False, "error": "model not trained"}
    x = torch.from_numpy(compute_pair_features(query, title, abstract)).unsqueeze(0)
    with torch.no_grad():
        score = float(torch.sigmoid(net(x)).item())
    return {"score": round(score, 4), "relevant": bool(score >= _threshold)}
