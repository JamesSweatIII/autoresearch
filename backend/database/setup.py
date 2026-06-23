import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import json
from pathlib import Path
from sqlalchemy import inspect, text as sql_text

SAMPLE_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_documents.json.bak"

_default_db_dir = Path(__file__).resolve().parent.parent.parent / "data"
_default_db_dir.mkdir(parents=True, exist_ok=True)
_default_db_url = f"sqlite:///{_default_db_dir / 'autoresearch.db'}"

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    try:
        from sqlalchemy.engine.url import make_url
        parsed = make_url(DATABASE_URL)
        db_path = parsed.database
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        DATABASE_URL = None

if not DATABASE_URL:
    DATABASE_URL = _default_db_url

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,
    )
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    documents_count = Column(Integer, default=0)
    top_keywords = Column(JSON, default=list)
    avg_relevance = Column(Float, default=0.0)
    top_source = Column(String(200), default="")
    processing_time = Column(Float, default=0.0)
    summary = Column(Text, default="")
    themes = Column(JSON, default=list)
    research_gaps = Column(JSON, default=list)
    topic_distribution = Column(JSON, default=dict)
    keyword_frequency = Column(JSON, default=dict)
    source_rankings = Column(JSON, default=list)
    web_results_count = Column(Integer, default=0)
    sentiment_distribution = Column(JSON, default=dict)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    paper_id = Column(Integer, nullable=True)
    title = Column(String(500), nullable=False)
    authors = Column(String(500), default="")
    source = Column(String(200), default="")
    year = Column(Integer, default=2024)
    abstract = Column(Text, default="")
    content = Column(Text, default="")
    keywords = Column(JSON, default=list)
    relevance_score = Column(Float, default=0.0)
    sentiment = Column(String(50), default="neutral")
    sentiment_scores = Column(JSON, default=dict)
    topic_cluster = Column(String(100), default="")
    source_type = Column(String(50), default="sample")
    url = Column(String(500), default="")
    llm_verified = Column(Integer, default=0)


class ResearchGroup(Base):
    __tablename__ = "research_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PaperGroup(Base):
    __tablename__ = "paper_groups"
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, nullable=False)
    group_id = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(String(500), default="")
    source = Column(String(200), default="web")
    year = Column(Integer, default=2024)
    abstract = Column(Text, default="")
    content = Column(Text, default="")
    keywords = Column(JSON, default=list)
    url = Column(String(500), default="")
    source_type = Column(String(50), default="web")
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    saved = Column(Integer, default=0)


def init_db():
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    _migrate_old_schema()
    _migrate_new_tables()
    _seed_sample_papers()


def _wait_for_db(max_retries=10, delay=2):
    if DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import text
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[AutoResearch] Database connected")
            return
        except Exception as e:
            print(f"[AutoResearch] DB connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                import time
                time.sleep(delay)
    print("[AutoResearch] WARNING: Could not connect to database after retries")


def _migrate_new_tables():
    ResearchGroup.__table__.create(bind=engine, checkfirst=True)
    PaperGroup.__table__.create(bind=engine, checkfirst=True)


def _migrate_old_schema():
    inspector = inspect(engine)
    try:
        indexes = [i["name"] for i in inspector.get_indexes("papers")]
        if "uq_paper_title" in indexes:
            with engine.connect() as conn:
                conn.execute(sql_text("DROP INDEX IF EXISTS uq_paper_title"))
                conn.commit()
            print("[AutoResearch] Removed old unique constraint from papers.title")
    except Exception:
        pass
    try:
        columns = [c["name"] for c in inspector.get_columns("documents")]
        if "sentiment_scores" not in columns:
            with engine.connect() as conn:
                conn.execute(sql_text("ALTER TABLE documents ADD COLUMN sentiment_scores JSON DEFAULT '{}'"))
                conn.commit()
            print("[AutoResearch] Added sentiment_scores column to documents")
    except Exception:
        pass
    try:
        columns = [c["name"] for c in inspector.get_columns("documents")]
        if "llm_verified" not in columns:
            with engine.connect() as conn:
                conn.execute(sql_text("ALTER TABLE documents ADD COLUMN llm_verified INTEGER DEFAULT 0"))
                conn.commit()
            print("[AutoResearch] Added llm_verified column to documents")
    except Exception:
        pass
    try:
        columns = [c["name"] for c in inspector.get_columns("papers")]
        if "saved" not in columns:
            with engine.connect() as conn:
                conn.execute(sql_text("ALTER TABLE papers ADD COLUMN saved INTEGER DEFAULT 0"))
                conn.commit()
            print("[AutoResearch] Added saved column to papers")
    except Exception:
        pass


def _seed_sample_papers():
    from sqlalchemy import exists
    if not SAMPLE_DATA_PATH.exists():
        return
    session = SessionLocal()
    try:
        if session.query(exists().where(Paper.source_type == "sample")).scalar():
            return
        with open(SAMPLE_DATA_PATH) as f:
            samples = json.load(f)
        count = 0
        for s in samples:
            title = (s.get("title") or "").strip()
            if not title:
                continue
            dup = session.query(exists().where(Paper.title == title)).scalar()
            if not dup:
                session.add(Paper(
                    title=title,
                    authors=s.get("authors", ""),
                    source=s.get("source", ""),
                    year=s.get("year", 2024),
                    abstract=s.get("abstract", ""),
                    content=s.get("content", s.get("abstract", "")),
                    keywords=s.get("keywords", []),
                    url=s.get("source_url", s.get("doi", "")),
                    source_type="sample",
                ))
                count += 1
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_session():
    return SessionLocal()
