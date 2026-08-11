from autoresearch.fulltext import _candidate_urls
from autoresearch.fulltext_resolver import resolve_paper_full_text_links
from autoresearch.schema import PaperRecord


def test_resolver_adds_arxiv_source_candidate_before_pdf():
    paper = PaperRecord(
        title="LLaVA-Med",
        arxiv_id="2306.00890",
        url="https://arxiv.org/abs/2306.00890",
        pdf_url="https://arxiv.org/pdf/2306.00890",
    )

    record = resolve_paper_full_text_links(paper)
    candidates = _candidate_urls(paper)

    assert record.status == "ok"
    assert "arxiv_source" in record.resolved_by
    assert candidates[0] == "https://arxiv.org/e-print/2306.00890"
    assert "https://export.arxiv.org/e-print/2306.00890" in candidates
    assert "https://arxiv.org/src/2306.00890" in candidates
    assert "https://arxiv.org/pdf/2306.00890" in candidates


def test_resolver_adds_europepmc_xml_for_pmcid():
    paper = PaperRecord(title="PMC Paper", pmcid="PMC6908718")

    record = resolve_paper_full_text_links(paper)
    candidates = _candidate_urls(paper)

    assert record.status == "ok"
    assert "europepmc_xml" in record.resolved_by
    assert candidates[0] == "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6908718/fullTextXML"
