from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from database.setup import get_session, ResearchJob, Document
from models.schemas import ResearchJobCreate, ResearchJobResponse, DocumentResponse
from pipeline.processing import ResearchPipeline
import threading
import time

router = APIRouter(prefix="/api/research", tags=["research"])
pipeline = ResearchPipeline()
active_jobs = {}


class ResearchResult(ResearchJobResponse):
    pass


@router.post("/", response_model=ResearchJobResponse)
def create_research_job(req: ResearchJobCreate):
    db = get_session()
    try:
        job = ResearchJob(topic=req.topic)
        db.add(job)
        db.commit()
        db.refresh(job)

        def run(job_id, topic):
            try:
                pipeline.run_pipeline(job_id, topic)
            except Exception as e:
                db2 = get_session()
                j = db2.query(ResearchJob).filter(ResearchJob.id == job_id).first()
                if j:
                    j.status = f"failed: {str(e)[:100]}"
                    db2.commit()
                db2.close()

        t = threading.Thread(target=run, args=(job.id, req.topic), daemon=True)
        active_jobs[job.id] = t
        t.start()

        return ResearchJobResponse(
            id=job.id,
            topic=job.topic,
            status=job.status,
            created_at=job.created_at.isoformat() if job.created_at else "",
        )
    finally:
        db.close()


@router.get("/", response_model=list)
def list_jobs(
    sentiment: str = Query("", description="Filter by dominant sentiment (positive/negative/neutral)"),
    sort_by: str = Query("date", description="Sort order: date, relevance, docs"),
):
    db = get_session()
    try:
        q = db.query(ResearchJob).order_by(ResearchJob.id.desc()).limit(50)
        all_jobs = q.all()
        if sentiment:
            all_jobs = [j for j in all_jobs if (j.sentiment_distribution or {}).get(sentiment, 0) > 0]
        # Active jobs first (pending/ingesting/processing/analyzing/summarizing),
        # then completed/failed, all sorted by selected order
        STATUS_RANK = {"pending": 0, "ingesting": 1, "processing": 2,
                       "analyzing": 3, "summarizing": 4, "completed": 5, "failed": 6}
        if sort_by == "relevance":
            all_jobs.sort(key=lambda j: (
                STATUS_RANK.get(j.status, 99),
                -(j.avg_relevance or 0),
                -(j.created_at.timestamp() if j.created_at else 0)
            ))
        elif sort_by == "docs":
            all_jobs.sort(key=lambda j: (
                STATUS_RANK.get(j.status, 99),
                -(j.documents_count or 0),
                -(j.created_at.timestamp() if j.created_at else 0)
            ))
        else:
            all_jobs.sort(key=lambda j: (
                STATUS_RANK.get(j.status, 99),
                -(j.created_at.timestamp() if j.created_at else 0)
            ))
        jobs = all_jobs[:20]
        return [
            ResearchJobResponse(
                id=j.id, topic=j.topic, status=j.status,
                created_at=j.created_at.isoformat() if j.created_at else "",
                completed_at=j.completed_at.isoformat() if j.completed_at else None,
                documents_count=j.documents_count or 0,
                top_keywords=j.top_keywords or [],
                avg_relevance=j.avg_relevance or 0.0,
                top_source=j.top_source or "",
                processing_time=j.processing_time or 0.0,
                web_results_count=j.web_results_count or 0,
                sentiment_distribution=j.sentiment_distribution or {},
            )
            for j in jobs
        ]
    finally:
        db.close()


@router.get("/{job_id}", response_model=ResearchResult)
def get_job_status(job_id: int):
    db = get_session()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return ResearchResult(
            id=job.id, topic=job.topic, status=job.status,
            created_at=job.created_at.isoformat() if job.created_at else "",
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            documents_count=job.documents_count or 0,
            top_keywords=job.top_keywords or [],
            avg_relevance=job.avg_relevance or 0.0,
            top_source=job.top_source or "",
            processing_time=job.processing_time or 0.0,
            summary=job.summary or "",
            themes=job.themes or [],
            research_gaps=job.research_gaps or [],
            topic_distribution=job.topic_distribution or {},
            keyword_frequency=job.keyword_frequency or {},
            source_rankings=job.source_rankings or [],
            web_results_count=job.web_results_count or 0,
            sentiment_distribution=job.sentiment_distribution or {},
        )
    finally:
        db.close()


@router.get("/{job_id}/documents", response_model=list)
def get_documents(job_id: int, limit: int = 50, sentiment: str = Query("", description="Filter by sentiment (positive/negative/neutral)")):
    db = get_session()
    try:
        q = db.query(Document).filter(Document.job_id == job_id)
        if sentiment:
            q = q.filter(Document.sentiment == sentiment)
        docs = q.order_by(Document.relevance_score.desc()).limit(limit).all()
        return [
            DocumentResponse(
                id=d.id, title=d.title, authors=d.authors or "",
                source=d.source or "", year=d.year or 2024,
                abstract=d.abstract or "", keywords=d.keywords or [],
                relevance_score=d.relevance_score or 0.0,
                sentiment=d.sentiment or "neutral",
                topic_cluster=d.topic_cluster or "",
                source_type=d.source_type or "sample",
                url=d.url or "",
                paper_id=d.paper_id,
            )
            for d in docs
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


@router.post("/{job_id}/retry", response_model=ResearchJobResponse)
def retry_job(job_id: int):
    db = get_session()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        new_job = ResearchJob(topic=job.topic)
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        def run(jid, topic):
            try:
                pipeline.run_pipeline(jid, topic)
            except Exception as e:
                db2 = get_session()
                j = db2.query(ResearchJob).filter(ResearchJob.id == jid).first()
                if j:
                    j.status = f"failed: {str(e)[:100]}"
                    db2.commit()
                db2.close()

        t = threading.Thread(target=run, args=(new_job.id, job.topic), daemon=True)
        active_jobs[new_job.id] = t
        t.start()

        return ResearchJobResponse(
            id=new_job.id,
            topic=new_job.topic,
            status=new_job.status,
            created_at=new_job.created_at.isoformat() if new_job.created_at else "",
        )
    finally:
        db.close()
