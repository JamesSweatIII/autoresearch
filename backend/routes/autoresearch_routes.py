"""
API for the autoresearch-trained relevance model.

- GET  /api/autoresearch/status   -> {ready, best_accuracy, training, ...}  (gate)
- POST /api/autoresearch/predict   -> {score, relevant} for an unseen (query, doc)
- POST /api/autoresearch/train     -> kicks off background training on the papers
                                      a search gathered (fast, in-process)

The torch model is trained by the autoresearch loop / fast trainer. This router
degrades gracefully if torch or the trained model are absent — matching the rest
of the app's optional-dependency style.
"""

import sys
import threading
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

# Make autoresearch/ modules (features, model, infer, trainer_api) importable.
AUTORESEARCH_DIR = Path(__file__).resolve().parent.parent.parent / "autoresearch"
if str(AUTORESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(AUTORESEARCH_DIR))

try:
    import infer as ar_infer
    import trainer_api as ar_trainer
    AR_AVAILABLE = True
    _IMPORT_ERR = ""
except Exception as e:  # torch missing, etc.
    AR_AVAILABLE = False
    _IMPORT_ERR = str(e)

from database.setup import get_session, Document, Paper

router = APIRouter(prefix="/api/autoresearch", tags=["autoresearch"])

# In-memory training state (single-process demo).
TRAIN_STATE = {"status": "idle", "topic": "", "message": ""}


class PredictRequest(BaseModel):
    query: str
    title: str
    abstract: str = ""


class TrainRequest(BaseModel):
    job_id: Optional[int] = None
    topic: str = ""


def _load_papers(job_id=None):
    """Load the papers a search gathered. Prefer a specific job's documents;
    else fall back to recently discovered web papers."""
    db = get_session()
    try:
        papers = []
        if job_id is not None:
            docs = db.query(Document).filter(Document.job_id == job_id).all()
            papers = [{"title": d.title, "abstract": d.abstract or d.content or "",
                       "keywords": d.keywords or []} for d in docs]
        if not papers:
            rows = db.query(Paper).filter(Paper.source_type == "web") \
                     .order_by(Paper.id.desc()).limit(120).all()
            papers = [{"title": p.title, "abstract": p.abstract or p.content or "",
                       "keywords": p.keywords or []} for p in rows]
        return papers
    finally:
        db.close()


def _train_worker(papers, topic):
    global TRAIN_STATE
    try:
        TRAIN_STATE = {"status": "training", "topic": topic,
                       "message": f"Training on {len(papers)} papers…"}
        time.sleep(3)
        result = ar_trainer.train_from_papers(papers, topic=topic)
        if result.get("ok"):
            TRAIN_STATE = {"status": "ready" if result["ready"] else "below_gate",
                           "topic": topic, "message": "", **result}
        else:
            TRAIN_STATE = {"status": "failed", "topic": topic,
                           "message": result.get("error", "training failed")}
    except Exception as e:
        TRAIN_STATE = {"status": "failed", "topic": topic, "message": str(e)}


@router.get("/status")
def ar_status():
    if not AR_AVAILABLE:
        return {"available": False, "ready": False, "training": TRAIN_STATE,
                "error": _IMPORT_ERR}
    s = ar_infer.status()
    s["available"] = True
    s["training"] = TRAIN_STATE
    return s


@router.post("/train")
def ar_train(req: TrainRequest):
    if not AR_AVAILABLE:
        return {"ok": False, "error": "autoresearch unavailable", "detail": _IMPORT_ERR}
    if TRAIN_STATE.get("status") == "training":
        return {"ok": False, "error": "already training", "training": TRAIN_STATE}
    papers = _load_papers(req.job_id)
    if len(papers) < ar_trainer.MIN_PAPERS:
        return {"ok": False, "error": f"Insufficient data to train — {len(papers)} articles available, "
                f"requires at least {ar_trainer.MIN_PAPERS}. Please search for articles on the Dashboard first."}
    t = threading.Thread(target=_train_worker, args=(papers, req.topic), daemon=True)
    t.start()
    return {"ok": True, "status": "training", "n_papers": len(papers), "topic": req.topic}


@router.post("/predict")
def ar_predict(req: PredictRequest):
    if not AR_AVAILABLE:
        return {"error": "autoresearch model unavailable", "detail": _IMPORT_ERR}
    return ar_infer.predict(req.query, req.title, req.abstract)
