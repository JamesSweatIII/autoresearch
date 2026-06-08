import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
import re
import math

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ── Multi-analyzer sentiment ───────────────────────────────
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from nltk.corpus import opinion_lexicon
    _lexicon_pos = set(opinion_lexicon.positive())
    _lexicon_neg = set(opinion_lexicon.negative())
    LEXICON_AVAILABLE = True
except ImportError:
    LEXICON_AVAILABLE = False

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SAMPLE_PATH = DATA_DIR / "sample_documents.json"
BING_LEXICON_PATH = DATA_DIR / "salex_bing.csv"

# Load Bing Liu lexicon from local CSV (more complete than NLTK corpus)
_bing_pos = set()
_bing_neg = set()
if BING_LEXICON_PATH.exists():
    with open(BING_LEXICON_PATH) as f:
        lines = f.readlines()
    for line in lines[1:]:  # skip header
        parts = line.strip().split(",")
        if len(parts) >= 4:
            word = parts[0].strip().lower()
            sent = int(parts[3])
            if word:
                if sent == 1:
                    _bing_pos.add(word)
                elif sent == -1:
                    _bing_neg.add(word)
    # Merge with NLTK lexicon if available
    if LEXICON_AVAILABLE:
        _bing_pos |= _lexicon_pos
        _bing_neg |= _lexicon_neg
    LEXICON_AVAILABLE = True
    print(f"[AutoResearch] Loaded {len(_bing_pos)} positive + {len(_bing_neg)} negative sentiment words")
elif LEXICON_AVAILABLE:
    _bing_pos = _lexicon_pos
    _bing_neg = _lexicon_neg


def load_sample_documents() -> List[Dict]:
    with open(SAMPLE_PATH, "r") as f:
        return json.load(f)


def filter_documents_by_topic(docs: List[Dict], topic: str) -> List[Dict]:
    if not docs:
        return []

    abstracts = [d.get("abstract", "") for d in docs]
    titles = [d.get("title", "") for d in docs]

    scores = compute_multi_signal_relevance(abstracts, titles, topic)
    scored = list(zip(scores, docs))
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


# ── BM25 Okapi ─────────────────────────────────────────
def _bm25_tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())


def _bm25_score(
    query_terms: List[str],
    doc_terms: List[str],
    doc_len: int,
    avg_doc_len: float,
    n_docs: int,
    doc_freq: Dict[str, int],
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    score = 0.0
    for qt in query_terms:
        if qt not in doc_freq or doc_freq[qt] == 0:
            continue
        tf = doc_terms.count(qt)
        if tf == 0:
            continue
        idf = math.log((n_docs - doc_freq[qt] + 0.5) / (doc_freq[qt] + 0.5) + 1.0)
        tf_norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * doc_len / avg_doc_len))
        score += idf * tf_norm
    return score


def compute_bm25_scores(
    query: str,
    corpus: List[str],
    k1: float = 1.5,
    b: float = 0.75,
) -> List[float]:
    if not corpus:
        return []
    query_terms = _bm25_tokenize(query)
    if not query_terms:
        return [0.0] * len(corpus)

    tokenized_docs = [_bm25_tokenize(d) for d in corpus]
    doc_lengths = [float(len(t)) for t in tokenized_docs]
    avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
    n_docs = len(corpus)

    doc_freq = {}
    for qt in query_terms:
        doc_freq[qt] = sum(1 for doc_tokens in tokenized_docs if qt in doc_tokens)

    scores = []
    for i, doc_tokens in enumerate(tokenized_docs):
        s = _bm25_score(
            query_terms, doc_tokens, doc_lengths[i],
            avg_doc_len, n_docs, doc_freq, k1, b,
        )
        scores.append(s)

    if NUMPY_AVAILABLE:
        scores_arr = np.array(scores)
        if scores_arr.max() > scores_arr.min():
            scores_arr = (scores_arr - scores_arr.min()) / (scores_arr.max() - scores_arr.min())
        elif scores_arr.max() > 0:
            scores_arr = scores_arr / scores_arr.max()
        return scores_arr.tolist()

    # Pure Python fallback min-max normalize
    mn, mx = min(scores), max(scores)
    if mx > mn:
        return [(s - mn) / (mx - mn) for s in scores]
    if mx > 0:
        return [s / mx for s in scores]
    return scores


def _parse_quoted_phrases(topic: str) -> Tuple[List[str], str]:
    phrases = re.findall(r'"([^"]+)"', topic)
    rest = re.sub(r'"[^"]+"', "", topic).strip()
    return phrases, rest


