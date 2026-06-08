from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database.setup import get_session, Paper
from services.relevance_model import (
    get_model, train_model, predict_relevance,
    batch_predict_relevance, MODEL_PATH, VECTORIZER_PATH,
)

router = APIRouter(prefix="/api/model", tags=["model"])


class PredictRequest(BaseModel):
    query: str
    title: str
    abstract: str = ""


class PredictResponse(BaseModel):
    score: float


class BatchPredictRequest(BaseModel):
    queries: List[str]
    titles: List[str]
    abstracts: List[str]


class ExplainResponse(BaseModel):
    score: float
    contributions: dict


class TrainResponse(BaseModel):
    status: str
    samples: int = 0
    papers: int = 0
    feature_importance: Optional[dict] = None
    message: str = ""


class StatusResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    trained: bool
    papers_count: int = 0
    model_path: str = ""
    feature_names: List[str] = []


@router.get("/status", response_model=StatusResponse)
def model_status():
    model = get_model()
    db = get_session()
    try:
        count = db.query(Paper).count()
    except Exception:
        count = 0
    finally:
        db.close()
    return StatusResponse(
        trained=model.trained,
        papers_count=count,
        model_path=str(MODEL_PATH) if MODEL_PATH.exists() else "",
        feature_names=model.feature_names if model.trained else [],
    )


@router.post("/train", response_model=TrainResponse)
def train():
    db = get_session()
    try:
        papers = db.query(Paper).all()
        if len(papers) < 5:
            raise HTTPException(400, f"Need at least 5 papers, have {len(papers)}")
        paper_dicts = [
            {
                "title": p.title or "",
                "abstract": p.abstract or "",
                "keywords": p.keywords or [],
            }
            for p in papers
        ]
        result = train_model(paper_dicts)
        if result["status"] == "error":
            raise HTTPException(400, result["message"])
        return TrainResponse(
            status="ok",
            samples=result.get("samples", 0),
            papers=result.get("papers", 0),
            feature_importance=result.get("feature_importance"),
            message=f"Trained on {result['samples']} pairs from {result['papers']} papers",
        )
    finally:
        db.close()


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    score = predict_relevance(req.query, req.title, req.abstract)
    return PredictResponse(score=score)


@router.post("/batch-predict", response_model=List[float])
def batch_predict(req: BatchPredictRequest):
    scores = batch_predict_relevance(req.queries, req.titles, req.abstracts)
    return scores


@router.post("/explain", response_model=ExplainResponse)
def explain(req: PredictRequest):
    model = get_model()
    if not model.trained:
        raise HTTPException(400, "Model not trained yet")
    result = model.explain(req.query, req.title, req.abstract)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return ExplainResponse(
        score=result["score"],
        contributions=result["contributions"],
    )
