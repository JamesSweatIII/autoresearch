import re
import urllib.parse
import os
import time
from typing import List, Dict, Optional, Callable
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup


# ── Config ──────────────────────────────────────────────────
ACTIVE_BACKEND = os.environ.get("AUTORESEARCH_SEARCH_BACKEND", "all")


# ── Shared helpers ──────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}

_LAST_API_CALL = 0


def _rate_limited_request(url: str, headers: dict = None, timeout: int = 10, method: str = "GET", json_data: dict = None) -> Optional[requests.Response]:
    global _LAST_API_CALL
    now = time.time()
    elapsed = now - _LAST_API_CALL
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    try:
        if method == "POST" and json_data:
            resp = requests.post(url, json=json_data, headers=headers or HEADERS, timeout=timeout)
        else:
            resp = requests.get(url, headers=headers or HEADERS, timeout=timeout)
        _LAST_API_CALL = time.time()
        if resp.status_code == 429:
            time.sleep(3)
            if method == "POST" and json_data:
                resp = requests.post(url, json=json_data, headers=headers or HEADERS, timeout=timeout)
            else:
                resp = requests.get(url, headers=headers or HEADERS, timeout=timeout)
            _LAST_API_CALL = time.time()
        return resp
    except Exception:
        return None

STOP_WORDS = {
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
    "new", "based", "novel", "using", "large", "high", "different",
}


def _extract_source(url: str) -> str:
    domain = urllib.parse.urlparse(url).netloc.lower()
    domain_map = {
        "arxiv.org": "arXiv",
        "scholar.google.com": "Google Scholar",
        "semanticscholar.org": "Semantic Scholar",
        "researchgate.net": "ResearchGate",
        "aclanthology.org": "ACL",
        "springer.com": "Springer",
        "link.springer.com": "Springer",
        "ieeexplore.ieee.org": "IEEE",
        "dl.acm.org": "ACM",
        "pubmed.ncbi.nlm.nih.gov": "PubMed",
        "ncbi.nlm.nih.gov": "PubMed Central",
        "openreview.net": "OpenReview",
        "papers.nips.cc": "NeurIPS",
        "proceedings.mlr.press": "PMLR",
        "jmlr.org": "JMLR",
        "wikipedia.org": "Wikipedia",
        "github.com": "GitHub",
        "bing.com": "Bing",
        "duckduckgo.com": "DuckDuckGo",
    }
    for key, val in domain_map.items():
        if key in domain:
            return val
    parts = domain.split(".")
    return parts[-2].title() if len(parts) >= 2 else domain


def _extract_year(text: str, snippet: str) -> int:
    combined = text + " " + snippet
    years = re.findall(r'\b(19[0-9]{2}|20[0-9]{2})\b', combined)
    if years:
        valid = [int(y) for y in years if 1950 <= int(y) <= 2026]
        if valid:
            counter = Counter(valid)
            return counter.most_common(1)[0][0]
    return 2024


def _extract_keywords_from_text(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    counter = Counter(tokens)
    return [w for w, _ in counter.most_common(10)]


def _clean_title(title: str) -> str:
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.rstrip('.')
    suffixes = [
        r'\s*\|.*$', r'\s*\- YouTube$', r'\s*\.pdf$', r'\s*– arXiv.*$',
        r'\s*\| arXiv.*$', r'\s*\[PDF\].*$', r'\s*– Semantic Scholar.*$',
        r'\s*\(PDF\).*$', r'\s*\|.*ResearchGate.*$', r'\s*\| SpringerLink.*$',
        r'\s*on .*ResearchGate$', r'\s*\| .*$',
    ]
    for s in suffixes:
        title = re.sub(s, '', title, flags=re.IGNORECASE)
    return title.strip()


def _paper_from_meta(title: str, snippet: str, url: str) -> Dict:
    return {
        "title": _clean_title(title),
        "abstract": snippet,
        "authors": "",
        "source": _extract_source(url),
        "year": _extract_year(title, snippet),
        "keywords": _extract_keywords_from_text(title + " " + snippet),
        "url": url,
        "content": snippet,
        "source_type": "web",
    }


def _enrich_with_arxiv(paper: Dict) -> Dict:
    arxiv_id = _parse_arxiv_id(paper["url"])
    if arxiv_id:
        meta = _fetch_arxiv_meta(arxiv_id)
        if meta:
            paper.update(meta)
            paper["source"] = "arXiv"
            paper["url"] = f"https://arxiv.org/abs/{arxiv_id}"
            paper["source_type"] = "web"
    return paper


def _enrich_via_semantic_scholar(paper: Dict) -> Dict:
    if paper.get("source") == "Semantic Scholar" or not paper.get("title"):
        return paper
    if paper.get("authors"):
        return paper
    try:
        title = paper["title"]
        params = {"query": title, "limit": "1", "fields": "title,year,authors,venue,citationCount"}
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urllib.parse.urlencode(params)}"
        resp = _rate_limited_request(url, timeout=5)
        if resp and resp.status_code == 200:
            data = resp.json()
            matches = data.get("data", [])
            if matches:
                m = matches[0]
                authors = ", ".join(a.get("name", "") for a in (m.get("authors") or []))
                if authors:
                    paper["authors"] = authors
                if m.get("year"):
                    paper["year"] = m["year"]
                if m.get("venue"):
                    paper["source"] = m["venue"]
    except Exception:
        pass
    return paper


