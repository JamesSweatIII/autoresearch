import threading
import time
import random
from typing import List, Optional

BROAD_TOPICS = [
    "machine learning",
    "deep learning",
    "natural language processing",
    "computer vision",
    "reinforcement learning",
    "robotics",
    "neural networks",
    "transformers attention",
    "large language models",
    "graph neural networks",
    "generative adversarial networks",
    "self-supervised learning",
    "transfer learning",
    "federated learning",
    "bayesian inference",
    "causal inference",
    "optimization algorithms",
    "reinforcement learning from human feedback",
    "diffusion models",
    "representation learning",
    "multi-agent systems",
    "neural architecture search",
    "meta learning",
    "few-shot learning",
    "continual learning",
]


def pool_articles(topics: Optional[List[str]] = None, max_per_topic: int = 50, topic_fraction: float = 0.5) -> dict:
    from database.setup import SessionLocal, Paper
    from services.article_retrieval import search_openalex

    if topics is None:
        topics = list(BROAD_TOPICS)

    topic_order = list(topics)
    random.shuffle(topic_order)
    if topic_fraction < 1.0:
        n = max(1, int(len(topic_order) * topic_fraction))
        topic_order = random.sample(topic_order, n)

    total_new = 0
    total_dup = 0
    searched = []

    for topic in topic_order:
        _pooler_state["current_topic"] = topic
        print(f"[Pooler] Searching: {topic}")
        articles = search_openalex(topic, page=random.randint(1, 10))
        if not articles:
            searched.append({"topic": topic, "found": 0, "new": 0})
            _pooler_state["progress"] += 1
            continue

        sample_size = min(len(articles), max_per_topic)
        random_articles = random.sample(articles, sample_size)
        db = SessionLocal()
        try:
            saved = 0
            dup = 0
            for a in random_articles:
                if not a.title or not a.abstract:
                    continue
                existing = (
                    db.query(Paper)
                    .filter(Paper.title.ilike(a.title.strip()))
                    .first()
                )
                if existing:
                    dup += 1
                    continue
                paper = Paper(
                    title=a.title.strip(),
                    authors=", ".join(a.authors),
                    year=a.year or 2024,
                    abstract=a.abstract,
                    source=a.source or "openalex",
                    url=a.url or "",
                    source_type="pooled",
                )
                db.add(paper)
                saved += 1
            db.commit()
            total_new += saved
            total_dup += dup
            print(f"[Pooler] '{topic}': {saved} new, {dup} dup")
        except Exception as e:
            db.rollback()
            print(f"[Pooler] Error saving '{topic}': {e}")
        finally:
            db.close()

        searched.append({"topic": topic, "found": len(articles), "new": saved})
        _pooler_state["progress"] += 1
        time.sleep(1.0)

    return {
        "new_articles": total_new,
        "duplicates_skipped": total_dup,
        "topics_searched": len(searched),
        "details": searched,
    }


_pooler_state = {
    "running": False,
    "progress": 0,
    "total_topics": 0,
    "current_topic": "",
    "status": "idle",
    "result": None,
    "error": None,
}
_pooler_thread = None


def start_pooler(topics: Optional[List[str]] = None, max_per_topic: int = 50, topic_fraction: float = 0.5):
    global _pooler_thread, _pooler_state

    if _pooler_state["running"]:
        return {"error": "Pooler already running"}

    topic_list = topics if topics is not None else BROAD_TOPICS
    _pooler_state = {
        "running": True,
        "progress": 0,
        "total_topics": len(topic_list),
        "current_topic": "",
        "status": "starting",
        "result": None,
        "error": None,
        "topics": topic_list,
        "max_per_topic": max_per_topic,
        "topic_fraction": topic_fraction,
    }

    def _run():
        try:
            _pooler_state["status"] = "running"
            result = pool_articles(topics=_pooler_state["topics"], max_per_topic=_pooler_state["max_per_topic"], topic_fraction=_pooler_state["topic_fraction"])
            _pooler_state["result"] = result
            _pooler_state["status"] = "complete"
            _pooler_state["progress"] = _pooler_state["total_topics"]
        except Exception as e:
            _pooler_state["error"] = str(e)
            _pooler_state["status"] = "error"
        finally:
            _pooler_state["running"] = False

    _pooler_thread = threading.Thread(target=_run, daemon=True)
    _pooler_thread.start()
    return {"status": "started", "topics": len(topic_list)}


def get_pooler_status():
    return {k: v for k, v in _pooler_state.items() if k not in ("topics", "max_per_topic", "topic_fraction")}
