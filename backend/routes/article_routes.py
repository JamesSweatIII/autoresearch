from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.article_retrieval import (
    find_relevant_articles,
    find_local_articles,
    ResearchArticle,
)
from database.setup import SessionLocal, Paper

router = APIRouter(prefix="/api/articles", tags=["articles"])


class ArticleSearchRequest(BaseModel):
    topic: str
    sources: List[str] = ["semantic_scholar", "openalex", "arxiv", "crossref"]


class ArticleResponse(BaseModel):
    id: str = ""
    title: str = ""
    authors: List[str] = []
    year: Optional[int] = None
    abstract: Optional[str] = None
    source: str = ""
    url: Optional[str] = None
    doi: Optional[str] = None
    citationCount: Optional[int] = None
    relevanceScore: Optional[float] = None
    reasonSelected: Optional[str] = None


class ArticleSearchResponse(BaseModel):
    topic: str
    sources: List[str]
    articles: List[ArticleResponse] = []
    total_found: int = 0


class SaveArticleRequest(BaseModel):
    title: str
    authors: List[str] = []
    year: Optional[int] = None
    abstract: Optional[str] = None
    source: str = ""
    url: Optional[str] = None
    doi: Optional[str] = None


def _auto_save_articles(articles):
    try:
        db = SessionLocal()
        try:
            for a in articles:
                if not a.title.strip():
                    continue
                dup = db.query(Paper).filter(Paper.title == a.title.strip()).first()
                if dup:
                    continue
                db.add(Paper(
                    title=a.title.strip(),
                    authors=", ".join(a.authors),
                    year=a.year or 2024,
                    abstract=a.abstract or "",
                    source=a.source or "web",
                    url=a.url or "",
                    source_type="web",
                ))
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


@router.post("/search", response_model=ArticleSearchResponse)
def search_articles(req: ArticleSearchRequest):
    if not req.topic.strip():
        return ArticleSearchResponse(topic=req.topic, sources=req.sources)

    has_local = "local" in req.sources
    external = [s for s in req.sources if s != "local"]

    results = []
    if external:
        results.extend(find_relevant_articles(req.topic.strip(), sources=external))
    if has_local:
        results.extend(find_local_articles(req.topic.strip()))

    _auto_save_articles(results)

    return ArticleSearchResponse(
        topic=req.topic,
        sources=req.sources,
        articles=[
            ArticleResponse(
                id=a.id,
                title=a.title,
                authors=a.authors,
                year=a.year,
                abstract=a.abstract,
                source=a.source,
                url=a.url,
                doi=a.doi,
                citationCount=a.citationCount,
                relevanceScore=a.relevanceScore,
                reasonSelected=a.reasonSelected,
            )
            for a in results
        ],
        total_found=len(results),
    )


@router.post("/save")
def save_article(req: SaveArticleRequest):
    if not req.title.strip():
        raise HTTPException(400, "Title is required")

    try:
        from database.setup import SessionLocal, Paper

        db = SessionLocal()
        try:
            paper = Paper(
                title=req.title.strip(),
                authors=", ".join(req.authors),
                year=req.year or 2024,
                abstract=req.abstract or "",
                source=req.source or "web",
                url=req.url or "",
                source_type="web",
            )
            db.add(paper)
            db.commit()
            return {"saved": True, "id": paper.id}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(500, f"Failed to save article: {e}")
