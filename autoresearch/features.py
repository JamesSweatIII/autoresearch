"""
Relational (query, document) features for the relevance model.

These features are *relational* — they describe how a query relates to a
document, not the document's vocabulary itself. That is what lets a model
trained on them generalize to queries and documents it never saw during
training (the "relate to external text" requirement).

Pure-Python / NumPy only — no sklearn — so the autoresearch trainer stays light.
"""

import re
from typing import List, Tuple

import numpy as np

FEATURE_NAMES = [
    "word_overlap",
    "title_match",
    "abstract_match",
    "bigram_overlap",
    "trigram_overlap",
    "quoted_match",
    "query_len",
    "doc_len",
    "title_individual",
    "coverage",
]

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "this", "that", "it", "its", "they", "them", "not", "no", "so", "if",
    "just", "about", "also", "been", "each", "some", "such", "only",
    "other", "more", "most", "much", "many", "into", "over", "after",
    "before", "between", "through", "during", "because", "using",
    "we", "our", "you", "your", "he", "she", "him", "her", "his", "all",
}


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", (text or "").lower())


def _ngrams(tokens: List[str], n: int) -> set:
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def _parse_quoted(topic: str) -> Tuple[List[str], str]:
    phrases = re.findall(r'"([^"]+)"', topic or "")
    rest = re.sub(r'"[^"]+"', "", topic or "").strip()
    return phrases, rest


def compute_pair_features(query: str, title: str, abstract: str) -> np.ndarray:
    """Return a fixed-length float32 feature vector for one (query, doc) pair."""
    quoted_phrases, unquoted = _parse_quoted(query)
    q_tokens = tokenize(unquoted)
    t_tokens = tokenize(title)
    a_tokens = tokenize(abstract)
    doc_tokens = t_tokens + a_tokens

    q_set, t_set, a_set, doc_set = set(q_tokens), set(t_tokens), set(a_tokens), set(doc_tokens)
    doc_text = f"{abstract} {title}".lower()

    word_overlap = len(q_set & doc_set) / max(len(q_set), 1)
    title_match = len(q_set & t_set) / max(len(q_set), 1)
    abstract_match = len(q_set & a_set) / max(len(q_set), 1)

    bigram_overlap = len(_ngrams(q_tokens, 2) & _ngrams(doc_tokens, 2)) / max(len(_ngrams(q_tokens, 2)), 1)
    trigram_overlap = len(_ngrams(q_tokens, 3) & _ngrams(doc_tokens, 3)) / max(len(_ngrams(q_tokens, 3)), 1)

    quoted_match = 0.0
    if quoted_phrases:
        quoted_match = sum(1 for p in quoted_phrases if p.lower() in doc_text) / len(quoted_phrases)

    query_len = min(len(q_tokens), 20) / 20.0
    doc_len = min(len(doc_tokens), 500) / 500.0

    title_individual = (sum(1 for qt in q_tokens if qt in t_set) / max(len(q_tokens), 1)) if t_tokens else 0.0

    required = [w for w in q_tokens if w not in _STOP_WORDS]
    coverage = (sum(1 for w in required if w in doc_set) / len(required)) if required else 0.0

    return np.array([
        word_overlap, title_match, abstract_match, bigram_overlap,
        trigram_overlap, quoted_match, query_len, doc_len,
        title_individual, coverage,
    ], dtype=np.float32)
