from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from services.article_retrieval import (
    find_relevant_articles,
    find_local_articles,
    ResearchArticle,
)

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


@router.post("/search", response_model=ArticleSearchResponse)
def search_articles(req: ArticleSearchRequest):
    if not req.topic.strip():
        return ArticleSearchResponse(topic=req.topic, sources=req.sources)

    if req.sources == ["local"]:
        results = find_local_articles(req.topic.strip())
    else:
        results = find_relevant_articles(req.topic.strip(), sources=req.sources)

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
