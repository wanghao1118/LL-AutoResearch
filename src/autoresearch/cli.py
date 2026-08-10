from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .bench import (
    match_benchmarks,
    search_benchmarks,
    understand_benchmark,
    write_bench_card_report,
    write_bench_evidence_block,
)
from .bench.catalog import list_seed_benches
from .codex_review import apply_codex_review_to_output, write_codex_review_packet
from .dashboard import load_artifacts, write_dashboard
from .domain_profile import generate_domain_profile, save_domain_profile
from .pipeline import run_search
from .report import write_report
from .synthesizer import build_synthesis, write_analysis_report
from .utils import slugify

app = typer.Typer(help="AutoResearch command line interface.", no_args_is_help=True)
bench_app = typer.Typer(help="Benchmark evidence tools.", no_args_is_help=True)
app.add_typer(bench_app, name="bench")
console = Console()
DEFAULT_OUTPUT_ROOT = Path("outputs")


@app.callback()
def main() -> None:
    """Evidence-grounded research workflow tools."""


@app.command()
def search(
    topic: str = typer.Argument(..., help="Research topic or direction."),
    limit: int = typer.Option(30, help="Number of deduplicated ranked papers to keep."),
    output_root: Path = typer.Option(  # noqa: B008
        DEFAULT_OUTPUT_ROOT,
        help="Directory for artifacts.",
    ),
    per_query_limit: int = typer.Option(8, help="Results per source/query pair."),
    full_text_limit: int = typer.Option(8, help="Number of top-ranked papers to fetch/read."),
    enrichment_limit: int = typer.Option(
        20,
        help="Number of top-ranked papers to enrich with Semantic Scholar.",
    ),
    open_access_limit: int = typer.Option(
        20,
        help="Number of top-ranked DOI papers to enrich with Unpaywall open-access links.",
    ),
    source_failure_skip_threshold: int = typer.Option(
        3,
        help="Skip a source for the rest of the run after this many consecutive failures.",
    ),
    llm_card_limit: int = typer.Option(
        0,
        help="Number of top paper cards to refine with a configured OpenAI-compatible LLM.",
    ),
    llm_model: str = typer.Option(
        "",
        help="Override AUTORESEARCH_LLM_MODEL for LLM-backed paper card extraction.",
    ),
    llm_timeout: float = typer.Option(
        45.0,
        help="Timeout in seconds for each LLM-backed paper card extraction request.",
    ),
    profile: str = typer.Option(
        "auto",
        help="Domain profile id or JSON path. Use 'auto', 'medical-vlm', 'gui-agent', or a profile file.",
    ),
) -> None:
    """Run Auto Search for a research topic."""
    artifacts, output_dir = run_search(
        topic,
        limit=limit,
        output_root=output_root,
        per_query_limit=per_query_limit,
        full_text_limit=full_text_limit,
        enrichment_limit=enrichment_limit,
        open_access_limit=open_access_limit,
        source_failure_skip_threshold=source_failure_skip_threshold,
        llm_card_limit=llm_card_limit,
        llm_model=llm_model,
        llm_timeout=llm_timeout,
        profile=profile,
        console=console,
    )
    console.print()
    console.print(f"[bold green]Done[/bold green] wrote artifacts to {output_dir}")
    console.print(f"Papers: {len(artifacts.ranked_papers)}")
    console.print(f"Gaps: {len(artifacts.gaps)}")
    console.print(f"Report: {output_dir / 'report.md'}")
    console.print(f"Dashboard: {output_dir / 'dashboard.html'}")


@bench_app.command("list")
def bench_list() -> None:
    """List seed benchmarks available to the BenchCard MVP."""
    for bench in list_seed_benches():
        console.print(
            f"[bold]{bench.bench_name}[/bold] "
            f"({', '.join(bench.domain[:3])}) -> {', '.join(bench.evaluated_capabilities[:3])}"
        )


@bench_app.command("match")
def bench_match(
    weakness: str = typer.Argument(..., help="Research weakness to test against seed benchmarks."),
    output_root: Path = typer.Option(  # noqa: B008
        DEFAULT_OUTPUT_ROOT,
        help="Directory for bench evidence artifacts.",
    ),
    limit: int = typer.Option(6, help="Number of related benchmark candidates to keep."),
) -> None:
    """Match a research weakness to benchmark evidence and benchmark weaknesses."""
    block = match_benchmarks(weakness, limit=limit)
    json_path, md_path = write_bench_evidence_block(block, output_root=output_root)
    console.print("[bold green]Done[/bold green] wrote Bench evidence block")
    console.print(f"Weakness: {weakness}")
    console.print(f"Need new benchmark: {block.need_new_benchmark}")
    console.print(f"Partial benches: {', '.join(block.partial_benches) or 'none'}")
    console.print(f"Sufficient benches: {', '.join(block.sufficient_benches) or 'none'}")
    console.print(f"JSON: {json_path}")
    console.print(f"Markdown: {md_path}")


@bench_app.command("understand")
def bench_understand(
    bench_name: str = typer.Argument(..., help="Benchmark name or alias to understand."),
    output_root: Path = typer.Option(  # noqa: B008
        DEFAULT_OUTPUT_ROOT,
        help="Directory for bench understanding artifacts.",
    ),
) -> None:
    """Generate a structured BenchCard and Chinese report for one seed benchmark."""
    try:
        bench = understand_benchmark(bench_name)
    except ValueError as error:
        console.print(f"[bold red]Error[/bold red] {error}")
        raise typer.Exit(code=1) from error
    json_path, md_path = write_bench_card_report(bench, output_root=output_root)
    console.print("[bold green]Done[/bold green] wrote Bench understanding report")
    console.print(f"Bench: {bench.bench_name}")
    console.print(f"Capabilities: {', '.join(bench.evaluated_capabilities) or 'none'}")
    console.print(f"Keywords: {', '.join([*bench.keywords, *bench.tags][:12]) or 'none'}")
    console.print(f"JSON: {json_path}")
    console.print(f"Markdown: {md_path}")


