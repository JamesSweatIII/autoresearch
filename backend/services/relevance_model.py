import json
import pickle
import re
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MODEL_PATH = DATA_DIR / "relevance_model.pkl"
VECTORIZER_PATH = DATA_DIR / "relevance_vectorizer.pkl"

_STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for",
    "of","with","by","from","as","is","was","are","were","be",
    "this","that","it","its","they","them","not","no","so","if",
    "just","about","also","been","each","some","such","only",
    "other","more","most","much","many","into","over","after",
    "before","between","through","during","because","using",
    "we","our","you","your","he","she","him","her","his","all",
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())


def _extract_ngrams(tokens: List[str], max_n: int = 3) -> set:
    ngrams = set()
    for n in range(1, min(max_n + 1, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngrams.add(" ".join(tokens[i:i+n]))
    return ngrams


def _parse_quoted(topic: str) -> Tuple[List[str], str]:
    phrases = re.findall(r'"([^"]+)"', topic)
    rest = re.sub(r'"[^"]+"', "", topic).strip()
    return phrases, rest


def compute_pair_features(query: str, title: str, abstract: str) -> np.ndarray:
    quoted_phrases, unquoted = _parse_quoted(query)
    query_tokens = _tokenize(unquoted)
    title_tokens = _tokenize(title)
    abstract_tokens = _tokenize(abstract)
    all_doc_tokens = title_tokens + abstract_tokens

    query_set = set(query_tokens)
    title_set = set(title_tokens)
    abstract_set = set(abstract_tokens)
    doc_set = set(all_doc_tokens)

    query_ngrams = _extract_ngrams(query_tokens)
    doc_text = (abstract + " " + title).lower()

    # 1. Word overlap (fraction of query words in doc)
    word_overlap = len(query_set & doc_set) / max(len(query_set), 1)

    # 2. Title match (fraction of query words in title)
    title_match = len(query_set & title_set) / max(len(query_set), 1)

    # 3. Abstract match
    abstract_match = len(query_set & abstract_set) / max(len(query_set), 1)

    # 4. Bigram overlap
    query_bigrams = _extract_ngrams(query_tokens, 2)
    doc_bigrams = _extract_ngrams(all_doc_tokens, 2)
    bigram_overlap = len(query_bigrams & doc_bigrams) / max(len(query_bigrams), 1)

    # 5. Trigram overlap
    query_trigrams = _extract_ngrams(query_tokens, 3)
    doc_trigrams = _extract_ngrams(all_doc_tokens, 3)
    trigram_overlap = len(query_trigrams & doc_trigrams) / max(len(query_trigrams), 1)

    # 6. Quoted phrase match
    quoted_match = 0.0
    if quoted_phrases:
        matches = sum(1 for p in quoted_phrases if p.lower() in doc_text)
        quoted_match = matches / len(quoted_phrases)

    # 7. Query length (words)
    query_len = min(len(query_tokens), 20) / 20.0

    # 8. Doc length (tokens)
    doc_len = min(len(all_doc_tokens), 500) / 500.0

    # 9. Title has query unigrams individually
    title_individual = 0.0
    if title_tokens:
        present = sum(1 for qt in query_tokens if qt in title_set)
        title_individual = present / max(len(query_tokens), 1)

    # 10. Coverage of required unquoted unigrams
    required = [w for w in query_tokens if w not in _STOP_WORDS]
    coverage = 0.0
    if required:
        present = sum(1 for w in required if w in doc_set)
        coverage = present / len(required)

    return np.array([
        word_overlap,
        title_match,
        abstract_match,
        bigram_overlap,
        trigram_overlap,
        quoted_match,
        query_len,
        doc_len,
        title_individual,
        coverage,
    ], dtype=np.float32)


class RelevanceModel:
    def __init__(self):
        self.model: Optional[GradientBoostingRegressor] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.trained = False
        self.feature_names = [
            "word_overlap", "title_match", "abstract_match",
            "bigram_overlap", "trigram_overlap", "quoted_match",
            "query_len", "doc_len", "title_individual", "coverage",
        ]

    def _build_tfidf_feature(self, query: str, title: str, abstract: str) -> float:
        if self.vectorizer is None:
            return 0.0
        try:
            tfidf = self.vectorizer.transform([query, title + " " + abstract])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return max(0.0, min(1.0, float(sim)))
        except Exception:
            return 0.0

    def predict_one(self, query: str, title: str, abstract: str) -> float:
        if not self.trained or self.model is None:
            return 0.0
        features = compute_pair_features(query, title, abstract)
        tfidf_feat = np.array([self._build_tfidf_feature(query, title, abstract)])
        all_features = np.concatenate([features, tfidf_feat])
        pred = self.model.predict(all_features.reshape(1, -1))[0]
        return max(0.0, min(1.0, float(pred)))

    def predict_batch(
        self, queries: List[str], titles: List[str], abstracts: List[str]
    ) -> List[float]:
        if not self.trained or self.model is None:
            return [0.0] * len(queries)
        feat_list = []
        for q, t, a in zip(queries, titles, abstracts):
            feats = compute_pair_features(q, t, a)
            tfidf_f = self._build_tfidf_feature(q, t, a)
            feat_list.append(np.concatenate([feats, np.array([tfidf_f])]))
        X = np.array(feat_list)
        preds = self.model.predict(X)
        return [max(0.0, min(1.0, float(p))) for p in preds]

    def train(self, papers: List[Dict]) -> Dict:
        if len(papers) < 5:
            return {"status": "error", "message": "Need at least 5 papers to train"}

        self.vectorizer = TfidfVectorizer(
            max_features=2000, stop_words="english",
            ngram_range=(1, 3), sublinear_tf=True,
        )
        corpus = [p.get("title", "") + " " + p.get("abstract", "") for p in papers]
        self.vectorizer.fit(corpus)

        features = []
        labels = []
        n = len(papers)
        rng = np.random.RandomState(42)

        for i in range(n):
            p = papers[i]
            p_title = p.get("title", "")
            p_abstract = p.get("abstract", "")
            p_keywords = p.get("keywords", [])
            if isinstance(p_keywords, list):
                p_keywords = [str(k) for k in p_keywords if k]

            # Generate short queries from this paper
            queries = []

            # Title as query
            if p_title:
                queries.append(p_title)

            # Each keyword as query
            for kw in p_keywords[:5]:
                if len(kw.split()) <= 5:
                    queries.append(kw)

            # Random 2-4 word phrases from abstract
            abs_words = _tokenize(p_abstract)
            if len(abs_words) >= 3:
                for _ in range(3):
                    start = rng.randint(0, max(1, len(abs_words) - 2))
                    length = rng.randint(2, min(5, len(abs_words) - start + 1))
                    phrase = " ".join(abs_words[start:start+length])
                    if len(phrase) > 5:
                        queries.append(phrase)

            for query in queries:
                if not query.strip():
                    continue

                # Positive: this paper itself
                feat = compute_pair_features(query, p_title, p_abstract)
                tfidf_f = self._build_tfidf_feature(query, p_title, p_abstract)
                features.append(np.concatenate([feat, np.array([tfidf_f])]))
                labels.append(1.0)

                # Negative: sample 2 random papers
                neg_indices = rng.choice(
                    [j for j in range(n) if j != i],
                    size=min(2, n - 1), replace=False
                )
                for j in neg_indices:
                    d = papers[j]
                    feat = compute_pair_features(
                        query, d.get("title", ""), d.get("abstract", "")
                    )
                    tfidf_f = self._build_tfidf_feature(
                        query, d.get("title", ""), d.get("abstract", "")
                    )
                    features.append(np.concatenate([feat, np.array([tfidf_f])]))
                    labels.append(0.0)

                # Partial match: find papers sharing a keyword (if any)
                if p_keywords:
                    for kw in p_keywords[:2]:
                        for j in range(n):
                            if j == i:
                                continue
                            d = papers[j]
                            d_kws = d.get("keywords", [])
                            if isinstance(d_kws, list) and kw in [str(k) for k in d_kws]:
                                feat = compute_pair_features(
                                    query, d.get("title", ""), d.get("abstract", "")
                                )
                                tfidf_f = self._build_tfidf_feature(
                                    query, d.get("title", ""), d.get("abstract", "")
                                )
                                features.append(np.concatenate([feat, np.array([tfidf_f])]))
                                # Heuristic label based on overlap
                                q_tokens = set(_tokenize(query))
                                d_tokens = set(_tokenize(d.get("title","") + " " + d.get("abstract","")))
                                overlap = len(q_tokens & d_tokens) / max(len(q_tokens | d_tokens), 1)
                                label = overlap * 0.7 + tfidf_f * 0.3
                                labels.append(min(1.0, label))
                                break  # one partial per query

        X = np.array(features)
        y = np.array(labels)

        if len(X) < 10:
            return {"status": "error", "message": "Not enough training pairs"}

        self.model = GradientBoostingRegressor(
            n_estimators=200, max_depth=5,
            learning_rate=0.08, min_samples_leaf=5,
            random_state=42,
        )
        self.model.fit(X, y)
        self.trained = True

        importance = dict(zip(
            self.feature_names + ["tfidf_similarity"],
            self.model.feature_importances_
        ))

        self.save()
        return {
            "status": "ok",
            "samples": len(X),
            "papers": n,
            "feature_importance": importance,
        }

    def save(self):
        model_data = {
            "model": self.model,
            "vectorizer": self.vectorizer,
            "trained": self.trained,
        }
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        with open(VECTORIZER_PATH, "wb") as f:
            pickle.dump(self.vectorizer, f)

    def load(self) -> bool:
        if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(VECTORIZER_PATH, "rb") as f:
                    self.vectorizer = pickle.load(f)
                self.trained = True
                return True
            except Exception:
                pass
        return False

    def explain(self, query: str, title: str, abstract: str) -> Dict:
        if not self.trained or self.model is None:
            return {"error": "Model not trained"}
        features = compute_pair_features(query, title, abstract)
        tfidf_f = self._build_tfidf_feature(query, title, abstract)
        all_features = np.concatenate([features, np.array([tfidf_f])])
        pred = self.model.predict(all_features.reshape(1, -1))[0]

        contributions = {}
        for name, val, imp in zip(
            self.feature_names + ["tfidf_similarity"],
            all_features,
            self.model.feature_importances_
        ):
            contributions[name] = round(float(val * imp * 100), 2)

        return {
            "score": round(float(pred), 4),
            "contributions": dict(sorted(contributions.items(), key=lambda x: -x[1])),
        }


_model_instance: Optional[RelevanceModel] = None


def get_model() -> RelevanceModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = RelevanceModel()
        _model_instance.load()
    return _model_instance


def train_model(papers: List[Dict]) -> Dict:
    model = get_model()
    return model.train(papers)


def predict_relevance(query: str, title: str, abstract: str) -> float:
    model = get_model()
    return model.predict_one(query, title, abstract)


def batch_predict_relevance(
    queries: List[str], titles: List[str], abstracts: List[str]
) -> List[float]:
    model = get_model()
    return model.predict_batch(queries, titles, abstracts)
