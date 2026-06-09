import io
import re
import time
import urllib.request
import urllib.error
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

PDF_DOWNLOAD_TIMEOUT = 10
MAX_INTRO_CHARS = 2000
MAX_WORKERS = 4

INTRO_PATTERNS = [
    re.compile(r'^\s*(?:1|I)\s*\.?\s*[—\-–]\s*[Ii]ntroduction\b'),
    re.compile(r'^\s*(?:1|I)\s*\.?\s*[Ii]ntroduction\b'),
    re.compile(r'^\s*[Ii]ntroduction\b'),
]

SECTION_BREAKS = [
    re.compile(r'^\s*(?:2|II|III|3)\s*\.?\s*(?:Related\s+Work|Background|Methods?|Methodology|Preliminaries|Approach|Experiments?|Results?|Discussion|Conclusion|Literature)\b'),
    re.compile(r'^\s*(?:Related\s+Work|Background|Methods?|Methodology|Preliminaries|Approach|Experiments?|Results?)\b'),
]

PDF_CACHE: dict = {}


def _download_pdf(url: str) -> Optional[bytes]:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AutoResearch/1.0)",
                "Accept": "application/pdf,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=PDF_DOWNLOAD_TIMEOUT) as resp:
            data = resp.read()
        if not data or len(data) < 1000:
            return None
        return data
    except Exception:
        return None


def _extract_introduction_from_text(text: str) -> Optional[str]:
    lines = text.split("\n")
    intro_start = None
    intro_end = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if intro_start is None:
            for pat in INTRO_PATTERNS:
                if pat.match(stripped):
                    intro_start = i
                    break
        elif intro_start is not None:
            for pat in SECTION_BREAKS:
                if pat.match(stripped):
                    intro_end = i
                    break
            if intro_end is not None:
                break

    if intro_start is not None:
        intro_lines = lines[intro_start + 1:intro_end if intro_end else None]
        text = " ".join(l.strip() for l in intro_lines if l.strip())
        text = re.sub(r'\s+', ' ', text).strip()
        if text and len(text) > 50:
            return text[:MAX_INTRO_CHARS]

    return None


def _parse_pdf_intro(data: bytes) -> Optional[str]:
    if not PYMUPDF_AVAILABLE:
        return None
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        text_parts = []
        for page_num in range(min(len(doc), 5)):
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()
        full_text = "\n".join(text_parts)
        if not full_text.strip():
            return None
        intro = _extract_introduction_from_text(full_text)
        if intro:
            return intro
        first_2000 = re.sub(r'\s+', ' ', full_text).strip()[:MAX_INTRO_CHARS]
        if len(first_2000) > 100:
            return first_2000
        return None
    except Exception:
        return None


def get_intro_text(pdf_url: str) -> Optional[str]:
    if pdf_url in PDF_CACHE:
        return PDF_CACHE[pdf_url]
    data = _download_pdf(pdf_url)
    if data is None:
        PDF_CACHE[pdf_url] = None
        return None
    intro = _parse_pdf_intro(data)
    PDF_CACHE[pdf_url] = intro
    return intro


def enrich_docs_with_intros(docs: list) -> list:
    if not PYMUPDF_AVAILABLE:
        print("[PDF] PyMuPDF not available, skipping PDF extraction")
        return docs

    todo = [(i, d) for i, d in enumerate(docs) if d.get("pdf_url")]
    if not todo:
        print("[PDF] No PDF URLs available in documents")
        return docs

    print(f"[PDF] Extracting introductions from {len(todo)} PDFs ({MAX_WORKERS} workers)...")
    success = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut_to_idx = {
            pool.submit(get_intro_text, d["pdf_url"]): i
            for i, d in todo
        }
        for fut in as_completed(fut_to_idx):
            idx = fut_to_idx[fut]
            try:
                intro = fut.result()
                if intro:
                    docs[idx]["intro_text"] = intro
                    success += 1
                    print(f"[PDF] Got intro for: {docs[idx].get('title', '')[:60]}")
            except Exception:
                pass

    elapsed = time.time() - start
    print(f"[PDF] {success}/{len(todo)} introductions extracted ({elapsed:.1f}s)")
    return docs