@bench_app.command("search")
def bench_search(
    query: str = typer.Argument(..., help="Keyword query, e.g. openai, finance workflow, GUI recovery."),
    limit: int = typer.Option(10, help="Number of matching benchmarks to show."),
) -> None:
    """Search seed benchmarks by domain, ability, metric, source, model, or weakness keyword."""
    results = search_benchmarks(query, limit=limit)
    console.print(f"[bold]Bench search[/bold]: {query}")
    if not results:
        console.print("No benchmark candidates found.")
        return
    for result in results:
        console.print(
            f"- [bold]{result.bench_name}[/bold] "
            f"score={result.relevance_score} "
            f"matched={', '.join(result.matched_keywords) or 'none'} "
            f"domain={', '.join(result.domain[:3]) or 'none'}"
        )


@app.command()
def synthesize(
    artifact_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Output directory or search_result.json path.",
    ),
) -> None:
    """Generate the Chinese LLM-style synthesis from existing artifacts."""
    artifacts = load_artifacts(artifact_path)
    target_dir = artifact_path if artifact_path.is_dir() else artifact_path.parent
    artifacts.synthesis = build_synthesis(artifacts)
    artifacts.write_json(target_dir)
    analysis_path = write_analysis_report(artifacts, target_dir)
    write_report(artifacts, target_dir)
    path = write_dashboard(artifacts, target_dir)
    console.print(f"[bold green]Done[/bold green] wrote synthesis to {analysis_path}")
    console.print(f"Dashboard: {path}")


@app.command("codex-packet")
def codex_packet(
    artifact_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Output directory or search_result.json path.",
    ),
    output_dir: Path | None = typer.Option(  # noqa: B008
        None,
        help="Directory for codex review packet files. Defaults to the artifact directory.",
    ),
) -> None:
    """Export an evidence packet for Codex to act as the manual LLM reviewer."""
    artifacts = load_artifacts(artifact_path)
    target_dir = output_dir or (artifact_path if artifact_path.is_dir() else artifact_path.parent)
    packet_md, packet_json, template_path = write_codex_review_packet(artifacts, target_dir)
    console.print(f"[bold green]Done[/bold green] wrote Codex review packet to {packet_md}")
    console.print(f"Packet JSON: {packet_json}")
    console.print(f"Result template: {template_path}")


@app.command("codex-apply")
def codex_apply(
    artifact_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Output directory or search_result.json path.",
    ),
    result_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Codex review result JSON.",
    ),
    output_dir: Path | None = typer.Option(  # noqa: B008
        None,
        help="Directory for updated artifacts. Defaults to the artifact directory.",
    ),
) -> None:
    """Apply a Codex manual LLM review result back into the artifacts and dashboard."""
    artifacts, dashboard_path = apply_codex_review_to_output(
        artifact_path,
        result_path,
        output_dir=output_dir,
    )
    console.print("[bold green]Done[/bold green] applied Codex review")
    console.print(f"Gaps: {len(artifacts.gaps)}")
    console.print(f"Research opportunities: {len(artifacts.research_opportunities)}")
    console.print(f"Dashboard: {dashboard_path}")


@app.command("profile")
def profile_command(
    topic: str = typer.Argument(..., help="Research topic or direction."),
    profile_id: str = typer.Option(
        "auto",
        help="Profile id to use or infer. Examples: auto, medical-vlm, gui-agent, llm-agent.",
    ),
    output_path: Path | None = typer.Option(  # noqa: B008
        None,
        help="Where to write the generated profile JSON.",
    ),
) -> None:
    """Generate or inspect a domain profile for a research topic."""
    profile = generate_domain_profile(topic, profile_id)
    target = output_path or Path("profiles") / f"{slugify(profile.domain_id)}.generated.json"
    path = save_domain_profile(profile, target)
    console.print(f"[bold green]Done[/bold green] wrote domain profile to {path}")
    console.print(f"Domain: {profile.domain_name}")
    console.print(f"Capabilities: {len(profile.capability_dimensions)}")
    console.print("Core concepts: " + ", ".join(profile.core_concepts[:8]))
    console.print("Preferred sources: " + ", ".join(profile.source_policy.preferred_sources))
    console.print("Downrank sources: " + ", ".join(profile.source_policy.downrank_sources))
    console.print(f"Core evidence keywords: {len(profile.evidence_policy.core_keywords)}")


@app.command()
def dashboard(
    artifact_path: Path = typer.Argument(  # noqa: B008
        ...,
        help="Output directory or search_result.json path.",
    ),
    output_dir: Path | None = typer.Option(  # noqa: B008
        None,
        help="Directory for dashboard.html. Defaults to the artifact directory.",
    ),
) -> None:
    """Generate a static HTML dashboard from existing search artifacts."""
    artifacts = load_artifacts(artifact_path)
    target_dir = output_dir
    if target_dir is None:
        target_dir = artifact_path if artifact_path.is_dir() else artifact_path.parent
    path = write_dashboard(artifacts, target_dir)
    console.print(f"[bold green]Done[/bold green] wrote dashboard to {path}")


if __name__ == "__main__":
    app()
