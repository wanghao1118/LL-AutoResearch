from __future__ import annotations

import os
import re
from urllib.parse import quote, urlencode

from .config import sanitize_error
from .http import get_client
from .schema import FullTextResolutionRecord, PaperRecord, RankedPaper
from .utils import clean_text


def _unpaywall_email() -> str:
    return os.getenv("UNPAYWALL_EMAIL", "").strip()


def _candidate_key(candidate: dict) -> tuple[str, str]:
    return str(candidate.get("provider") or ""), str(candidate.get("url") or "")


def _raw_candidates(paper: PaperRecord) -> list[dict]:
    candidates = paper.raw.setdefault("full_text_candidates", [])
    if not isinstance(candidates, list):
        candidates = []
        paper.raw["full_text_candidates"] = candidates
    return candidates


def add_full_text_candidate(paper: PaperRecord, provider: str, url: str, kind: str) -> bool:
    url = clean_text(url)
    if not url:
        return False
    candidate = {"provider": provider, "url": url, "kind": kind}
    candidates = _raw_candidates(paper)
    existing = {_candidate_key(row) for row in candidates if isinstance(row, dict)}
    if _candidate_key(candidate) in existing:
        return False
    candidates.append(candidate)
    return True


def _arxiv_id_from_paper(paper: PaperRecord) -> str:
    if paper.arxiv_id:
        return paper.arxiv_id.removesuffix(".pdf")
    for value in [paper.url, paper.pdf_url]:
        match = re.search(r"arxiv\.org/(?:abs|pdf|e-print|src)/([^?#/]+)", value or "")
        if match:
            return match.group(1).removesuffix(".pdf")
    return ""


def _add_arxiv_source_candidates(paper: PaperRecord) -> list[str]:
    arxiv_id = _arxiv_id_from_paper(paper)
    if not arxiv_id:
        return []
    resolved_by: list[str] = []
    for url in [
        f"https://arxiv.org/e-print/{arxiv_id}",
        f"https://export.arxiv.org/e-print/{arxiv_id}",
        f"https://arxiv.org/src/{arxiv_id}",
    ]:
        if add_full_text_candidate(paper, provider="arxiv_source", url=url, kind="source"):
            resolved_by.append("arxiv_source")
    return resolved_by


def _add_pmc_candidates(paper: PaperRecord, pmcid: str) -> list[str]:
    resolved_by: list[str] = []
    if add_full_text_candidate(
        paper,
        provider="europepmc_xml",
        url=f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
        kind="xml",
    ):
        resolved_by.append("europepmc_xml")
    if add_full_text_candidate(
        paper,
        provider="pmc_html",
        url=f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
        kind="html",
    ):
        resolved_by.append("pmc_html")
    return resolved_by


def _candidate_from_url(provider: str, url: str) -> tuple[str, str, str] | None:
    url = clean_text(url)
    if not url:
        return None
    lowered = url.lower()
    kind = "pdf" if lowered.endswith(".pdf") or "type=pdf" in lowered else "html"
    return provider, url, kind


def _first_europepmc_item(payload: dict) -> dict:
    rows = (payload.get("resultList") or {}).get("result") or []
    return rows[0] if rows else {}


def _europepmc_full_text_urls(item: dict) -> list[str]:
    entries = ((item.get("fullTextUrlList") or {}).get("fullTextUrl")) or []
    return [clean_text(entry.get("url") or "") for entry in entries if clean_text(entry.get("url") or "")]


def _query_europepmc(paper: PaperRecord, timeout: float = 12.0) -> tuple[dict, str]:
    if paper.doi:
        query = f'DOI:"{paper.doi}"'
    elif paper.pmid:
        query = f"EXT_ID:{paper.pmid} AND SRC:MED"
    else:
        return {}, "missing DOI/PMID"
    params = urlencode({"query": query, "format": "json", "pageSize": 1, "resultType": "core"})
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}"
    with get_client(timeout=timeout) as client:
        response = client.get(url)
        response.raise_for_status()
        return _first_europepmc_item(response.json()), ""


