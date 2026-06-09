"""LLM-based relevance verification using Qwen2.5 via ollama."""

import json
import hashlib
import time
from typing import List, Dict, Optional, Callable
import urllib.request

OLLAMA_BASE = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"


class LLMRelevanceFilter:
    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model
        self._cache: Dict[str, bool] = {}
        self._stats = {"total": 0, "cached": 0, "relevant": 0, "not_relevant": 0}

    def _cache_key(self, topic: str, title: str) -> str:
        raw = f"{topic.lower().strip()}||{title.lower().strip()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _query_llm(self, prompt: str) -> str:
        data = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 10},
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        return result.get("response", "")

    def judge_relevance(self, topic: str, title: str, abstract: str) -> bool:
        key = self._cache_key(topic, title)
        if key in self._cache:
            self._stats["cached"] += 1
            return self._cache[key]

        self._stats["total"] += 1
        start = time.time()

        prompt = (
            f"Research Topic: {topic}\n\n"
            f"Paper Title: {title}\n"
            f"Paper Abstract: {abstract[:500]}\n\n"
            f"Question: Is this paper directly relevant to the research topic?\n"
            f"Answer with exactly one word: YES or NO."
        )

        response = self._query_llm(prompt)
        is_relevant = response.strip().upper().startswith("YES")

        elapsed = time.time() - start
        print(f"[LLM] {'REL' if is_relevant else 'NOT'} ({elapsed:.1f}s) {title[:60]}")

        self._cache[key] = is_relevant
        if is_relevant:
            self._stats["relevant"] += 1
        else:
            self._stats["not_relevant"] += 1
        return is_relevant

    def filter_top_documents(
        self, topic: str, documents: List[Dict],
        top_n: int = 10,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict]:
        if not documents:
            return []

        llm_candidates = documents[:top_n]
        rest = documents[top_n:]

        for i, doc in enumerate(llm_candidates):
            if progress_callback:
                progress_callback({
                    "progress": 0.30 + 0.15 * ((i + 1) / len(llm_candidates)),
                    "stage": "analyzing",
                    "message": f"LLM relevance: {i + 1}/{len(llm_candidates)}",
                })
            try:
                is_rel = self.judge_relevance(
                    topic, doc.get("title", ""), doc.get("abstract", "")
                )
            except Exception as e:
                print(f"[LLM] Error judging doc: {e}")
                is_rel = True
            doc["llm_verified"] = is_rel

        if progress_callback:
            progress_callback({
                "progress": 0.45,
                "stage": "analyzing",
                "message": f"LLM relevance verification complete for {len(llm_candidates)} documents",
            })

        kept = [d for d in llm_candidates if d.get("llm_verified")]
        removed = len(llm_candidates) - len(kept)
        if removed:
            print(f"[LLM] Removed {removed}/{len(llm_candidates)} top docs as not relevant")
        return kept + rest

    def get_stats(self) -> Dict:
        return {**self._stats}
