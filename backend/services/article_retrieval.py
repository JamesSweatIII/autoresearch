import re
import json
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

import time
_LAST_API_CALL = 0


def _get(url: str, timeout: int = 15):
    global _LAST_API_CALL
    now = time.time()
    if now - _LAST_API_CALL < 0.5:
        time.sleep(0.5 - (now - _LAST_API_CALL))
    _LAST_API_CALL = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 429:
            time.sleep(3)
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
        return resp
    except Exception:
        return None


@dataclass
class ResearchArticle:
    id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: Optional[str] = None
    source: str = ""
    url: Optional[str] = None
    doi: Optional[str] = None
    citationCount: Optional[int] = None
    relevanceScore: Optional[float] = None
    reasonSelected: Optional[str] = None


def search_semantic_scholar(query: str) -> List[ResearchArticle]:
    articles = []
    try:
        params = {
            "query": query,
            "limit": "20",
            "fields": "title,year,authors,venue,citationCount,externalIds,abstract",
        }
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{urllib.parse.urlencode(params)}"
        resp = _get(url)
        if not resp or resp.status_code != 200:
            return articles
        for item in (resp.json().get("data") or []):
            authors = [a.get("name", "") for a in (item.get("authors") or []) if a.get("name")]
            doi = (item.get("externalIds") or {}).get("DOI", "")
            articles.append(ResearchArticle(
                id=f"ss_{item.get('paperId', '')}",
                title=item.get("title", ""),
                authors=authors,
                year=item.get("year"),
                abstract=item.get("abstract"),
                source="semantic_scholar",
                url=f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                doi=doi or None,
                citationCount=item.get("citationCount"),
            ))
    except Exception as e:
        print(f"[AR] Semantic Scholar error: {e}")
    return articles


def search_openalex(query: str, page: int = 1) -> List[ResearchArticle]:
    articles = []
    try:
        params = {"search": query, "per-page": "20", "sort": "relevance_score:desc",
                   "select": "id,title,authorships,publication_year,abstract_inverted_index,cited_by_count,doi",
                   "page": str(page)}
        url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        resp = _get(url)
        if not resp or resp.status_code != 200:
            return articles
        for item in (resp.json().get("results") or []):
            title = (item.get("title") or "").strip()
            if not title:
                continue
            authors = []
            for a in (item.get("authorships") or []):
                name = (a.get("author") or {}).get("display_name", "")
                if name:
                    authors.append(name)
            abstract = ""
            inv = item.get("abstract_inverted_index")
            if inv:
                wpos = {}
                for word, positions in inv.items():
                    for pos in positions:
                        wpos[pos] = word
                if wpos:
                    abstract = " ".join(wpos[i] for i in sorted(wpos))
            articles.append(ResearchArticle(
                id=f"oa_{item.get('id', '').split('/')[-1]}",
                title=title, authors=authors,
                year=item.get("publication_year"),
                abstract=abstract or None, source="openalex",
                url=item.get("id") or None,
                doi=item.get("doi", "").replace("https://doi.org/", "") if item.get("doi") else None,
                citationCount=item.get("cited_by_count"),
            ))
    except Exception as e:
        print(f"[AR] OpenAlex error: {e}")
    return articles


def search_arxiv(query: str) -> List[ResearchArticle]:
    articles = []
    try:
        url = f"http://export.arxiv.org/api/query?{urllib.parse.urlencode({'search_query': f'all:{query}', 'start': '0', 'max_results': '30'})}"
        resp = _get(url, timeout=20)
        if not resp or resp.status_code != 200:
            return articles
        soup = BeautifulSoup(resp.text, "xml")
        for entry in soup.find_all("entry"):
            title_el = entry.find("title")
            abstract_el = entry.find("summary")
            aid = entry.find("id")
            url_text = aid.text.strip() if aid is not None else ""
            m = re.search(r'(?:abs|pdf)/(\d+\.\d+|[a-z\-]+/\d+)', url_text)
            if not m:
                continue
            arxiv_id = m.group(1)
            title = (title_el.text.strip() if title_el is not None else "").replace("\n", " ").strip()
            if not title:
                continue
            authors = [a.find("name").text for a in entry.find_all("author") if a.find("name") is not None]
            published = entry.find("published")
            year = None
            if published is not None:
                ym = re.match(r"(\d{4})", published.text)
                if ym:
                    year = int(ym.group(1))
            articles.append(ResearchArticle(
                id=f"arxiv_{arxiv_id.replace('/', '_')}", title=title, authors=authors,
                year=year, abstract=abstract_el.text.strip() if abstract_el is not None else None,
                source="arxiv", url=f"https://arxiv.org/abs/{arxiv_id}",
            ))
    except Exception as e:
        print(f"[AR] arXiv error: {e}")
    return articles