def _parse_arxiv_id(url: str) -> Optional[str]:
    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)',
        r'arxiv\.org/(?:abs|pdf)/([a-z\-]+/\d+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def _fetch_arxiv_meta(arxiv_id: str) -> Optional[Dict]:
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
        resp = _rate_limited_request(url, timeout=5)
        if not resp or resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "xml")
        entry = soup.find("entry")
        if not entry:
            return None
        title = entry.find("title")
        abstract = entry.find("summary")
        authors = []
        for a in entry.find_all("author"):
            name = a.find("name")
            if name:
                authors.append(name.text)
        categories = [cat.get("term", "") for cat in entry.find_all("category") if cat.get("term")]
        published = entry.find("published")
        year = 2024
        if published:
            ym = re.match(r'(\d{4})', published.text)
            if ym:
                year = int(ym.group(1))
        return {
            "title": title.text.strip() if title else "",
            "abstract": abstract.text.strip() if abstract else "",
            "authors": ", ".join(authors),
            "year": year,
            "keywords": categories or [],
        }
    except Exception:
        return None


# ── Search backends ────────────────────────────────────────

def _search_arxiv(topic: str, max_results: int) -> List[Dict]:
    papers = []
    seen_titles = set()
    queries = [topic]
    words = topic.split()
    if len(words) > 3:
        queries.append(" ".join(words[:3]))
    for query in queries:
        if len(papers) >= max_results:
            break
        try:
            params = urllib.parse.urlencode({
                "search_query": f"all:{query}",
                "start": "0",
                "max_results": str(min(max_results * 2, 50)),
            })
            url = f"http://export.arxiv.org/api/query?{params}"
            resp = _rate_limited_request(url, timeout=15)
            if not resp or resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "xml")
            for entry in soup.find_all("entry"):
                if len(papers) >= max_results:
                    break
                title = entry.find("title")
                abstract = entry.find("summary")
                aid = entry.find("id")
                url_text = aid.text.strip() if aid else ""
                arxiv_id = _parse_arxiv_id(url_text) if url_text else None
                if not arxiv_id:
                    continue
                paper_title = _clean_title(title.text.strip() if title else "")
                if paper_title.lower() in seen_titles:
                    continue
                seen_titles.add(paper_title.lower())
                authors = [a.find("name").text for a in entry.find_all("author") if a.find("name")]
                categories = [cat.get("term", "") for cat in entry.find_all("category") if cat.get("term")]
                published = entry.find("published")
                year = 2024
                if published:
                    ym = __import__("re").match(r"(\d{4})", published.text)
                    if ym:
                        year = int(ym.group(1))
                papers.append({
                    "title": paper_title,
                    "abstract": abstract.text.strip() if abstract else "",
                    "authors": ", ".join(authors),
                    "source": "arXiv",
                    "year": year,
                    "keywords": [c for c in categories if c],
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "content": abstract.text.strip() if abstract else "",
                    "source_type": "web",
                })
        except Exception as e:
            print(f"[AutoResearch Web] arXiv search failed: {e}")
    return papers[:max_results]


