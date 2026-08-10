from __future__ import annotations

import contextlib
import hashlib
import re
import signal
import threading
from dataclasses import dataclass
from pathlib import Path

import fitz
from bs4 import BeautifulSoup, FeatureNotFound

from .http import get_client
from .schema import FullTextRecord, PaperRecord, RankedPaper, TextSection
from .utils import clean_text, normalize_title

SECTION_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "methods",
    "method",
    "materials and methods",
    "experiments",
    "experimental setup",
    "results",
    "evaluation",
    "discussion",
    "limitations",
    "limitation",
    "conclusion",
    "conclusions",
}


@dataclass(frozen=True)
class FullTextCandidate:
    provider: str
    url: str
    kind: str


def _safe_stem(title: str, index: int) -> str:
    digest = hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()[:10]
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_title(title)).strip("-")[:80]
    return f"{index:02d}-{slug or 'paper'}-{digest}"


def _arxiv_id_from_url(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([^?#/]+)", url)
    if not match:
        return ""
    return match.group(1).removesuffix(".pdf")


def _candidate_records(paper: PaperRecord) -> list[FullTextCandidate]:
    candidates: list[FullTextCandidate] = []
    if paper.pmcid:
        candidates.append(
            FullTextCandidate(
                provider="pmc_xml",
                url=f"https://pmc.ncbi.nlm.nih.gov/articles/{paper.pmcid}/?report=xml",
                kind="xml",
            )
        )
        candidates.append(
            FullTextCandidate(
                provider="pmc_html",
                url=f"https://pmc.ncbi.nlm.nih.gov/articles/{paper.pmcid}/",
                kind="html",
            )
        )
    if paper.pdf_url:
        provider = "arxiv_pdf" if "arxiv.org" in paper.pdf_url.lower() else "direct_pdf"
        candidates.append(FullTextCandidate(provider=provider, url=paper.pdf_url, kind="pdf"))
    arxiv_id = paper.arxiv_id or _arxiv_id_from_url(paper.url)
    if arxiv_id:
        candidates.append(
            FullTextCandidate(
                provider="arxiv_pdf",
                url=f"https://arxiv.org/pdf/{arxiv_id}",
                kind="pdf",
            )
        )
    if paper.url and (
        paper.url.lower().endswith(".pdf")
        or "ncbi.nlm.nih.gov/pmc/articles/" in paper.url.lower()
    ):
        kind = "pdf" if paper.url.lower().endswith(".pdf") else "html"
        provider = "direct_pdf" if kind == "pdf" else "direct_html"
        candidates.append(FullTextCandidate(provider=provider, url=paper.url, kind=kind))
    seen = set()
    return [
        candidate
        for candidate in candidates
        if candidate.url and not ((candidate.provider, candidate.url) in seen or seen.add((candidate.provider, candidate.url)))
    ]


def _candidate_urls(paper: PaperRecord) -> list[str]:
    return [candidate.url for candidate in _candidate_records(paper)]


def _extract_pdf_text(content: bytes) -> str:
    document = fitz.open(stream=content, filetype="pdf")
    try:
        return "\n".join(page.get_text("text") for page in document)
    finally:
        document.close()


def _extract_html_text(content: bytes) -> tuple[str, list[TextSection]]:
    soup = BeautifulSoup(content, "html.parser")
    for node in soup(["script", "style", "noscript", "nav", "footer"]):
        node.decompose()
    sections: list[TextSection] = []
    current_heading = "body"
    current_parts: list[str] = []
    for node in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = clean_text(node.get_text(" "))
        if not text:
            continue
        if node.name in {"h1", "h2", "h3"}:
            if current_parts:
                sections.append(TextSection(heading=current_heading, text=clean_text(" ".join(current_parts))))
            current_heading = text[:100]
            current_parts = []
        else:
            current_parts.append(text)
    if current_parts:
        sections.append(TextSection(heading=current_heading, text=clean_text(" ".join(current_parts))))
    return clean_text(soup.get_text(" ")), sections


def _extract_jats_xml_text(content: bytes) -> tuple[str, list[TextSection]]:
    try:
        soup = BeautifulSoup(content, "xml")
    except FeatureNotFound:
        soup = BeautifulSoup(content, "html.parser")
    sections: list[TextSection] = []
    for abstract in soup.find_all("abstract"):
        text = clean_text(abstract.get_text(" "))
        if text:
            sections.append(TextSection(heading="Abstract", text=text))
    for sec in soup.find_all("sec"):
        title_node = sec.find("title", recursive=False)
        heading = clean_text(title_node.get_text(" ")) if title_node else "Section"
        parts = [
            clean_text(node.get_text(" "))
            for node in sec.find_all(["p", "list-item"], recursive=True)
            if clean_text(node.get_text(" "))
        ]
        if parts:
            sections.append(TextSection(heading=heading[:100], text=clean_text(" ".join(parts), 9000)))
    text = clean_text(soup.get_text(" "))
    return text, sections or split_sections(text)


def _looks_like_heading(line: str) -> bool:
    normalized = re.sub(r"^\d+(?:\.\d+)*\s+", "", clean_text(line)).lower().strip(":")
    if normalized in SECTION_HEADINGS:
        return True
    return bool(
        re.match(
            r"^(?:\d+\.?\s+)?(abstract|introduction|methods?|experiments?|results|discussion|limitations?|conclusions?)$",
            normalized,
        )
    )


def split_sections(text: str, max_section_chars: int = 9000) -> list[TextSection]:
    sections: list[TextSection] = []
    heading = "body"
    parts: list[str] = []
    for raw_line in text.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        if len(line) < 90 and _looks_like_heading(line):
            if parts:
                sections.append(TextSection(heading=heading, text=clean_text(" ".join(parts), max_section_chars)))
            heading = re.sub(r"^\d+(?:\.\d+)*\s+", "", line).strip()
            parts = []
        else:
            parts.append(line)
    if parts:
        sections.append(TextSection(heading=heading, text=clean_text(" ".join(parts), max_section_chars)))
    if not sections and text:
        sections.append(TextSection(heading="body", text=clean_text(text, max_section_chars)))
    return sections[:20]


@contextlib.contextmanager
def _paper_time_limit(seconds: float):
    if seconds <= 0 or threading.current_thread() is not threading.main_thread():
        yield
        return
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(_signum, _frame):
        raise TimeoutError(f"full-text read exceeded {seconds:.1f}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _content_kind(candidate: FullTextCandidate, content_type: str, url: str, content: bytes) -> str:
    lowered_type = content_type.lower()
    lowered_url = url.lower()
    prefix = content[:200].lstrip().lower()
    if candidate.kind == "xml" or "xml" in lowered_type or b"<article" in prefix:
        return "xml"
    if candidate.kind == "pdf" or "pdf" in lowered_type or lowered_url.endswith(".pdf"):
        return "pdf"
    return "html"


def _extract_text_for_kind(kind: str, content: bytes) -> tuple[str, list[TextSection]]:
    if kind == "pdf":
        text = _extract_pdf_text(content)
        return text, split_sections(text)
    if kind == "xml":
        return _extract_jats_xml_text(content)
    text, html_sections = _extract_html_text(content)
    return text, html_sections or split_sections(text)


def fetch_full_text(
    paper: PaperRecord,
    raw_dir: Path,
    index: int,
    max_chars: int = 180_000,
    timeout: float = 12.0,
    hard_timeout: float = 35.0,
) -> FullTextRecord:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(paper.title, index)
    candidates = _candidate_records(paper)
    attempted_urls = [candidate.url for candidate in candidates]
    attempted_providers = [candidate.provider for candidate in candidates]
    if not candidates:
        return FullTextRecord(
            title=paper.title,
            source_url=paper.url,
            status="skipped",
            failure_stage="candidate_discovery",
            error="No full-text candidate URL.",
        )

    last_error = ""
    try:
        with _paper_time_limit(hard_timeout), get_client(timeout=timeout) as client:
            for candidate in candidates:
                try:
                    response = client.get(candidate.url)
                    response.raise_for_status()
                except Exception as exc:
                    if isinstance(exc, TimeoutError) or "full-text read exceeded" in str(exc):
                        raise TimeoutError(str(exc)) from exc
                    last_error = f"{candidate.provider} request failed: {exc}"
                    continue
                content_type = response.headers.get("content-type", "")
                kind = _content_kind(candidate, content_type, str(response.url), response.content)
                suffix = {"pdf": ".pdf", "xml": ".xml"}.get(kind, ".html")
                raw_path = raw_dir / f"{stem}-{candidate.provider}{suffix}"
                raw_path.write_bytes(response.content)
                try:
                    text, sections = _extract_text_for_kind(kind, response.content)
                except Exception as exc:
                    if isinstance(exc, TimeoutError) or "full-text read exceeded" in str(exc):
                        raise TimeoutError(str(exc)) from exc
                    last_error = f"{candidate.provider} text extraction failed: {exc}"
                    continue
                text = text[:max_chars]
                if len(text) < 500:
                    last_error = f"{candidate.provider} extracted too little text"
                    continue
                text_path = raw_dir / f"{stem}.txt"
                text_path.write_text(text, encoding="utf-8", errors="ignore")
                return FullTextRecord(
                    title=paper.title,
                    source_url=paper.url,
                    fetched_url=str(response.url),
                    raw_path=str(raw_path),
                    text_path=str(text_path),
                    status="ok",
                    provider=candidate.provider,
                    attempted_providers=attempted_providers,
                    attempted_urls=attempted_urls,
                    content_type=content_type,
                    sections=sections,
                )
    except TimeoutError as exc:
        return FullTextRecord(
            title=paper.title,
            source_url=paper.url,
            status="failed",
            provider=attempted_providers[0] if attempted_providers else "",
            attempted_providers=attempted_providers,
            attempted_urls=attempted_urls,
            failure_stage="timeout",
            error=str(exc),
        )
    return FullTextRecord(
        title=paper.title,
        source_url=paper.url,
        status="failed",
        provider=attempted_providers[0] if attempted_providers else "",
        attempted_providers=attempted_providers,
        attempted_urls=attempted_urls,
        failure_stage="provider_fetch_or_parse",
        error=last_error,
    )


def fetch_full_texts(
    ranked: list[RankedPaper],
    raw_dir: Path,
    limit: int = 8,
    max_workers: int = 4,
    timeout: float = 12.0,
    hard_timeout: float = 35.0,
) -> dict[str, FullTextRecord]:
    records: dict[str, FullTextRecord] = {}
    rows = list(enumerate(ranked[:limit], start=1))
    if not rows:
        return records
    _ = max_workers
    for index, row in rows:
        paper = row.paper
        try:
            records[paper.title] = fetch_full_text(
                paper,
                raw_dir=raw_dir,
                index=index,
                timeout=timeout,
                hard_timeout=hard_timeout,
            )
        except Exception as exc:  # noqa: BLE001 - one unexpected parser/fetch issue should not stop the run.
            records[paper.title] = FullTextRecord(
                title=paper.title,
                source_url=paper.url,
                status="failed",
                failure_stage="unexpected",
                error=str(exc),
            )
    return records
