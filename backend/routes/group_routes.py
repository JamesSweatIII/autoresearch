from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.setup import SessionLocal, ResearchGroup, PaperGroup, Paper

router = APIRouter(tags=["groups"])


class CreateGroupBody(BaseModel):
    name: str
    description: str = ""


class AddPaperBody(BaseModel):
    paper_id: int


@router.get("/api/groups")
def list_groups():
    db = SessionLocal()
    try:
        groups = db.query(ResearchGroup).order_by(ResearchGroup.id.desc()).all()
        result = []
        for g in groups:
            count = db.query(PaperGroup).filter(PaperGroup.group_id == g.id).count()
            if count == 0:
                continue
            result.append({
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "paper_count": count,
            })
        return {"groups": result}
    finally:
        db.close()


@router.post("/api/groups")
def create_group(body: CreateGroupBody):
    db = SessionLocal()
    try:
        g = ResearchGroup(name=body.name, description=body.description)
        db.add(g)
        db.commit()
        db.refresh(g)
        return {"id": g.id, "name": g.name, "description": g.description}
    finally:
        db.close()


@router.get("/api/groups/{group_id}")
def get_group(group_id: int):
    db = SessionLocal()
    try:
        g = db.query(ResearchGroup).filter(ResearchGroup.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="Group not found")
        members = (
            db.query(PaperGroup, Paper)
            .join(Paper, PaperGroup.paper_id == Paper.id)
            .filter(PaperGroup.group_id == group_id)
            .order_by(PaperGroup.added_at.desc())
            .all()
        )
        papers = []
        for pg, p in members:
            papers.append({
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "source": p.source,
                "year": p.year,
                "abstract": p.abstract,
                "keywords": p.keywords or [],
                "source_type": p.source_type,
                "saved": bool(p.saved),
                "added_at": pg.added_at.isoformat() if pg.added_at else None,
            })
        return {
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "papers": papers,
            "paper_count": len(papers),
        }
    finally:
        db.close()


@router.post("/api/groups/{group_id}/papers")
def add_paper_to_group(group_id: int, body: AddPaperBody):
    db = SessionLocal()
    try:
        g = db.query(ResearchGroup).filter(ResearchGroup.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="Group not found")
        p = db.query(Paper).filter(Paper.id == body.paper_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Paper not found")
        existing = db.query(PaperGroup).filter(
            PaperGroup.paper_id == body.paper_id,
            PaperGroup.group_id == group_id,
        ).first()
        if not existing:
            pg = PaperGroup(paper_id=body.paper_id, group_id=group_id)
            db.add(pg)
            db.commit()
        return {"ok": True}
    finally:
        db.close()


@router.delete("/api/groups/{group_id}")
def delete_group(group_id: int):
    db = SessionLocal()
    try:
        g = db.query(ResearchGroup).filter(ResearchGroup.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail="Group not found")
        db.query(PaperGroup).filter(PaperGroup.group_id == group_id).delete()
        db.delete(g)
        db.commit()
        return {"message": "Group deleted"}
    finally:
        db.close()


@router.delete("/api/groups/{group_id}/papers/{paper_id}")
def remove_paper_from_group(group_id: int, paper_id: int):
    db = SessionLocal()
    try:
        pg = db.query(PaperGroup).filter(
            PaperGroup.paper_id == paper_id,
            PaperGroup.group_id == group_id,
        ).first()
        if pg:
            db.delete(pg)
            db.commit()
        return {"ok": True}
    finally:
        db.close()
