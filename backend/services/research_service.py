import json
import random
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter
import re
import math

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SAMPLE_PATH = DATA_DIR / "sample_documents.json"


def load_sample_documents() -> List[Dict]:
    with open(SAMPLE_PATH, "r") as f:
        return json.load(f)


def filter_documents_by_topic(docs: List[Dict], topic: str, threshold: float = 0.05) -> List[Dict]:
    if not docs:
        return []

    texts = []
    for doc in docs:
        parts = [
            doc.get("title", ""),
            doc.get("abstract", ""),
            " ".join(doc.get("keywords", []) if isinstance(doc.get("keywords"), list) else []),
        ]
        texts.append(" ".join(p for p in parts if p))

    if SKLEARN_AVAILABLE and len(texts) > 1:
        try:
            vectorizer = TfidfVectorizer(
                max_features=2000,
                stop_words="english",
                ngram_range=(1, 3),
                sublinear_tf=True,
            )
            all_texts = [topic] + texts
            tfidf = vectorizer.fit_transform(all_texts)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

            scored = [
                (float(sim), doc)
                for sim, doc in zip(sims, docs)
            ]
            scored.sort(key=lambda x: -x[0])
            return [doc for _, doc in scored]
        except Exception:
            pass

    topic_lower = topic.lower()
    topic_terms = set(topic_lower.split())
    scored = []
    for doc in docs:
        text = (doc.get("title", "") + " " + doc.get("abstract", "") + " " +
                " ".join(doc.get("keywords", []))).lower()
        score = sum(1 for t in topic_terms if t in text)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    return [doc for _, doc in scored]


def extract_keywords(texts: List[str], top_n: int = 20) -> List[str]:
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can", "need",
        "this", "that", "these", "those", "it", "its", "they", "them", "their",
        "we", "us", "our", "you", "your", "he", "she", "him", "her", "his",
        "not", "no", "nor", "so", "if", "than", "then", "just", "about",
        "also", "very", "been", "each", "some", "such", "only", "other",
        "more", "most", "much", "many", "into", "over", "after", "before",
        "between", "through", "during", "because", "using", "among", "both",
    }
    words = []
    for text in texts:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
        words.extend(t for t in tokens if t not in stop_words and len(t) > 2)
    counter = Counter(words)
    return [word for word, _ in counter.most_common(top_n)]


def compute_relevance(text: str, topic: str) -> float:
    if SKLEARN_AVAILABLE:
        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            tfidf = vectorizer.fit_transform([topic, text])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return max(0.0, min(1.0, float(sim)))
        except Exception:
            pass
    topic_terms = set(topic.lower().split())
    text_lower = text.lower()
    matches = sum(1 for t in topic_terms if t in text_lower)
    if len(topic_terms) == 0:
        return 0.5
    return min(1.0, matches / len(topic_terms))


def batch_compute_relevance(texts: List[str], topic: str) -> List[float]:
    if SKLEARN_AVAILABLE and texts:
        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            all_texts = [topic] + texts
            tfidf = vectorizer.fit_transform(all_texts)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
            return [max(0.0, min(1.0, float(s))) for s in sims]
        except Exception:
            pass
    return [compute_relevance(t, topic) for t in texts]


def generate_summary(docs: List[Dict], keywords: List[str], topic: str) -> str:
    if not docs:
        return f"No documents found for '{topic}'. Try a different topic."

    n = len(docs)
    top_kw = ", ".join(keywords[:8])
    sources = set(d.get("source", "Unknown") for d in docs)
    years = [d.get("year", 2024) for d in docs if d.get("year")]
    yr_range = f"{min(years)}–{max(years)}" if years else "N/A"

    return (
        f"AutoResearch analyzed **{n}** documents related to **{topic}** "
        f"published between {yr_range}. "
        f"Key themes include **{top_kw}**. "
        f"Documents were sourced from {len(sources)} venues including "
        f"{', '.join(list(sources)[:4])}. "
        f"The average relevance score across all documents is "
        f"**{sum(d.get('relevance_score', 0) for d in docs) / max(n, 1):.2f}**."
    )


def detect_themes(docs: List[Dict], topic: str) -> List[str]:
    all_keywords = []
    for d in docs:
        all_keywords.extend(d.get("keywords", []))
    counter = Counter(k.lower() for k in all_keywords)
    common = [k for k, _ in counter.most_common(30)]
    clusters = []
    if any("deep learning" in k or "neural" in k for k in common):
        clusters.append("Deep Learning & Neural Networks")
    if any("reinforcement" in k for k in common):
        clusters.append("Reinforcement Learning")
    if any("nlp" in k or "language model" in k or "transformer" in k for k in common):
        clusters.append("Natural Language Processing")
    if any("computer vision" in k or "image" in k for k in common):
        clusters.append("Computer Vision")
    if any("health" in k or "medical" in k or "clinical" in k for k in common):
        clusters.append("Healthcare & Medicine")
    if any("sport" in k or "athlete" in k or "baseball" in k or "basketball" in k for k in common):
        clusters.append("Sports Analytics")
    if any("education" in k or "student" in k or "learning" in k for k in common):
        clusters.append("Education Technology")
    if any("climate" in k or "environment" in k or "sustain" in k for k in common):
        clusters.append("Climate & Sustainability")
    if any("finance" in k or "fraud" in k or "market" in k for k in common):
        clusters.append("Financial Technology")
    if any("robotic" in k or "autonom" in k for k in common):
        clusters.append("Robotics & Automation")
    if not clusters:
        clusters = ["General " + topic.title()]
    return clusters[:5]


