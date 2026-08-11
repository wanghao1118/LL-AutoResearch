from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import os
import re
import signal
import tarfile
import threading
import time
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path

import fitz
import httpx
from bs4 import BeautifulSoup, FeatureNotFound, XMLParsedAsHTMLWarning

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


@dataclass(frozen=True)
class FetchedContent:
    content: bytes
    content_type: str
    url: str
    cache_status: str = "miss"


class CachedFullTextFailure(RuntimeError):
    pass


def _safe_stem(title: str, index: int) -> str:
    digest = hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()[:10]
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_title(title)).strip("-")[:80]
    return f"{index:02d}-{slug or 'paper'}-{digest}"


def _arxiv_id_from_url(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|pdf|e-print|src)/([^?#/]+)", url)
    if not match:
        return ""
    return match.group(1).removesuffix(".pdf")


def _arxiv_source_candidates(arxiv_id: str) -> list[FullTextCandidate]:
    return [
        FullTextCandidate(
            provider="arxiv_source",
            url=f"https://arxiv.org/e-print/{arxiv_id}",
            kind="source",
        ),
        FullTextCandidate(
            provider="arxiv_source",
            url=f"https://export.arxiv.org/e-print/{arxiv_id}",
            kind="source",
        ),
        FullTextCandidate(
            provider="arxiv_source",
            url=f"https://arxiv.org/src/{arxiv_id}",
            kind="source",
        ),
    ]


def _arxiv_pdf_candidates(arxiv_id: str) -> list[FullTextCandidate]:
    return [
        FullTextCandidate(
            provider="arxiv_pdf",
            url=f"https://arxiv.org/pdf/{arxiv_id}",
            kind="pdf",
        ),
        FullTextCandidate(
            provider="arxiv_pdf",
            url=f"https://export.arxiv.org/pdf/{arxiv_id}",
            kind="pdf",
        ),
    ]


def _candidate_records(paper: PaperRecord) -> list[FullTextCandidate]:
    candidates: list[FullTextCandidate] = []
    for raw_candidate in paper.raw.get("full_text_candidates") or []:
        if not isinstance(raw_candidate, dict):
            continue
        provider = str(raw_candidate.get("provider") or "").strip()
        url = str(raw_candidate.get("url") or "").strip()
        kind = str(raw_candidate.get("kind") or "").strip()
        if provider and url and kind:
            candidates.append(FullTextCandidate(provider=provider, url=url, kind=kind))
    if paper.pmcid:
        candidates.append(
            FullTextCandidate(
                provider="europepmc_xml",
                url=f"https://www.ebi.ac.uk/europepmc/webservices/rest/{paper.pmcid}/fullTextXML",
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
        candidates.extend(_arxiv_source_candidates(arxiv_id))
        candidates.extend(_arxiv_pdf_candidates(arxiv_id))
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
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
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


def _decode_text(content: bytes) -> str:
    for encoding in ["utf-8", "latin-1"]:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _latex_to_text(text: str) -> str:
    text = re.sub(r"\\(?:sub)*section\*?\{([^{}]{1,120})\}", r"\n\1\n", text)
    text = re.sub(r"\\(?:paragraph|subparagraph)\*?\{([^{}]{1,120})\}", r"\n\1\n", text)
    text = re.sub(r"\\begin\{(?:abstract)\}", "\nAbstract\n", text)
    text = re.sub(r"\\end\{(?:abstract)\}", "\n", text)
    text = re.sub(r"\\(?:cite|ref|label|url|href|footnote)(?:\[[^\]]*\])?\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$]", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:220_000]


def _source_file_is_useful(name: str) -> bool:
    lowered = name.lower()
    if lowered.endswith((".cls", ".sty", ".bst", ".bib", ".png", ".jpg", ".jpeg", ".pdf", ".eps")):
        return False
    return lowered.endswith((".tex", ".bbl", ".txt", ".md"))


def _text_from_source_member(name: str, content: bytes) -> str:
    text = _decode_text(content)
    if name.lower().endswith((".tex", ".bbl")):
        return _latex_to_text(text)
    return clean_text(text, 80_000)


def _extract_arxiv_source_text(content: bytes) -> tuple[str, list[TextSection]]:
    parts: list[str] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or not _source_file_is_useful(member.name):
                    continue
                extracted = archive.extractfile(member)
                if not extracted:
                    continue
                text = _text_from_source_member(member.name, extracted.read())
                if len(text) > 200:
                    parts.append(text)
                if len(" ".join(parts)) > 180_000:
                    break
    except tarfile.TarError:
        parts = []
    if not parts:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                for name in archive.namelist():
                    if not _source_file_is_useful(name):
                        continue
                    text = _text_from_source_member(name, archive.read(name))
                    if len(text) > 200:
                        parts.append(text)
                    if len(" ".join(parts)) > 180_000:
                        break
        except zipfile.BadZipFile:
            parts = []
    if not parts:
        try:
            decompressed = gzip.decompress(content)
            if decompressed != content:
                return _extract_arxiv_source_text(decompressed)
        except (gzip.BadGzipFile, EOFError, OSError):
            pass
    if not parts:
        raw = _decode_text(content)
        parts = [_latex_to_text(raw) if "\\" in raw else clean_text(raw, 180_000)]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(parts)).strip()[:180_000]
    return text, split_sections(text)


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
    if prefix.startswith((b"<!doctype html", b"<html")) or "text/html" in lowered_type:
        return "html"
    if candidate.kind == "source":
        return "source"
    if candidate.kind == "xml" or "xml" in lowered_type or prefix.startswith(b"<?xml") or b"<article" in prefix:
        return "xml"
    if candidate.kind == "pdf" or "pdf" in lowered_type or lowered_url.endswith(".pdf"):
        return "pdf"
    return "html"


def _extract_text_for_kind(kind: str, content: bytes) -> tuple[str, list[TextSection]]:
    if kind == "source":
        return _extract_arxiv_source_text(content)
    if kind == "pdf":
        text = _extract_pdf_text(content)
        return text, split_sections(text)
    if kind == "xml":
        return _extract_jats_xml_text(content)
    text, html_sections = _extract_html_text(content)
    return text, html_sections or split_sections(text)


def _candidate_time_budget(candidate: FullTextCandidate, hard_timeout: float) -> float:
    if candidate.kind == "source":
        return min(hard_timeout, 15.0)
    if candidate.kind == "pdf":
        return min(hard_timeout, 20.0)
    return hard_timeout


def _is_arxiv_candidate(candidate: FullTextCandidate) -> bool:
    return candidate.provider.startswith("arxiv_") or "arxiv.org" in candidate.url.lower()


def _fulltext_cache_dir() -> Path:
    return Path(os.environ.get("AUTORESEARCH_CACHE_DIR", ".cache/autoresearch")) / "fulltext"


def _cache_key(candidate: FullTextCandidate) -> str:
    return hashlib.sha256(f"{candidate.provider}|{candidate.url}".encode()).hexdigest()[:32]


def _cache_paths(candidate: FullTextCandidate) -> tuple[Path, Path, Path]:
    root = _fulltext_cache_dir()
    key = _cache_key(candidate)
    return root / f"{key}.bin", root / f"{key}.json", root / f"{key}.failure.json"


def _failure_cache_ttl() -> float:
    return float(os.environ.get("AUTORESEARCH_FULLTEXT_FAILURE_CACHE_TTL_SECONDS", "3600"))


def _read_success_cache(candidate: FullTextCandidate) -> FetchedContent | None:
    data_path, meta_path, _failure_path = _cache_paths(candidate)
    if not data_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return FetchedContent(
            content=data_path.read_bytes(),
            content_type=str(meta.get("content_type") or ""),
            url=str(meta.get("url") or candidate.url),
            cache_status="hit",
        )
    except (OSError, json.JSONDecodeError):
        return None


def _write_success_cache(candidate: FullTextCandidate, fetched: FetchedContent) -> None:
    try:
        data_path, meta_path, _failure_path = _cache_paths(candidate)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_bytes(fetched.content)
        meta_path.write_text(
            json.dumps(
                {
                    "provider": candidate.provider,
                    "candidate_url": candidate.url,
                    "url": fetched.url,
                    "content_type": fetched.content_type,
                    "written_at": time.time(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        return


def _read_failure_cache(candidate: FullTextCandidate) -> str:
    if not _is_arxiv_candidate(candidate):
        return ""
    _data_path, _meta_path, failure_path = _cache_paths(candidate)
    if not failure_path.exists():
        return ""
    if time.time() - failure_path.stat().st_mtime > _failure_cache_ttl():
        return ""
    try:
        payload = json.loads(failure_path.read_text(encoding="utf-8"))
        return clean_text(str(payload.get("error") or "recent cached provider failure"))
    except (OSError, json.JSONDecodeError):
        return "recent cached provider failure"


def _write_failure_cache(candidate: FullTextCandidate, error: str) -> None:
    if not _is_arxiv_candidate(candidate):
        return
    try:
        _data_path, _meta_path, failure_path = _cache_paths(candidate)
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(
            json.dumps(
                {
                    "provider": candidate.provider,
                    "candidate_url": candidate.url,
                    "error": clean_text(error, 400),
                    "written_at": time.time(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        return


def _candidate_request_timeout(
    candidate: FullTextCandidate,
    *,
    default_timeout: float,
    candidate_timeout: float,
) -> float:
    if candidate.provider == "arxiv_source":
        configured = float(os.environ.get("AUTORESEARCH_ARXIV_FULLTEXT_SOURCE_TIMEOUT_SECONDS", "8.0"))
        return max(1.0, min(candidate_timeout, configured))
    if candidate.provider == "arxiv_pdf":
        configured = float(os.environ.get("AUTORESEARCH_ARXIV_FULLTEXT_PDF_TIMEOUT_SECONDS", "10.0"))
        return max(1.0, min(candidate_timeout, configured))
    return max(1.0, min(candidate_timeout, default_timeout))


def _candidate_attempts(candidate: FullTextCandidate) -> int:
    if not _is_arxiv_candidate(candidate):
        return 1
    return max(1, int(os.environ.get("AUTORESEARCH_ARXIV_FULLTEXT_RETRIES", "2")))


def _download_candidate_content(
    client: httpx.Client,
    candidate: FullTextCandidate,
    *,
    request_timeout: float,
) -> FetchedContent:
    cached = _read_success_cache(candidate)
    if cached:
        return cached
    cached_failure = _read_failure_cache(candidate)
    if cached_failure:
        raise CachedFullTextFailure(f"{candidate.provider} cached failure: {cached_failure}")

    last_error = ""
    attempts = _candidate_attempts(candidate)
    for attempt in range(attempts):
        try:
            response = client.get(candidate.url, timeout=request_timeout)
            if response.status_code in {429, 500, 502, 503, 504} and attempt + 1 < attempts:
                retry_after = response.headers.get("Retry-After")
                try:
                    delay = min(float(retry_after), 3.0) if retry_after else 1.0
                except ValueError:
                    delay = 1.0
                time.sleep(delay)
                continue
            response.raise_for_status()
            return FetchedContent(
                content=response.content,
                content_type=response.headers.get("content-type", ""),
                url=str(response.url),
            )
        except httpx.TimeoutException as exc:
            last_error = clean_text(str(exc) or "request timed out", 500)
            if attempt + 1 < attempts:
                time.sleep(0.5)
                continue
            _write_failure_cache(candidate, f"{candidate.provider} timed out: {last_error}")
            raise TimeoutError(last_error) from exc
        except (httpx.HTTPError, OSError) as exc:
            last_error = clean_text(str(exc), 500)
            if attempt + 1 < attempts:
                time.sleep(0.5)
                continue
            break
    if last_error:
        _write_failure_cache(candidate, last_error)
        raise RuntimeError(last_error)
    raise RuntimeError("download returned no content")


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
    errors: list[str] = []
    deadline = time.monotonic() + hard_timeout
    with get_client(timeout=timeout) as client:
        for candidate in candidates:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                last_error = f"full-text read exceeded {hard_timeout:.1f}s"
                errors.append(last_error)
                break
            candidate_timeout = max(1.0, min(_candidate_time_budget(candidate, hard_timeout), remaining))
            try:
                with _paper_time_limit(candidate_timeout):
                    fetched = _download_candidate_content(
                        client,
                        candidate,
                        request_timeout=_candidate_request_timeout(
                            candidate,
                            default_timeout=timeout,
                            candidate_timeout=candidate_timeout,
                        ),
                    )
                    content_type = fetched.content_type
                    kind = _content_kind(candidate, content_type, fetched.url, fetched.content)
                    suffix = {"pdf": ".pdf", "xml": ".xml", "source": ".src"}.get(kind, ".html")
                    raw_path = raw_dir / f"{stem}-{candidate.provider}{suffix}"
                    raw_path.write_bytes(fetched.content)
                    text, sections = _extract_text_for_kind(kind, fetched.content)
            except (
                CachedFullTextFailure,
                TimeoutError,
                httpx.HTTPError,
                OSError,
                RuntimeError,
                ValueError,
                fitz.FileDataError,
            ) as exc:
                if isinstance(exc, CachedFullTextFailure):
                    last_error = str(exc)
                elif isinstance(exc, TimeoutError) or "full-text read exceeded" in str(exc):
                    last_error = f"{candidate.provider} timed out after {candidate_timeout:.1f}s"
                    _write_failure_cache(candidate, last_error)
                else:
                    last_error = f"{candidate.provider} failed: {exc}"
                errors.append(last_error)
                continue
            text = text[:max_chars]
            if len(text) < 500:
                last_error = f"{candidate.provider} extracted too little text"
                errors.append(last_error)
                continue
            if fetched.cache_status != "hit":
                _write_success_cache(candidate, fetched)
            text_path = raw_dir / f"{stem}.txt"
            text_path.write_text(text, encoding="utf-8", errors="ignore")
            return FullTextRecord(
                title=paper.title,
                source_url=paper.url,
                fetched_url=fetched.url,
                raw_path=str(raw_path),
                text_path=str(text_path),
                status="ok",
                provider=candidate.provider,
                attempted_providers=attempted_providers,
                attempted_urls=attempted_urls,
                content_type=content_type,
                sections=sections,
            )
    failure_stage = "timeout" if errors and all("timed out" in error or "exceeded" in error for error in errors) else "provider_fetch_or_parse"
    return FullTextRecord(
        title=paper.title,
        source_url=paper.url,
        status="failed",
        provider=attempted_providers[0] if attempted_providers else "",
        attempted_providers=attempted_providers,
        attempted_urls=attempted_urls,
        failure_stage=failure_stage,
        error="; ".join(errors[-4:]) or last_error,
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