def _resolve_europepmc(paper: PaperRecord, notes: list[str]) -> list[str]:
    resolved_by: list[str] = []
    if paper.pmcid:
        resolved_by.extend(_add_pmc_candidates(paper, paper.pmcid))
        return resolved_by
    if not (paper.doi or paper.pmid):
        notes.append("Europe PMC skipped: missing DOI/PMID")
        return resolved_by
    item, reason = _query_europepmc(paper)
    if reason:
        notes.append(f"Europe PMC skipped: {reason}")
        return resolved_by
    if not item:
        notes.append("Europe PMC found no matching record")
        return resolved_by
    pmcid = clean_text(item.get("pmcid") or "")
    if pmcid and not paper.pmcid:
        paper.pmcid = pmcid
        resolved_by.append("europepmc_pmcid")
        resolved_by.extend(_add_pmc_candidates(paper, pmcid))
    if item.get("pmid") and not paper.pmid:
        paper.pmid = clean_text(item.get("pmid") or "")
    for url in _europepmc_full_text_urls(item):
        candidate = _candidate_from_url("europepmc_full_text", url)
        if candidate and add_full_text_candidate(paper, *candidate):
            resolved_by.append("europepmc_full_text")
    if not resolved_by:
        notes.append("Europe PMC matched metadata but exposed no OA full-text URL")
    return sorted(set(resolved_by))


def _resolve_unpaywall(paper: PaperRecord, notes: list[str], timeout: float = 12.0) -> list[str]:
    email = _unpaywall_email()
    if not paper.doi:
        notes.append("Unpaywall skipped: missing DOI")
        return []
    if not email:
        notes.append("Unpaywall skipped: UNPAYWALL_EMAIL is not configured")
        return []
    with get_client(timeout=timeout) as client:
        response = client.get(
            f"https://api.unpaywall.org/v2/{quote(paper.doi, safe='')}",
            params={"email": email},
        )
        if response.status_code == 404:
            notes.append("Unpaywall found no DOI record")
            return []
        response.raise_for_status()
        payload = response.json()
    location = payload.get("best_oa_location") or {}
    urls = [
        ("unpaywall_pdf", location.get("url_for_pdf") or "", "pdf"),
        ("unpaywall_landing", location.get("url_for_landing_page") or "", "html"),
    ]
    resolved_by: list[str] = []
    for provider, url, kind in urls:
        if add_full_text_candidate(paper, provider, url, kind):
            resolved_by.append(provider)
            if kind == "pdf" and not paper.pdf_url:
                paper.pdf_url = url
    if not resolved_by:
        notes.append("Unpaywall record has no usable OA URL")
    return resolved_by


def resolve_paper_full_text_links(paper: PaperRecord) -> FullTextResolutionRecord:
    notes: list[str] = []
    resolved_by: list[str] = []
    try:
        resolved_by.extend(_add_arxiv_source_candidates(paper))
        resolved_by.extend(_resolve_europepmc(paper, notes))
        resolved_by.extend(_resolve_unpaywall(paper, notes))
        candidates = _raw_candidates(paper)
        candidate_urls = [str(row.get("url") or "") for row in candidates if isinstance(row, dict) and row.get("url")]
        status = "ok" if candidate_urls else "no_full_text_candidate"
        return FullTextResolutionRecord(
            title=paper.title,
            status=status,
            resolved_by=sorted(set(resolved_by)),
            candidate_count=len(candidate_urls),
            candidate_urls=candidate_urls,
            pmcid=paper.pmcid,
            doi=paper.doi,
            pmid=paper.pmid,
            notes=notes,
        )
    except Exception as exc:  # noqa: BLE001 - resolver failures should not stop the search run.
        candidates = _raw_candidates(paper)
        candidate_urls = [str(row.get("url") or "") for row in candidates if isinstance(row, dict) and row.get("url")]
        return FullTextResolutionRecord(
            title=paper.title,
            status="failed",
            resolved_by=sorted(set(resolved_by)),
            candidate_count=len(candidate_urls),
            candidate_urls=candidate_urls,
            pmcid=paper.pmcid,
            doi=paper.doi,
            pmid=paper.pmid,
            notes=notes,
            error=sanitize_error(str(exc)),
        )


def resolve_full_text_links(ranked: list[RankedPaper], limit: int = 8) -> dict[str, FullTextResolutionRecord]:
    records: dict[str, FullTextResolutionRecord] = {}
    if limit <= 0:
        return records
    for row in ranked[:limit]:
        records[row.paper.title] = resolve_paper_full_text_links(row.paper)
    return records
