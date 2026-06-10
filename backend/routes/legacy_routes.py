from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from database.setup import SessionLocal, Paper

router = APIRouter(tags=["legacy"])


@router.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        total = db.query(Paper).count()
        source_counts = {}
        source_type_counts = {}
        for p in db.query(Paper).all():
            src = p.source or "Unknown"
            source_counts[src] = source_counts.get(src, 0) + 1
            st = p.source_type or "unknown"
            source_type_counts[st] = source_type_counts.get(st, 0) + 1
        return {
            "total_papers": total,
            "source_distribution": dict(sorted(source_counts.items(), key=lambda x: -x[1])),
            "source_type_distribution": dict(sorted(source_type_counts.items(), key=lambda x: -x[1])),
            "total_jobs": 0,
            "sources": len(source_counts),
        }
    finally:
        db.close()


@router.get("/api/papers")
def list_papers(
    search: str = "", source: str = "", source_type: str = "",
    saved: str = "", limit: int = 20, offset: int = 0
):
    db = SessionLocal()
    try:
        q = db.query(Paper)
        if search:
            q = q.filter(
                Paper.title.ilike(f"%{search}%")
                | Paper.abstract.ilike(f"%{search}%")
                | Paper.authors.ilike(f"%{search}%")
            )
        if source:
            sources = [s.strip() for s in source.split(",") if s.strip()]
            if len(sources) == 1:
                q = q.filter(Paper.source == sources[0])
            elif len(sources) > 1:
                q = q.filter(Paper.source.in_(sources))
        if source_type:
            q = q.filter(Paper.source_type == source_type)
        if saved == "true":
            q = q.filter(Paper.saved == 1)
        elif saved == "false":
            q = q.filter(Paper.saved == 0)
        total = q.count()
        rows = q.order_by(Paper.id.desc()).offset(offset).limit(limit).all()
        def format_url(url, source_type, source):
            if not url:
                return ""
            if url.startswith("http"):
                return url
            if source_type == "sample" or url.startswith("10."):
                return f"https://doi.org/{url}"
            return url

        papers = [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "source": p.source,
                "year": p.year,
                "abstract": p.abstract,
                "keywords": p.keywords or [],
                "url": format_url(p.url, p.source_type, p.source),
                "source_type": p.source_type,
                "saved": bool(p.saved),
            }
            for p in rows
        ]
        return {"papers": papers, "total": total}
    finally:
        db.close()


@router.get("/api/sources")
def list_sources(source_type: str = ""):
    db = SessionLocal()
    try:
        q = db.query(Paper.source)
        if source_type:
            q = q.filter(Paper.source_type == source_type)
        sources = sorted(set(row[0] for row in q.all() if row[0] and row[0].lower() != "test"))
        return {"sources": sources}
    finally:
        db.close()


@router.get("/api/papers/{paper_id}")
def get_paper(paper_id: int):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return {"paper": None, "similar_papers": []}
        similar = (
            db.query(Paper)
            .filter(Paper.id != paper_id, Paper.source == paper.source)
            .limit(5)
            .all()
        )
        def fmt_url(url, st, src):
            if not url:
                return ""
            if url.startswith("http"):
                return url
            if st == "sample" or url.startswith("10."):
                return f"https://doi.org/{url}"
            return url

        return {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "authors": paper.authors,
                "source": paper.source,
                "year": paper.year,
                "abstract": paper.abstract,
                "content": paper.content or "",
                "keywords": paper.keywords or [],
                "url": fmt_url(paper.url, paper.source_type, paper.source),
                "source_type": paper.source_type,
            },
            "similar_papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "authors": p.authors,
                    "source": p.source,
                    "year": p.year,
                    "abstract": p.abstract,
                    "source_type": p.source_type,
                }
                for p in similar
            ],
        }
    finally:
        db.close()


class SaveToggle(BaseModel):
    saved: bool


@router.patch("/api/papers/{paper_id}/save")
def toggle_saved(paper_id: int, body: SaveToggle):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        paper.saved = 1 if body.saved else 0
        db.commit()
        return {"id": paper.id, "saved": body.saved}
    finally:
        db.close()