def _search_crossref(topic: str, max_results: int) -> List[Dict]:
    papers = []
    seen_titles = set()
    queries = [topic]
    words = topic.split()
    if len(words) > 3:
        queries.append(" ".join(words[:3]))
    for query in queries:
        if len(papers) >= max_results:
            break
        try:
            params = urllib.parse.urlencode({
                "query": query,
                "rows": str(min(max_results * 2, 50)),
                "select": "DOI,title,author,abstract,container-title,published-print,issued",
            })
            url = f"https://api.crossref.org/works?{params}"
            resp = _rate_limited_request(url, timeout=10)
            if not resp or resp.status_code != 200:
                continue
            data = resp.json()
            for item in data.get("message", {}).get("items", []):
                if len(papers) >= max_results:
                    break
                titles = item.get("title", [])
                if not titles or not titles[0]:
                    continue
                title = _clean_title(titles[0])
                if title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())
                authors = ", ".join(
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in (item.get("author") or [])
                )
                issued = item.get("issued") or item.get("published-print") or {}
                date_parts = (issued.get("date-parts") or [[None]])[0]
                year = date_parts[0] if date_parts and date_parts[0] else 2024
                abstract = item.get("abstract", "").replace("<jats:p>", "").replace("</jats:p>", "").replace("<p>", "").replace("</p>", "")
                doi = item.get("DOI", "")
                papers.append({
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "source": item.get("container-title", [""])[0] if item.get("container-title") else "CrossRef",
                    "year": int(year) if year else 2024,
                    "keywords": [],
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "content": abstract,
                    "source_type": "web",
                })
        except Exception as e:
            print(f"[AutoResearch Web] Crossref search failed: {e}")
    return papers[:max_results]



def _search_semantic_scholar(topic: str, max_results: int) -> List[Dict]:
    papers = []
    try:
        params = {"query": topic, "limit": str(min(max_results * 2, 50)), "fields": "title,year,authors,venue,citationCount,tldr"}
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urllib.parse.urlencode(params)}"
        resp = _rate_limited_request(url, timeout=10)
        if not resp or resp.status_code != 200:
            return papers
        data = resp.json()
        for item in data.get("data", []):
            if len(papers) >= max_results:
                break
            paper_id = item.get("paperId", "")
            papers.append({
                "title": _clean_title(item.get("title", "")),
                "abstract": "",
                "authors": ", ".join(a.get("name", "") for a in (item.get("authors") or [])),
                "source": item.get("venue") or "Semantic Scholar",
                "year": item.get("year", 2024),
                "keywords": [],
                "url": f"https://www.semanticscholar.org/paper/{paper_id}",
                "content": "",
                "source_type": "web",
            })
        # Batch-fetch abstracts for richer results
        if papers:
            paper_ids = [p["url"].split("/")[-1] for p in papers]
            batch_url = f"https://api.semanticscholar.org/graph/v1/paper/batch?{urllib.parse.urlencode({'fields': 'title,abstract,authors,year,venue,citationCount'})}"
            batch_resp = _rate_limited_request(batch_url, method="POST", json_data={"ids": paper_ids}, timeout=10)
            if batch_resp and batch_resp.status_code == 200:
                batch_data = batch_resp.json()
                for i, bp in enumerate(batch_data):
                    if bp and i < len(papers):
                        papers[i]["abstract"] = bp.get("abstract") or ""
                        if bp.get("venue"):
                            papers[i]["source"] = bp["venue"]
                        papers[i]["keywords"] = _extract_keywords_from_text(
                            papers[i]["title"] + " " + papers[i]["abstract"]
                        )
    except Exception as e:
        print(f"[AutoResearch Web] Semantic Scholar search failed: {e}")
    return papers[:max_results]


