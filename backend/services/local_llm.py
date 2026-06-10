import json
from typing import List, Dict, Optional

_MODEL = None


def _get_encoder():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def rank_articles(articles: List[Dict], topic: str) -> Optional[str]:
    if not articles:
        return None
    encoder = _get_encoder()
    topic_emb = encoder.encode(topic)
    results = []
    for i, a in enumerate(articles):
        text = f"{a.get('title', '')} {a.get('abstract', '') or ''}"
        if not text.strip():
            text = a.get('title', '')
        emb = encoder.encode(text)
        score = float(_cosine_sim(topic_emb, emb))
        results.append({
            "index": i + 1,
            "score": round(score, 4),
            "reasonSelected": f"Semantic similarity: {score:.3f}",
        })
    results.sort(key=lambda x: -x["score"])
    return json.dumps(results)



