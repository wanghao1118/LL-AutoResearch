"""Agent 3: optional live arXiv search for benchmark evidence."""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from .models import SearchHit


ARXIV_API = "https://export.arxiv.org/api/query"


GENERIC_QUERY_TERMS = {
    "agent",
    "benchmark",
    "dataset",
    "evaluation",
    "text",
    "code",
    "web",
    "image",
    "static",
    "interactive",
    "environment",
}


def _compile_query(query: str) -> tuple[str, set[str]]:
    """Compile a human query into valid arXiv API syntax and core tokens."""

    phrases = [" ".join(phrase.split()) for phrase in re.findall(r'"([^"]+)"', query)]
    remainder = re.sub(r'"[^"]+"', " ", query)
    tokens = re.findall(r"[a-z0-9]+", remainder.casefold())
    clauses = [f'all:"{phrase}"' for phrase in phrases]
    if "benchmark" in tokens or "dataset" in tokens:
        clauses.append("(all:benchmark OR all:dataset)")
    for token in tokens:
        if token not in GENERIC_QUERY_TERMS and len(token) >= 4:
            clauses.append(f"all:{token}")
        if len(clauses) >= 4:
            break
    if not clauses:
        clauses = [f"all:{token}" for token in tokens[:3]]
    core_tokens = {
        token
        for phrase in phrases
        for token in re.findall(r"[a-z0-9]+", phrase.casefold())
        if token not in GENERIC_QUERY_TERMS and len(token) >= 3
    }
    core_tokens.update(
        token for token in tokens if token not in GENERIC_QUERY_TERMS and len(token) >= 4
    )
    return " AND ".join(dict.fromkeys(clauses)), core_tokens


def _is_relevant(title: str, summary: str, core_tokens: set[str]) -> bool:
    """Reject API results that share none of the task-specific query terms."""

    if not core_tokens:
        return True
    haystack = set(re.findall(r"[a-z0-9]+", f"{title} {summary}".casefold()))
    required = 1 if len(core_tokens) <= 2 else 2
    return len(core_tokens & haystack) >= required


def search_arxiv(queries: list[str], max_results_per_query: int = 4, timeout: int = 20) -> list[SearchHit]:
    """Search official arXiv metadata and return de-duplicated literature hits."""

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    seen: set[str] = set()
    hits: list[SearchHit] = []
    for query in queries:
        compiled_query, core_tokens = _compile_query(query)
        params = urllib.parse.urlencode(
            {
                "search_query": compiled_query,
                "start": 0,
                "max_results": max_results_per_query,
                "sortBy": "relevance",
            }
        )
        request = urllib.request.Request(
            f"{ARXIV_API}?{params}",
            headers={"User-Agent": "AutoBenchResearch/0.1 (literature matching)"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            root = ET.fromstring(response.read())
        for entry in root.findall("atom:entry", namespace):
            url = entry.findtext("atom:id", default="", namespaces=namespace).strip()
            if not url or url in seen:
                continue
            title = " ".join(entry.findtext("atom:title", default="", namespaces=namespace).split())
            summary = " ".join(entry.findtext("atom:summary", default="", namespaces=namespace).split())
            if not _is_relevant(title, summary, core_tokens):
                continue
            seen.add(url)
            hits.append(
                SearchHit(
                    title=title,
                    summary=summary,
                    url=url.replace("http://", "https://"),
                    query=query,
                )
            )
    return hits
