from fastapi import APIRouter, HTTPException
from database.setup import get_session, ResearchJob, Document

router = APIRouter(prefix="/api/research", tags=["research"])


@router.get("/")
def list_jobs():
    db = get_session()
    try:
        jobs = db.query(ResearchJob).order_by(ResearchJob.id.desc()).limit(50).all()
        return [
            {
                "id": j.id,
                "topic": j.topic,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else "",
                "documents_count": j.documents_count or 0,
            }
            for j in jobs
        ]
    finally:
        db.close()


@router.delete("/{job_id}")
def delete_job(job_id: int):
    db = get_session()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        db.query(Document).filter(Document.job_id == job_id).delete()
        db.delete(job)
        db.commit()
        return {"message": "Job deleted"}
    finally:
        db.close()
