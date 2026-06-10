from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.article_pooler import start_pooler, get_pooler_status

router = APIRouter(prefix="/api/pooler", tags=["pooler"])


class PoolRequest(BaseModel):
    topics: Optional[List[str]] = None
    max_per_topic: int = 50
    topic_fraction: float = 0.5


class PoolResponse(BaseModel):
    new_articles: int = 0
    duplicates_skipped: int = 0
    topics_searched: int = 0
    details: list = []


@router.post("/pool")
def run_pooler(req: PoolRequest):
    if req.max_per_topic < 1 or req.max_per_topic > 200:
        raise HTTPException(400, "max_per_topic must be between 1 and 200")
    result = start_pooler(topics=req.topics, max_per_topic=req.max_per_topic, topic_fraction=req.topic_fraction)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/status")
def pooler_status():
    return get_pooler_status()