def detect_research_gaps(docs: List[Dict], keywords: List[str]) -> List[str]:
    gaps = [
        "Longitudinal studies tracking real-world deployment over 3+ years",
        "Cross-domain transfer learning applications",
        "Ethical framework development for AI-assisted decision making",
        "Scalability analysis for production-grade systems",
        "Integration with existing legacy infrastructure",
        "User trust and adoption barriers in practice",
        "Cost-benefit analysis of implementation at scale",
        "Explainability requirements for regulated industries",
    ]
    random.shuffle(gaps)
    return gaps[:4]


def build_topic_distribution(docs: List[Dict]) -> Dict[str, int]:
    sources = {}
    for d in docs:
        src = d.get("source", "Unknown")
        sources[src] = sources.get(src, 0) + 1
    return dict(sorted(sources.items(), key=lambda x: -x[1]))


def build_keyword_frequency(texts: List[str], top_n: int = 15) -> Dict[str, int]:
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can", "need",
        "this", "that", "these", "those", "it", "its", "they", "them", "their",
        "we", "us", "our", "you", "your", "he", "she", "him", "her", "his",
        "not", "no", "nor", "so", "if", "than", "then", "just", "about",
        "also", "very", "been", "each", "some", "such", "only", "other",
        "more", "most", "much", "many", "into", "over", "after", "before",
        "between", "through", "during", "because", "using", "among", "both",
    }
    words = []
    for text in texts:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
        words.extend(t for t in tokens if t not in stop_words and len(t) > 2)
    counter = Counter(words)
    return dict(counter.most_common(top_n))


def rank_sources(docs: List[Dict]) -> List[Dict]:
    source_stats = {}
    for d in docs:
        src = d.get("source", "Unknown")
        if src not in source_stats:
            source_stats[src] = {"count": 0, "total_relevance": 0.0, "docs": []}
        source_stats[src]["count"] += 1
        source_stats[src]["total_relevance"] += d.get("relevance_score", 0)
        source_stats[src]["docs"].append(d.get("title", ""))
    rankings = []
    for src, stats in source_stats.items():
        rankings.append({
            "source": src,
            "documents": stats["count"],
            "avg_relevance": round(stats["total_relevance"] / stats["count"], 3),
            "sample_titles": stats["docs"][:3],
        })
    rankings.sort(key=lambda x: -x["avg_relevance"])
    return rankings


def analyze_sentiment(text: str) -> str:
    strong_positive = {
        "breakthrough", "outperform", "outperforms", "outperformed",
        "state-of-the-art", "state of the art", "revolutionary",
        "exceptional", "landmark", "superior", "cutting-edge",
        "highly effective", "remarkable", "milestone",
    }
    strong_negative = {
        "fail", "fails", "failed", "failure", "failures",
        "harmful", "overfit", "overfitting", "bias", "biased",
        "degrade", "degradation", "inaccurate", "incorrect",
        "poor performance", "low accuracy", "unstable",
        "erroneous", "meaningless", "worse than", "underperform",
    }
    text_lower = text.lower()
    pos_count = sum(1 for w in strong_positive if w in text_lower or w.replace("-", " ") in text_lower)
    neg_count = sum(1 for w in strong_negative if w in text_lower)
    if pos_count >= 2 and pos_count > neg_count:
        return "positive"
    if neg_count >= 2 and neg_count > pos_count:
        return "negative"
    return "neutral"


def find_similar_papers(target_id: int, all_papers: List[Dict], top_n: int = 5) -> List[Dict]:
    target = next((p for p in all_papers if p["id"] == target_id), None)
    if not target:
        return []

    others = [p for p in all_papers if p["id"] != target_id]
    if not others:
        return []

    target_text = _paper_text_for_sim(target)
    other_texts = [_paper_text_for_sim(p) for p in others]

    if SKLEARN_AVAILABLE:
        try:
            vectorizer = TfidfVectorizer(
                max_features=2000,
                stop_words="english",
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            all_texts = [target_text] + other_texts
            tfidf = vectorizer.fit_transform(all_texts)
            sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
            ranked = sorted(
                zip(sims, others),
                key=lambda x: -x[0],
            )
            return [
                {**p, "similarity_score": round(float(s), 4)}
                for s, p in ranked[:top_n]
                if s > 0.05
            ]
        except Exception:
            pass

    return _jaccard_similarity_fallback(target, others, top_n)


def _paper_text_for_sim(paper: Dict) -> str:
    parts = [
        paper.get("title", ""),
        paper.get("abstract", ""),
        " ".join(paper.get("keywords", []) if isinstance(paper.get("keywords"), list) else []),
    ]
    return " ".join(p for p in parts if p)


def _jaccard_similarity_fallback(target: Dict, others: List[Dict], top_n: int) -> List[Dict]:
    target_kw = set(
        t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", _paper_text_for_sim(target))
    )
    scored = []
    for p in others:
        other_kw = set(
            t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", _paper_text_for_sim(p))
        )
        if not target_kw or not other_kw:
            continue
        intersection = target_kw & other_kw
        union = target_kw | other_kw
        score = len(intersection) / len(union) if union else 0
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [
        {**p, "similarity_score": round(float(s), 4)}
        for s, p in scored[:top_n]
    ]