def _search_google_scholar(topic: str, max_results: int) -> List[Dict]:
    papers = []
    seen_urls = set()
    query = topic
    try:
        params = {"q": query, "hl": "en", "as_ylo": "2018"}
        url = f"https://scholar.google.com/scholar?{urllib.parse.urlencode(params)}"
        resp = requests.get(url, headers={**HEADERS, "Accept-Language": "en-US,en;q=0.9"}, timeout=10)
        if resp.status_code != 200:
            return papers
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select(".gs_r.gs_or.gs_scl"):
            if len(papers) >= max_results:
                break
            a = row.select_one(".gs_rt a")
            if not a:
                continue
            href = a.get("href", "")
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            snippet_el = row.select_one(".gs_rs")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            author_el = row.select_one(".gs_a")
            authors = author_el.get_text(strip=True) if author_el else ""
            paper = _paper_from_meta(title, snippet, href)
            paper["authors"] = authors.split("-")[0].strip() if "-" in authors else authors
            paper = _enrich_with_arxiv(paper)
            paper = _enrich_via_semantic_scholar(paper)
            papers.append(paper)
    except Exception as e:
        print(f"[AutoResearch Web] Google Scholar search failed: {e}")
    return papers[:max_results]


# ── Registry ────────────────────────────────────────────────

BACKENDS = {
    "arxiv": {
        "name": "arXiv",
        "description": "arXiv API — open-access scholarly papers, no API key needed",
        "search": _search_arxiv,
    },
    "crossref": {
        "name": "Crossref",
        "description": "Crossref API — DOI metadata for published research, generous rate limits",
        "search": _search_crossref,
    },
    "semantic_scholar": {
        "name": "Semantic Scholar",
        "description": "Academic paper API — structured metadata, no API key needed",
        "search": _search_semantic_scholar,
    },
    "google_scholar": {
        "name": "Google Scholar",
        "description": "Google Scholar — HTML scraping, may be rate-limited",
        "search": _search_google_scholar,
    },
}


def get_active_backend() -> str:
    return ACTIVE_BACKEND


def set_active_backend(name: str):
    global ACTIVE_BACKEND
    if name in BACKENDS or name == "all":
        ACTIVE_BACKEND = name


def list_backends() -> List[Dict]:
    engines = [
        {"id": "all", "name": "All Engines",
         "description": "Query every search engine in parallel, merge & deduplicate",
         "active": ACTIVE_BACKEND == "all"},
    ]
    engines += [
        {"id": k, "name": v["name"], "description": v["description"], "active": k == ACTIVE_BACKEND}
        for k, v in BACKENDS.items()
    ]
    return engines


def search_web_papers(topic: str, max_results: int = 15, backend: Optional[str] = None) -> List[Dict]:
    engine = backend or ACTIVE_BACKEND

    if engine == "all":
        return _search_all_backends(topic, max_results)

    backend_info = BACKENDS.get(engine)
    if not backend_info:
        print(f"[AutoResearch Web] Unknown backend '{engine}', falling back to duckduckgo")
        backend_info = BACKENDS["duckduckgo"]
    print(f"[AutoResearch Web] Searching via {backend_info['name']}...")
    return backend_info["search"](topic, max_results)


def _search_all_backends(topic: str, max_results: int) -> List[Dict]:
    per_backend = max(max_results, 15)
    seen_urls = set()
    merged = []

    print(f"[AutoResearch Web] Searching ALL backends in parallel...")

    with ThreadPoolExecutor(max_workers=len(BACKENDS)) as pool:
        fut_to_name = {
            pool.submit(info["search"], topic, per_backend): name
            for name, info in BACKENDS.items()
        }
        for fut in as_completed(fut_to_name):
            name = fut_to_name[fut]
            try:
                results = fut.result()
                print(f"[AutoResearch Web] {name} returned {len(results)} results")
                for p in results:
                    url = (p.get("url") or "").rstrip("/").lower()
                    title = (p.get("title") or "").strip().lower()
                    dedup_key = url or title
                    if dedup_key and dedup_key not in seen_urls:
                        seen_urls.add(dedup_key)
                        merged.append(p)
            except Exception as e:
                print(f"[AutoResearch Web] {name} failed: {e}")

    # Stable sort: prefer results with abstracts (richer data) then by keyword count
    merged.sort(key=lambda p: (
        1 if p.get("abstract") else 0,
        len(p.get("keywords") or []),
    ), reverse=True)

    print(f"[AutoResearch Web] Merged {len(merged)} unique results from all backends")
    return merged[:max_results]



