from fastapi import APIRouter, Query, HTTPException
from pathlib import Path
import json

from database.setup import get_session, Paper, ResearchJob
from services.research_service import find_similar_papers

router = APIRouter(prefix="/api", tags=["status"])

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SAMPLE_PATH = DATA_DIR / "sample_documents.json"


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "AutoResearch API"}


@router.get("/sources")
def get_sources():
    with open(SAMPLE_PATH) as f:
        docs = json.load(f)
    sources = list(set(d.get("source", "Unknown") for d in docs))
    return sources


@router.get("/stats")
def get_global_stats():
    db = get_session()
    try:
        paper_count = db.query(Paper).count()
        sample_count = db.query(Paper).filter(Paper.source_type == "sample").count()
        web_count = db.query(Paper).filter(Paper.source_type == "web").count()
        job_count = db.query(ResearchJob).count()
        sources = {}
        years = {}
        for p in db.query(Paper).all():
            src = p.source or "Unknown"
            sources[src] = sources.get(src, 0) + 1
            y = p.year or 2024
            years[y] = years.get(y, 0) + 1
        return {
            "total_papers": paper_count,
            "sample_papers": sample_count,
            "web_papers": web_count,
            "total_jobs": job_count,
            "sources": len(sources),
            "year_range": f"{min(years.keys())}–{max(years.keys())}" if years else "N/A",
            "source_distribution": dict(sorted(sources.items(), key=lambda x: -x[1])),
            "year_distribution": {str(k): v for k, v in sorted(years.items())},
        }
    finally:
        db.close()


@router.get("/papers")
def get_knowledge_base(
    search: str = Query("", description="Filter by title/author/abstract"),
    source_type: str = Query("", description="Filter by source_type (sample|web)"),
    source: str = Query("", description="Filter by publication source"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    db = get_session()
    try:
        q = db.query(Paper)
        if search:
            like = f"%{search}%"
            q = q.filter(
                Paper.title.ilike(like) |
                Paper.authors.ilike(like) |
                Paper.abstract.ilike(like)
            )
        if source_type:
            q = q.filter(Paper.source_type == source_type)
        if source:
            q = q.filter(Paper.source.ilike(f"%{source}%"))
        total = q.count()
        papers = q.order_by(Paper.id.desc()).offset(offset).limit(limit).all()
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "authors": p.authors or "",
                    "source": p.source or "",
                    "year": p.year or 2024,
                    "abstract": p.abstract or "",
                    "keywords": p.keywords or [],
                    "url": p.url or "",
                    "source_type": p.source_type or "",
                }
                for p in papers
            ],
        }
    finally:
        db.close()


@router.get("/papers/{paper_id}")
def get_paper(paper_id: int):
    db = get_session()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        all_papers = [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors or "",
                "source": p.source or "",
                "year": p.year or 2024,
                "abstract": p.abstract or "",
                "content": p.content or "",
                "keywords": p.keywords or [],
                "url": p.url or "",
                "source_type": p.source_type or "",
                "discovered_at": p.discovered_at.isoformat() if p.discovered_at else "",
            }
            for p in db.query(Paper).all()
        ]

        similar = find_similar_papers(paper_id, all_papers, top_n=5)

        return {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors or "",
                "source": paper.source or "",
                "year": paper.year or 2024,
                "abstract": paper.abstract or "",
                "content": paper.content or "",
                "keywords": paper.keywords or [],
                "url": paper.url or "",
                "source_type": paper.source_type or "",
                "discovered_at": paper.discovered_at.isoformat() if paper.discovered_at else "",
            },
            "similar_papers": similar,
        }
    finally:
        db.close()