def _extract_topic_ngrams(topic: str, max_n: int = 3) -> set:
    words = topic.lower().split()
    ngrams = set()
    for n in range(1, min(max_n + 1, len(words) + 1)):
        for i in range(len(words) - n + 1):
            ngrams.add(" ".join(words[i:i+n]))
    ngrams.discard("")
    return ngrams


def compute_multi_signal_relevance(
    abstracts: List[str],
    titles: List[str],
    topic: str,
) -> List[float]:
    n = len(abstracts)
    if n == 0:
        return []

    quoted_phrases, unquoted_topic = _parse_quoted_phrases(topic)
    topic_ngrams = _extract_topic_ngrams(unquoted_topic)
    for phrase in quoted_phrases:
        topic_ngrams.add(phrase.lower())

    # Required unquoted unigrams — doc must contain most of these
    _stop_words = {"the","a","an","and","or","but","in","on","at","to","for",
                   "of","with","by","from","as","is","was","are","were","be",
                   "this","that","it","its","they","them","not","no","so","if",
                   "just","about","also","been","each","some","such","only",
                   "other","more","most","much","many","into","over","after",
                   "before","between","through","during","because","using"}
    required_unigrams = [
        w for w in unquoted_topic.lower().split()
        if w not in _stop_words and len(w) > 2
    ]

    combined_texts = [a + " " + t for a, t in zip(abstracts, titles)]

    # 1. BM25 Okapi ranking
    bm25_scores = compute_bm25_scores(topic, combined_texts, k1=1.5, b=0.75)

    # Compute IDF weights for each topic n-gram across the document set
    all_texts = [a.lower() + " " + t.lower() for a, t in zip(abstracts, titles)]
    idf_weights = {}
    for ng in topic_ngrams:
        doc_count = sum(1 for text in all_texts if ng in text)
        idf_weights[ng] = math.log((n + 1) / (doc_count + 1)) + 1
        if ng.lower() in [p.lower() for p in quoted_phrases]:
            idf_weights[ng] *= 5

    quoted_lower = [p.lower() for p in quoted_phrases]

    def _coverage_ratio(text_lower: str) -> float:
        if not required_unigrams:
            return 1.0
        present = sum(1 for w in required_unigrams if w in text_lower)
        return present / len(required_unigrams)

    def _weighted_overlap(text: str) -> float:
        if not topic_ngrams:
            return 0.0
        text_lower = text.lower()
        if quoted_lower and not any(p in text_lower for p in quoted_lower):
            return 0.0
        match_weight = sum(idf_weights.get(ng, 1) for ng in topic_ngrams if ng in text_lower)
        max_weight = sum(idf_weights.values())
        base = match_weight / max_weight if max_weight > 0 else 0.0
        return base * _coverage_ratio(text_lower)

    scores = []
    for i in range(n):
        abs_overlap = _weighted_overlap(abstracts[i])
        title_overlap = _weighted_overlap(titles[i])

        combined = (
            bm25_scores[i] * 0.50 +
            abs_overlap * 0.25 +
            title_overlap * 0.25
        )
        scores.append(min(1.0, max(0.0, combined)))

    return scores


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


def analyze_sentiment_textblob(text: str) -> Tuple[str, float]:
    if TEXTBLOB_AVAILABLE:
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            if polarity >= 0.25:
                return "positive", polarity
            elif polarity <= -0.25:
                return "negative", polarity
            return "neutral", polarity
        except Exception:
            pass
    return "neutral", 0.0


def analyze_sentiment_lexicon(text: str) -> Tuple[str, float]:
    if LEXICON_AVAILABLE:
        try:
            words = re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())
            pos_count = sum(1 for w in words if w in _bing_pos)
            neg_count = sum(1 for w in words if w in _bing_neg)
            total = pos_count + neg_count
            if total == 0:
                return "neutral", 0.0
            score = (pos_count - neg_count) / total
            if score >= 0.3:
                return "positive", score
            elif score <= -0.3:
                return "negative", score
            return "neutral", score
        except Exception:
            pass
    return "neutral", 0.0


def analyze_sentiment(text: str) -> str:
    return analyze_sentiment_multi(text)["combined"]


def analyze_sentiment_multi(text: str) -> Dict[str, any]:
    tb_label, tb_score = analyze_sentiment_textblob(text)
    lex_label, lex_score = analyze_sentiment_lexicon(text)

    if tb_label == lex_label:
        combined_label = tb_label
    else:
        tb_magnitude = abs(tb_score)
        lex_magnitude = abs(lex_score)
        combined_label = tb_label if tb_magnitude >= lex_magnitude else lex_label

    return {
        "combined": combined_label,
        "textblob": {"label": tb_label, "score": round(tb_score, 4)},
        "lexicon": {"label": lex_label, "score": round(lex_score, 4)},
    }


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
