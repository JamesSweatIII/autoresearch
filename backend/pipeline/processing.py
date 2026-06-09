import time
import re
from typing import List, Dict, Optional
from collections import Counter
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import udf, col, explode, split, lower, count
    from pyspark.sql.types import StringType, FloatType, ArrayType
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

try:
    from py4j.protocol import Py4JNetworkError
    PY4J_AVAILABLE = True
except ImportError:
    PY4J_AVAILABLE = False

from sqlalchemy import func
from database.setup import get_session, ResearchJob, Document, Paper, init_db
from services.research_service import (
    filter_documents_by_topic, extract_keywords,
    compute_multi_signal_relevance, compute_relevance,
    generate_summary, detect_themes, detect_research_gaps,
    build_topic_distribution, build_keyword_frequency, rank_sources,
    analyze_sentiment_multi,
)
from services.web_search_service import search_web_papers
from services.llm_relevance import LLMRelevanceFilter


class ResearchPipeline:
    STAGES = [
        ("ingesting", "Ingesting research documents from data sources"),
        ("processing", "Processing and cleaning text data"),
        ("analyzing", "Running NLP analysis and keyword extraction"),
        ("summarizing", "Generating summaries and detecting themes"),
        ("storing", "Storing results and building dashboard data"),
    ]

    def __init__(self):
        init_db()

    def _get_spark(self):
        if not SPARK_AVAILABLE:
            return None
        try:
            return (SparkSession.builder
                    .appName("AutoResearch")
                    .master("local[*]")
                    .config("spark.driver.memory", "2g")
                    .config("spark.ui.showConsoleProgress", "false")
                    .getOrCreate())
        except Exception as e:
            print(f"[AutoResearch] PySpark unavailable (no Java runtime?): {e}")
            return None

    def run_pipeline(self, job_id: int, topic: str,
                     progress_callback=None) -> Dict:
        db = get_session()
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        start_time = time.time()
        spark = self._get_spark()

        try:
            # Stage 1: Search the web FIRST — primary data source
            job.status = "ingesting"
            db.commit()
            self._report_progress(progress_callback, 0, "ingesting",
                                  "Searching the web for relevant papers...")

            web_papers = search_web_papers(topic, max_results=80)

            # Load all known papers from the database (includes seeded samples + previous web results)
            existing_urls = set()
            existing_titles = set()
            known_docs = []
            for p in db.query(Paper).all():
                known_docs.append({
                    "title": p.title,
                    "authors": p.authors or "",
                    "source": p.source or "",
                    "year": p.year or 2024,
                    "abstract": p.abstract or "",
                    "content": p.content or "",
                    "keywords": p.keywords or [],
                    "url": p.url or "",
                    "source_type": p.source_type or "sample",
                })
                if p.url:
                    existing_urls.add(p.url.rstrip("/").lower())
                if p.title:
                    existing_titles.add(p.title.strip().lower())

            self._report_progress(progress_callback, 0.08, "ingesting",
                                  f"Loaded {len(known_docs)} papers from database")

            # Store new web papers in Papers table (skip dups by URL + title)
            new_web_papers = []
            for wp in web_papers:
                wp_url = wp.get("url", "").rstrip("/").lower()
                wp_title = wp.get("title", "").strip().lower()
                if not wp_title:
                    continue
                is_dup = bool(wp_url and wp_url in existing_urls) or bool(wp_title and wp_title in existing_titles)
                if not is_dup:
                    if wp_url:
                        existing_urls.add(wp_url)
                    if wp_title:
                        existing_titles.add(wp_title)
                    new_web_papers.append(wp)
                    try:
                        db.add(Paper(
                            title=wp_title,
                            authors=wp.get("authors", ""),
                            source=wp.get("source", "Web"),
                            year=wp.get("year", 2024),
                            abstract=wp.get("abstract", wp.get("content", "")),
                            content=wp.get("content", ""),
                            keywords=wp.get("keywords", []),
                            url=wp.get("url", ""),
                            source_type="web",
                        ))
                        db.commit()
                    except Exception:
                        db.rollback()

            self._report_progress(progress_callback, 0.15, "ingesting",
                                  f"Found {len(new_web_papers)} new papers from the web")

            # Merge known + web docs (web first = primary)
            all_docs = new_web_papers + known_docs
            job.web_results_count = len(new_web_papers)

            # Stage 2: Filter by topic relevance
            matched = filter_documents_by_topic(all_docs, topic)
            if not matched:
                matched = all_docs[:20]
            job.status = "processing"
            db.commit()
            self._report_progress(progress_callback, 0.30, "processing",
                                  f"Found {len(matched)} relevant documents ({len(new_web_papers)} from web)")

            # If Spark is available, use it for distributed processing
            if spark:
                processed = self._spark_processing(spark, matched, topic)
            else:
                processed = self._local_processing(matched, topic)

            # Stage 3: Analyze
            job.status = "analyzing"
            db.commit()
            self._report_progress(progress_callback, 0.50, "analyzing",
                                  "Extracting keywords and computing scores")

            all_texts = [d.get("abstract", "") + " " + d.get("title", "")
                         for d in processed]
            keywords = extract_keywords(all_texts)
            keyword_freq = build_keyword_frequency(all_texts)
            topic_dist = build_topic_distribution(processed)
            source_rankings = rank_sources(processed)

            # Relevance scoring
            abs_texts = [d.get("abstract", "") for d in processed]
            title_texts = [d.get("title", "") for d in processed]
            relevance_scores = compute_multi_signal_relevance(abs_texts, title_texts, topic)

            for d, score in zip(processed, relevance_scores):
                d["relevance_score"] = round(score, 3)
                sentiment_result = analyze_sentiment_multi(
                    d.get("abstract", "") + " " + d.get("title", "")
                )
                d["sentiment"] = sentiment_result["combined"]
                d["sentiment_scores"] = sentiment_result

            processed.sort(key=lambda x: -x.get("relevance_score", 0))

            # Apply relevance threshold — only keep the best articles
            RELEVANCE_THRESHOLD = 0.03  # TF-IDF cosine similarity floor
            MIN_KEEP = 30               # always keep at least this many
            above_bar = [d for d in processed if d.get("relevance_score", 0) >= RELEVANCE_THRESHOLD]
            if len(above_bar) >= MIN_KEEP:
                processed = above_bar
            else:
                processed = processed[:MIN_KEEP]
            self._report_progress(progress_callback, 0.45, "analyzing",
                                  f"Keeping {len(processed)} documents above relevance threshold ({RELEVANCE_THRESHOLD})")

            # LLM relevance verification — filters out false positives from top docs
            if processed:
                self._report_progress(progress_callback, 0.50, "analyzing",
                                      f"Verifying top documents with LLM relevance model...")
                llm_filter = LLMRelevanceFilter()
                processed = llm_filter.filter_top_documents(topic, processed, top_n=10, progress_callback=progress_callback)
                verified_count = sum(1 for d in processed if d.get("llm_verified"))
                self._report_progress(progress_callback, 0.60, "analyzing",
                                      f"LLM verification complete: {verified_count} verified relevant")

            # Persist ALL discovered documents into Papers table
            papers_saved = 0
            for d in processed:
                raw_title = (d.get("title") or "").strip()
                if not raw_title:
                    continue
                d_title = re.sub(r'\s+', ' ', raw_title)
                d_title_lower = d_title.lower()
                dup = bool(db.query(Paper).filter(func.lower(Paper.title) == d_title_lower).first())
                if not dup:
                    d_url = (d.get("url") or "").rstrip("/").strip()
                    if d_url:
                        dup = bool(db.query(Paper).filter(Paper.url == d_url).first())
                if not dup:
                    try:
                        db.add(Paper(
                            title=d_title,
                            authors=d.get("authors", ""),
                            source=d.get("source", ""),
                            year=d.get("year", 2024),
                            abstract=d.get("abstract", ""),
                            content=d.get("content", d.get("abstract", "")),
                            keywords=d.get("keywords", []),
                            url=d.get("url", ""),
                            source_type=d.get("source_type", "sample"),
                        ))
                        db.commit()
                        papers_saved += 1
                    except Exception:
                        db.rollback()

            if papers_saved > 0:
                self._report_progress(progress_callback, 0.70, "storing",
                                      f"Saved {papers_saved} new papers to database")

            # Stage 4: Summarize
            job.status = "summarizing"
            db.commit()
            self._report_progress(progress_callback, 0.75, "summarizing",
                                  "Generating executive summary and themes")

            summary = generate_summary(processed, keywords, topic)
            themes = detect_themes(processed, topic)
            gaps = detect_research_gaps(processed, keywords)
            avg_rel = sum(d.get("relevance_score", 0) for d in processed) / max(len(processed), 1)
            top_src = source_rankings[0]["source"] if source_rankings else ""

            elapsed = time.time() - start_time

            # Build paper_id lookup by title
            paper_lookup = {}
            for p in db.query(Paper).all():
                key = (p.title or "").strip().lower()
                if key:
                    paper_lookup[key] = p.id

            # Store documents for this job
            for d in processed[:100]:
                doc_title = (d.get("title", "") or "").strip()
                doc = Document(
                    job_id=job_id,
                    paper_id=paper_lookup.get(doc_title.lower()),
                    title=doc_title or "Untitled",
                    authors=d.get("authors", ""),
                    source=d.get("source", ""),
                    year=d.get("year", 2024),
                    abstract=d.get("abstract", ""),
                    content=d.get("content", d.get("abstract", "")),
                    keywords=d.get("keywords", []),
                    relevance_score=d.get("relevance_score", 0),
                    sentiment=d.get("sentiment", "neutral"),
                    sentiment_scores=d.get("sentiment_scores", {}),
                    topic_cluster=themes[0] if themes else "",
                    source_type=d.get("source_type", "sample"),
                    url=d.get("url", ""),
                    llm_verified=1 if d.get("llm_verified") else 0,
                )
                db.add(doc)

            # Update job
            job.status = "completed"
            job.documents_count = len(processed)
            job.top_keywords = keywords[:15]
            job.avg_relevance = round(avg_rel, 3)
            job.top_source = top_src
            job.processing_time = round(elapsed, 2)
            job.summary = summary
            job.themes = themes
            job.research_gaps = gaps
            job.topic_distribution = topic_dist
            job.keyword_frequency = keyword_freq
            job.source_rankings = source_rankings
            job.sentiment_distribution = dict(
                Counter(d.get("sentiment", "neutral") for d in processed)
            )
            db.commit()

            self._report_progress(progress_callback, 1.0, "storing",
                                  "Research complete!")

            return self._build_result(job, processed)

        except Exception as e:
            job.status = "failed"
            db.commit()
            raise e
        finally:
            if spark:
                spark.stop()
            db.close()

    def _spark_processing(self, spark, docs: List[Dict], topic: str) -> List[Dict]:
        df = spark.createDataFrame(docs)
        processed = df.collect()
        return [row.asDict() for row in processed]

    def _local_processing(self, docs: List[Dict], topic: str) -> List[Dict]:
        for doc in docs:
            doc["word_count"] = len(doc.get("abstract", "").split())
        return docs

    def _report_progress(self, callback, progress, stage, message):
        if callback:
            callback({"progress": progress, "stage": stage, "message": message})

    def _build_result(self, job, processed) -> Dict:
        return {
            "id": job.id,
            "topic": job.topic,
            "status": job.status,
            "documents_count": job.documents_count,
            "top_keywords": job.top_keywords,
            "avg_relevance": job.avg_relevance,
            "top_source": job.top_source,
            "processing_time": job.processing_time,
            "summary": job.summary,
            "themes": job.themes,
            "research_gaps": job.research_gaps,
            "topic_distribution": job.topic_distribution,
            "keyword_frequency": job.keyword_frequency,
            "source_rankings": job.source_rankings,
            "web_results_count": job.web_results_count or 0,
        }