def search_crossref(query: str) -> List[ResearchArticle]:
    articles = []
    try:
        params = urllib.parse.urlencode({"query": query, "rows": "30",
                                          "select": "DOI,title,author,abstract,container-title,published-print,issued,type"})
        url = f"https://api.crossref.org/works?{params}"
        resp = _get(url)
        if not resp or resp.status_code != 200:
            return articles
        for item in (resp.json().get("message", {}).get("items") or []):
            titles = item.get("title", [])
            if not titles or not titles[0]:
                continue
            authors = []
            for a in (item.get("author") or []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)
            issued = item.get("issued") or item.get("published-print") or {}
            dp = (issued.get("date-parts") or [[None]])[0]
            year = dp[0] if dp and dp[0] else None
            abstract = re.sub(r'</?jats?:?p>', '', item.get("abstract", ""))
            abstract = re.sub(r'</?p>', '', abstract)
            doi = item.get("DOI", "")
            articles.append(ResearchArticle(
                id=f"cr_{doi.replace('/', '_')}" if doi else f"cr_{hash(titles[0]) % 10**8}",
                title=titles[0], authors=authors,
                year=int(year) if year else None,
                abstract=abstract or None, source="crossref",
                url=f"https://doi.org/{doi}" if doi else None, doi=doi or None,
            ))
    except Exception as e:
        print(f"[AR] CrossRef error: {e}")
    return articles


def search_local_database(query: str, max_results: int = 50) -> List[ResearchArticle]:
    articles = []
    try:
        from database.setup import SessionLocal, Paper
        db = SessionLocal()
        try:
            like = f"%{query}%"
            rows = db.query(Paper).filter(
                (Paper.title.ilike(like)) | (Paper.abstract.ilike(like))
            ).limit(max_results).all()
            for row in rows:
                author_list = [a.strip() for a in (row.authors or "").split(",") if a.strip()]
                articles.append(ResearchArticle(
                    id=f"local_{row.id}", title=row.title or "",
                    authors=author_list, year=row.year,
                    abstract=row.abstract or None, source="local_db",
                    url=row.url or None,
                ))
        finally:
            db.close()
    except Exception as e:
        print(f"[AR] Local DB error: {e}")
    return articles


SOURCES = {
    "semantic_scholar": search_semantic_scholar,
    "openalex": search_openalex,
    "arxiv": search_arxiv,
    "crossref": search_crossref,
}


def find_relevant_articles(topic: str, sources: Optional[List[str]] = None) -> List[ResearchArticle]:
    if sources is None:
        sources = ["semantic_scholar", "openalex", "arxiv", "crossref"]

    print(f"[AR] Searching for: {topic} across {sources}")

    all_articles = []
    active_fns = [(name, SOURCES[name]) for name in sources if name in SOURCES]

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fn, topic) for _, fn in active_fns]
        for fut in as_completed(futures):
            try:
                all_articles.extend(fut.result())
            except Exception as e:
                print(f"[AR] Search failed: {e}")

    # Dedup
    seen_dois, seen_titles = set(), set()
    deduped = []
    for a in all_articles:
        if a.doi and a.doi.lower() in seen_dois:
            continue
        if a.doi:
            seen_dois.add(a.doi.lower())
        nt = a.title.lower().strip()
        nt = re.sub(r'[^\w\s]', '', nt)
        nt = re.sub(r'\s+', ' ', nt)
        if nt in seen_titles:
            continue
        seen_titles.add(nt)
        deduped.append(a)

    print(f"[AR] Raw: {len(all_articles)} -> Deduped: {len(deduped)}")

    # Rank with LLM
    ranked = _rank_with_llm(deduped, topic)
    return ranked[:10]


def _rank_with_llm(articles: List[ResearchArticle], topic: str) -> List[ResearchArticle]:
    from services.local_llm import rank_articles as llm_rank

    dicts = [
        {"title": a.title, "authors": a.authors, "year": a.year,
         "abstract": a.abstract, "citationCount": a.citationCount, "source": a.source}
        for a in articles
    ]

    result = llm_rank(dicts, topic)
    if not result:
        print("[AR] LLM ranking failed, returning deduped results as-is")
        return articles

    try:
        parsed = json.loads(result)
        ranked = []
        for entry in parsed:
            idx = entry.get("index", 0) - 1
            if 0 <= idx < len(articles):
                articles[idx].relevanceScore = round(entry.get("score", 0), 4)
                articles[idx].reasonSelected = entry.get("reasonSelected", "")
                ranked.append(articles[idx])
        ranked.sort(key=lambda a: -(a.relevanceScore or 0))
        print(f"[AR] LLM ranked {len(ranked)} articles")
        return ranked
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[AR] Failed to parse LLM response: {e}\nResponse: {result[:200]}")
        return articles


def find_local_articles(topic: str) -> List[ResearchArticle]:
    print(f"[AR] Searching local database for: {topic}")
    articles = search_local_database(topic, max_results=50)
    articles = _rank_with_llm(articles, topic)
    print(f"[AR] Local DB returned {len(articles)} results")
    return articles[:10]
