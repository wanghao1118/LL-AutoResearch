"""Source-revealed human audit for blind literature benchmark matching."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


AUDIT_DECISIONS = ("MATCH", "PARTIAL", "MISMATCH")


def _clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _list_text(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _default_audit_id(display_label: str | None, iteration: int, cases: list[dict[str, Any]]) -> str:
    """Create a stable scope label so an older submission cannot be reused silently."""

    label = display_label or "auto_bench_literature_audit"
    slug = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
    slug = re.sub(r"_round_\d+(?:_delta)?$", "", slug)
    case_suffix = "_".join(case["case_id"] for case in cases)
    return f"{slug}_round_{iteration}_{case_suffix}"


def _actual_benchmark_scope(case: dict[str, Any]) -> list[tuple[str, str]]:
    """Return the human-verified paper list independent of catalog status.

    A benchmark may move from ``unmodeled`` to a typed primary or secondary
    catalog entry after feedback. The paper name and evidence section remain
    the review scope; that internal catalog-role change does not invalidate the
    researcher's earlier source-list verification.
    """

    return sorted(
        (
            re.sub(
                r"\blanguage\s+ports?\b",
                "",
                re.sub(r"[^a-z0-9]+", " ", str(item["benchmark_name"]).casefold()),
            ).strip(),
            str(item["evidence_section"]),
        )
        for item in case["actual_benchmarks"]
    )


def _submission_scope_snapshot(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Record the exact recommendation views covered by one human judgement."""

    return [
        {
            "case_id": case["case_id"],
            "selected_benchmark_ids": [
                item["benchmark_id"] for item in case["selected_recommendations"]
            ],
            "top_6_benchmark_ids": [item["benchmark_id"] for item in case["top_6_details"]],
            "route": case["route"],
        }
        for case in cases
    ]


def _carry_prior_source_checks(
    cases: list[dict[str, Any]],
    prior_audit: dict[str, Any],
    prior_submission: dict[str, Any],
) -> int:
    """Carry only unchanged source and gold-list checks into a later iteration.

    Recommendation comparison, judgement, and notes are intentionally excluded:
    they refer to the earlier portfolio and must be supplied again for the new
    iteration.
    """

    reviewer_id = _clean_text(prior_submission.get("reviewer_id"))
    prior_cases = {str(case["case_id"]): case for case in prior_audit.get("cases", [])}
    prior_reviews = {
        str(review.get("case_id", "")): review
        for review in prior_submission.get("reviews", [])
        if isinstance(review, dict)
    }
    carried = 0
    for case in cases:
        case_id = str(case["case_id"])
        old_case = prior_cases.get(case_id)
        old_review = prior_reviews.get(case_id)
        if not old_case or not old_review or not reviewer_id:
            continue
        same_scope = (
            case.get("source_title") == old_case.get("source_title")
            and case.get("source_url") == old_case.get("source_url")
            and case.get("source_input_sections") == old_case.get("source_input_sections")
            and _actual_benchmark_scope(case) == _actual_benchmark_scope(old_case)
        )
        if not same_scope:
            continue
        if old_review.get("source_verified") is not True:
            continue
        if old_review.get("actual_benchmarks_verified") is not True:
            continue
        case["carried_review_evidence"] = {
            "source_verified": True,
            "actual_benchmarks_verified": True,
            "reviewer_id": reviewer_id,
            "from_iteration": int(prior_audit.get("iteration", 1)),
            "scope_match": True,
        }
        carried += 1
    return carried


def _render_case(case: dict[str, Any], index: int) -> str:
    """Render one complete audit card without abbreviating its source text.

    The card joins three views that were separated during blind execution: the
    revealed paper and evidence sections, the generated benchmark portfolio,
    and the exact anonymized Introduction/Method input. It then appends the
    researcher's checks that are serialized by the page-level JavaScript.
    """

    actual_rows = []
    for benchmark in case["actual_benchmarks"]:
        rank = benchmark["rank_in_autobench"] if benchmark["rank_in_autobench"] is not None else "outside catalog"
        actual_rows.append(
            "<tr>"
            f"<td>{html.escape(str(benchmark['role']))}</td>"
            f"<td>{html.escape(str(benchmark['benchmark_name']))}</td>"
            f"<td>{html.escape(str(benchmark['evidence_section']))}</td>"
            f"<td>{'yes' if benchmark['selected_by_autobench'] else 'no'}</td>"
            f"<td>{html.escape(str(rank))}</td>"
            "</tr>"
        )
    selected_rows = []
    for item in case["selected_recommendations"]:
        selected_rows.append(
            "<tr>"
            f"<td>{item['rank']}</td>"
            f"<td><a href=\"{html.escape(item['source_url'], quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\">{html.escape(item['benchmark_name'])}</a></td>"
            f"<td>{item['score']:.3f}</td>"
            f"<td>{html.escape(item['selection_role'])}</td>"
            f"<td>{html.escape(item['paper_role'])}</td>"
            "</tr>"
        )
    comparison = case["comparison"]
    visible = case["visible_input"]
    source_sections = case["source_input_sections"]
    route_context = ""
    if "adaptation_plan" in case:
        route_context = f"""
        <div class="comparison">
          <h3>Route, gaps, and fallback plan</h3>
          <dl>
            <dt>Route</dt><dd>{html.escape(case['route'])}</dd>
            <dt>Expected literature route</dt><dd>{html.escape(case['expected_route'])}</dd>
            <dt>Decision reason</dt><dd>{html.escape(case['route_reason'])}</dd>
            <dt>Inferred task coverage</dt><dd>{case['coverage_ratio']:.1%}</dd>
            <dt>Missing task families</dt><dd>{html.escape(_list_text(case['adaptation_plan']['missing_task_families']))}</dd>
            <dt>Synthesis required</dt><dd>{'yes' if case['synthesis_plan']['required'] else 'no'}</dd>
            <dt>Synthesis targets</dt><dd>{html.escape(_list_text(case['synthesis_plan']['target_task_families']))}</dd>
            <dt>Catalog admission proposals</dt><dd>{len(case.get('catalog_admission_proposals', []))}</dd>
          </dl>
        </div>
        <details><summary>Complete adaptation plan</summary><pre>{html.escape(json.dumps(case['adaptation_plan'], ensure_ascii=False, indent=2))}</pre></details>
        <details><summary>Complete synthesis plan</summary><pre>{html.escape(json.dumps(case['synthesis_plan'], ensure_ascii=False, indent=2))}</pre></details>
        <details><summary>Catalog admission proposals</summary><pre>{html.escape(json.dumps(case.get('catalog_admission_proposals', []), ensure_ascii=False, indent=2))}</pre></details>
        """.strip()
    carried = case.get("carried_review_evidence")
    source_attrs = " checked disabled" if carried and carried["source_verified"] else ""
    actual_attrs = " checked disabled" if carried and carried["actual_benchmarks_verified"] else ""
    carried_note = ""
    if carried:
        carried_note = (
            '<p class="carried">Source paper and actual benchmark list carried from Round '
            f"{carried['from_iteration']} review by {html.escape(carried['reviewer_id'])}; "
            "the paper/evidence scope is unchanged. Only the updated recommendation comparison needs a new judgement.</p>"
        )
    card = f"""
    <article class="case" data-case-id="{html.escape(case['case_id'], quote=True)}">
      <div class="case-head">
        <div class="case-number">CASE {index + 1}</div>
        <h2>{html.escape(case['source_title'])}</h2>
        <a class="paper-link" href="{html.escape(case['source_url'], quote=True)}" target="_blank" rel="noopener noreferrer">Open official arXiv source ↗</a>
        <p><strong>Source sections used before anonymization:</strong> Introduction: {html.escape(_list_text(source_sections['introduction']))}; Method: {html.escape(_list_text(source_sections['method']))}.</p>
        <p>Matcher phase used only <code>{html.escape(case['matcher_visible_input'])}</code>. Paper identity and actual benchmarks were revealed after the worker exited.</p>
      </div>
      <div class="case-body">
        <h3>Benchmarks actually used by the paper</h3>
        <table><thead><tr><th>Role</th><th>Benchmark</th><th>Paper section</th><th>Selected</th><th>Rank</th></tr></thead><tbody>{''.join(actual_rows)}</tbody></table>

        <h3>Auto-Bench selected portfolio</h3>
        <table><thead><tr><th>Rank</th><th>Recommendation</th><th>Score</th><th>Selection role</th><th>Role in paper</th></tr></thead><tbody>{''.join(selected_rows)}</tbody></table>

        <div class="comparison">
          <h3>Direct comparison</h3>
          <dl>
            <dt>Selected primary matches</dt><dd>{html.escape(_list_text(comparison['selected_primary_matches']))}</dd>
            <dt>Selected secondary matches</dt><dd>{html.escape(_list_text(comparison['selected_secondary_matches']))}</dd>
            <dt>Selected post-freeze catalog matches</dt><dd>{html.escape(_list_text(comparison.get('selected_admitted_matches', [])))}</dd>
            <dt>Primary missing from selected</dt><dd>{html.escape(_list_text(comparison['primary_missing_from_selected']))}</dd>
            <dt>Secondary missing from selected</dt><dd>{html.escape(_list_text(comparison['secondary_missing_from_selected']))}</dd>
            <dt>Post-freeze catalog items missing from selected</dt><dd>{html.escape(_list_text(comparison.get('admitted_missing_from_selected', [])))}</dd>
            <dt>Selected but absent from paper</dt><dd>{html.escape(_list_text(comparison['selected_not_used_in_paper']))}</dd>
            <dt>Top-6 primary matches</dt><dd>{html.escape(_list_text(comparison['top_6_primary_matches']))}</dd>
            <dt>Top-6 post-freeze catalog matches</dt><dd>{html.escape(_list_text(comparison.get('top_6_admitted_matches', [])))}</dd>
          </dl>
        </div>
{route_context}

        <details><summary>Exact anonymized Introduction given to the matcher</summary><pre>{html.escape(visible['introduction'])}</pre></details>
        <details><summary>Exact anonymized Method given to the matcher</summary><pre>{html.escape(visible['method'])}</pre></details>
        <details><summary>Complete Top-6 recommendation record</summary><pre>{html.escape(json.dumps(case['top_6_details'], ensure_ascii=False, indent=2))}</pre></details>

        <section class="human-check">
          <h3>Your literature check</h3>
{carried_note}
          <label><input type="checkbox" data-field="source_verified"{source_attrs}> I opened the source paper and verified the named evidence sections.</label>
          <label><input type="checkbox" data-field="actual_benchmarks_verified"{actual_attrs}> I confirmed the benchmark list actually used by the paper.</label>
          <label><input type="checkbox" data-field="comparison_reviewed"> I compared the paper benchmark list with Selected and Top-6 recommendations.</label>
          <label class="field">Judgement
            <select data-field="decision"><option value="">Select</option><option>MATCH</option><option>PARTIAL</option><option>MISMATCH</option></select>
          </label>
          <label class="field">Notes
            <textarea data-field="notes" placeholder="Record whether the recommendation recovered the paper benchmarks and which extras or misses matter."></textarea>
          </label>
        </section>
      </div>
    </article>
    """
    return card.strip() + "\n"


def _render_iteration_summary(comparison: dict[str, Any] | None) -> str:
    """Render the previous human verdict and concrete portfolio changes."""

    if not comparison:
        return ""
    previous_iteration = int(comparison.get("previous_iteration", 1))
    current_iteration = int(comparison.get("current_iteration", 2))
    rows = []
    for case in comparison["cases"]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(case['case_id'])}</td>"
            f"<td>{html.escape(str(case['previous_human_decision']))}</td>"
            f"<td>{html.escape(str(case['previous_human_notes']))}</td>"
            f"<td>{html.escape(_list_text(case['before']['selected']))}</td>"
            f"<td>{html.escape(_list_text(case['after']['selected']))}</td>"
            f"<td>{case['before']['selected_modeled_recall']:.3f} → {case['after']['selected_modeled_recall']:.3f}</td>"
            f"<td>{html.escape(_list_text(case['unmodeled_gold']))}</td>"
            "</tr>"
        )
    return f"""
    <section class="protocol iteration-summary">
      <h2>What changed after your Round {previous_iteration} audit</h2>
      <p>Previous aggregate human status: <strong>{html.escape(comparison['aggregate']['previous_human_status'])}</strong>. Round {current_iteration} is a feedback-driven regression on the same papers; newly modeled and still-outside-catalog choices remain visible.</p>
      <table><thead><tr><th>Case</th><th>Previous judgement</th><th>Previous note</th><th>Selected before</th><th>Selected now</th><th>Modeled recall</th><th>Still outside catalog</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
    </section>
    """.strip()


def render_audit_html(audit: dict[str, Any]) -> str:
    """Render the complete post-match audit as a self-contained HTML file.

    All case data is embedded locally, while only the frozen case IDs are put
    into the JavaScript scope. The script validates every checkbox, judgement,
    note, and reviewer ID before downloading a submission JSON file.
    """

    cards = "".join(_render_case(case, index) for index, case in enumerate(audit["cases"]))
    iteration = int(audit.get("iteration", 1))
    display_label = audit.get("display_label") or f"Auto-Bench Blind Literature Audit — Round {iteration}"
    submission_filename = audit.get("submission_filename") or f"literature_audit_submission_round_{iteration}.json"
    summary = _render_iteration_summary(audit.get("iteration_comparison"))
    carried_reviewers = sorted(
        {
            case["carried_review_evidence"]["reviewer_id"]
            for case in audit["cases"]
            if "carried_review_evidence" in case
        }
    )
    prefilled_reviewer = carried_reviewers[0] if len(carried_reviewers) == 1 else ""
    scope = _json_for_script(
        {
            "audit_id": audit["audit_id"],
            "scope_snapshot": audit["submission_scope_snapshot"],
            "case_ids": [case["case_id"] for case in audit["cases"]],
            "iteration": iteration,
            "submission_filename": submission_filename,
        }
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(display_label)}</title>
  <style>
    :root {{ --ink:#172033; --muted:#606b80; --paper:#f4f6fb; --card:#fff; --line:#d9dfeb; --blue:#2e54ce; --green:#147653; --amber:#9b5b00; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:var(--paper); font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
    header {{ padding:38px max(24px,calc((100vw - 1180px)/2)); color:white; background:linear-gradient(125deg,#14213d,#315bd5); }}
    header h1 {{ margin:0 0 10px; font-size:32px; }} header p {{ max-width:920px; margin:0; opacity:.92; }}
    main {{ max-width:1180px; margin:26px auto 90px; padding:0 24px; }}
    .protocol,.case {{ background:var(--card); border:1px solid var(--line); border-radius:15px; box-shadow:0 7px 24px rgba(31,48,84,.08); }}
    .protocol {{ padding:22px; }} .case {{ margin:26px 0; overflow:hidden; }}
    .case-head {{ padding:22px 24px; background:#edf2ff; border-bottom:1px solid var(--line); }} .case-head h2 {{ margin:3px 0 8px; }}
    .case-number {{ color:var(--blue); font-weight:800; letter-spacing:.08em; font-size:12px; }} .paper-link {{ color:var(--blue); font-weight:700; }}
    .case-body {{ padding:24px; }} h3 {{ margin:26px 0 10px; }}
    table {{ width:100%; border-collapse:collapse; margin:10px 0 20px; }} th,td {{ border:1px solid var(--line); text-align:left; padding:9px 10px; vertical-align:top; }} th {{ background:#f3f5fa; }}
    .comparison {{ padding:2px 17px 16px; border-left:4px solid var(--blue); background:#f7f9ff; }} dl {{ display:grid; grid-template-columns:250px 1fr; gap:7px 16px; }} dt {{ font-weight:700; }} dd {{ margin:0; }}
    details {{ margin:12px 0; border:1px solid var(--line); border-radius:9px; padding:10px 12px; }} summary {{ cursor:pointer; font-weight:700; }} pre {{ white-space:pre-wrap; overflow-wrap:anywhere; }}
    .human-check {{ margin-top:24px; padding:20px; border:2px solid #b9c7ed; border-radius:12px; }} .human-check > label:not(.field) {{ display:block; margin:10px 0; }} .carried {{ padding:10px 12px; color:var(--green); background:#edf9f4; border-left:4px solid var(--green); }}
    .field {{ display:block; margin-top:14px; font-weight:700; }} select,textarea,input[type="text"] {{ width:100%; margin-top:5px; padding:9px 10px; border:1px solid #aeb8cc; border-radius:8px; background:white; font:inherit; }} textarea {{ min-height:95px; resize:vertical; }}
    .footer {{ position:sticky; bottom:0; display:flex; gap:12px; align-items:center; flex-wrap:wrap; padding:14px 16px; background:rgba(255,255,255,.97); border:1px solid var(--line); border-radius:12px; box-shadow:0 -5px 24px rgba(31,48,84,.12); }}
    button {{ border:0; border-radius:9px; padding:10px 16px; color:white; background:var(--blue); font-weight:750; cursor:pointer; }} #message {{ color:var(--amber); font-weight:700; }}
    @media(max-width:760px) {{ dl {{ grid-template-columns:1fr; }} table {{ display:block; overflow-x:auto; }} }}
  </style>
</head>
<body>
  <header><h1>{html.escape(display_label)}</h1><p>The matcher first saw only anonymized Introduction and Method text. This post-run page now reveals each source paper and its experiment-derived benchmark list so you can verify whether Auto-Bench recovered the choices made by the paper.</p></header>
  <main>
    <section class="protocol">
      <h2>Human audit protocol</h2>
      <ol><li>Open the official paper link unless its unchanged source check is carried from the prior round.</li><li>Confirm the actual benchmark list unless that unchanged check is carried forward.</li><li>Compare the current Selected and Top-6 recommendations with the paper benchmark list.</li><li>Read route and synthesis information as supporting context.</li><li>Choose MATCH, PARTIAL, or MISMATCH and record the important misses or extras.</li></ol>
      <label class="field">Reviewer ID<input id="reviewer-id" type="text" value="{html.escape(prefilled_reviewer, quote=True)}" placeholder="Your name, initials, or stable internal identifier"></label>
    </section>
{summary}
    {cards}
    <div class="footer"><button id="download" type="button">Validate and download audit JSON</button><span id="progress"></span><span id="message" role="status"></span></div>
  </main>
  <script id="audit-scope" type="application/json">{scope}</script>
  <script>
    const scope = JSON.parse(document.getElementById('audit-scope').textContent);
    function collect(validate) {{
      const reviewerId = document.getElementById('reviewer-id').value.trim();
      const errors = [];
      if (!reviewerId) errors.push('Reviewer ID is empty');
      const reviews = Array.from(document.querySelectorAll('.case')).map((card) => {{
        const caseId = card.dataset.caseId;
        const sourceVerified = card.querySelector('[data-field="source_verified"]').checked;
        const actualVerified = card.querySelector('[data-field="actual_benchmarks_verified"]').checked;
        const comparisonReviewed = card.querySelector('[data-field="comparison_reviewed"]').checked;
        const decision = card.querySelector('[data-field="decision"]').value;
        const notes = card.querySelector('[data-field="notes"]').value.trim();
        if (validate && !sourceVerified) errors.push(caseId + ': source paper not verified');
        if (validate && !actualVerified) errors.push(caseId + ': actual benchmarks not verified');
        if (validate && !comparisonReviewed) errors.push(caseId + ': comparison not reviewed');
        if (validate && !decision) errors.push(caseId + ': judgement is empty');
        if (validate && !notes) errors.push(caseId + ': notes are empty');
        return {{case_id:caseId, source_verified:sourceVerified, actual_benchmarks_verified:actualVerified, comparison_reviewed:comparisonReviewed, decision:decision || null, notes:notes || null}};
      }});
      return {{payload:{{schema_version:2, audit_id:scope.audit_id, iteration:scope.iteration, scope_snapshot:scope.scope_snapshot, reviewer_id:reviewerId || null, reviews:reviews}}, errors:errors}};
    }}
    function updateProgress() {{
      const reviews = collect(false).payload.reviews;
      const complete = reviews.filter((row) => row.source_verified && row.actual_benchmarks_verified && row.comparison_reviewed && row.decision && row.notes).length;
      document.getElementById('progress').textContent = 'Complete ' + complete + ' / ' + scope.case_ids.length;
    }}
    document.querySelectorAll('input,select,textarea').forEach((element) => element.addEventListener('input', updateProgress));
    document.getElementById('download').addEventListener('click', () => {{
      const result = collect(true); const message = document.getElementById('message');
      if (result.errors.length) {{ message.textContent = result.errors.join('; '); return; }}
      const blob = new Blob([JSON.stringify(result.payload, null, 2) + '\\n'], {{type:'application/json'}});
      const anchor = document.createElement('a'); anchor.href = URL.createObjectURL(blob); anchor.download = scope.submission_filename; anchor.click(); URL.revokeObjectURL(anchor.href);
      message.textContent = 'Audit JSON downloaded';
    }});
    updateProgress();
  </script>
</body>
</html>
"""


def prepare_literature_audit(
    evaluation_path: str | Path,
    output_dir: str | Path,
    *,
    workspace_root: str | Path,
    iteration: int = 1,
    iteration_comparison: dict[str, Any] | None = None,
    display_label: str | None = None,
    submission_filename: str | None = None,
    prior_audit_path: str | Path | None = None,
    prior_submission_path: str | Path | None = None,
    case_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a source-revealed audit package from a blind evaluation.

    The function reopens each matcher-visible JSON to show the exact text used,
    joins it with paper identity and benchmark gold already added by the
    post-run evaluator, and writes the data, interactive HTML, blank submission
    template, and pending verdict as four independently inspectable artifacts.
    """

    workspace = Path(workspace_root)
    evaluation = json.loads(Path(evaluation_path).read_text(encoding="utf-8"))
    evaluation_cases = evaluation["cases"]
    requested_case_ids = set(case_ids or [case["case_id"] for case in evaluation_cases])
    known_case_ids = {case["case_id"] for case in evaluation_cases}
    unknown_case_ids = sorted(requested_case_ids - known_case_ids)
    if unknown_case_ids:
        raise ValueError(f"unknown audit case IDs: {unknown_case_ids}")
    if not requested_case_ids:
        raise ValueError("case_ids must contain at least one case")
    cases = []
    for case in evaluation_cases:
        if case["case_id"] not in requested_case_ids:
            continue
        visible_path = workspace / case["matcher_visible_input"]
        visible = json.loads(visible_path.read_text(encoding="utf-8"))
        cases.append({**case, "visible_input": {"introduction": visible["introduction"], "method": visible["method"]}})
    if (prior_audit_path is None) != (prior_submission_path is None):
        raise ValueError("prior_audit_path and prior_submission_path must be supplied together")
    carried_count = 0
    if prior_audit_path is not None and prior_submission_path is not None:
        prior_audit = json.loads(Path(prior_audit_path).read_text(encoding="utf-8"))
        prior_submission = json.loads(Path(prior_submission_path).read_text(encoding="utf-8"))
        carried_count = _carry_prior_source_checks(cases, prior_audit, prior_submission)
    audit_id = _default_audit_id(display_label, iteration, cases)
    audit = {
        "schema_version": "2.0",
        "audit_id": audit_id,
        "iteration": iteration,
        "submission_scope_snapshot": _submission_scope_snapshot(cases),
        "protocol": {
            "matcher_input": ["introduction", "method", "constraints"],
            "paper_identity_visible_to_matcher": False,
            "paper_benchmarks_visible_to_matcher": False,
            "source_revealed_after_matching": True,
            "human_task": "verify the source paper benchmark list and compare it with Auto-Bench recommendations",
            "carried_source_and_gold_checks": carried_count,
            "route_context_is_informational": True,
            "full_evaluation_case_count": len(evaluation_cases),
            "audit_case_count": len(cases),
            "changed_case_filter": [case["case_id"] for case in cases],
        },
        "aggregate": evaluation["aggregate"],
        "cases": cases,
    }
    if display_label:
        audit["display_label"] = display_label
    if submission_filename:
        audit["submission_filename"] = submission_filename
    if iteration_comparison:
        audit["iteration_comparison"] = {
            **iteration_comparison,
            "cases": [
                case
                for case in iteration_comparison["cases"]
                if case["case_id"] in requested_case_ids
            ],
        }
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    audit_json = root / "literature_audit.json"
    audit_html = root / "literature_audit.html"
    review_template = root / "literature_audit_review_template.json"
    pending_verdict = root / "pending_verdict.json"
    audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_html.write_text(render_audit_html(audit), encoding="utf-8")
    template_reviews = []
    for case in cases:
        review = {
            "case_id": case["case_id"],
            "source_verified": True if "carried_review_evidence" in case else None,
            "actual_benchmarks_verified": True if "carried_review_evidence" in case else None,
            "comparison_reviewed": None,
            "decision": None,
            "notes": None,
        }
        template_reviews.append(review)
    template = {
        "schema_version": 2,
        "audit_id": audit_id,
        "iteration": iteration,
        "scope_snapshot": audit["submission_scope_snapshot"],
        "reviewer_id": next(
            (
                case["carried_review_evidence"]["reviewer_id"]
                for case in cases
                if "carried_review_evidence" in case
            ),
            None,
        ),
        "reviews": template_reviews,
    }
    review_template.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pending = {
        "status": "HUMAN_LITERATURE_AUDIT_REQUIRED",
        "audit_id": audit_id,
        "expected_case_ids": [case["case_id"] for case in cases],
        "pending_case_ids": [case["case_id"] for case in cases],
    }
    pending_verdict.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "case_count": len(cases),
        "audit_id": audit_id,
        "carried_source_and_gold_checks": carried_count,
        "audit_json": str(audit_json),
        "audit_html": str(audit_html),
        "review_template": str(review_template),
        "pending_verdict": str(pending_verdict),
    }


def evaluate_literature_audit(
    submission: dict[str, Any],
    audit_scope: dict[str, Any],
) -> dict[str, Any]:
    """Validate one human comparison against every case in the frozen scope.

    A case is complete only when the source, actual benchmark list, and direct
    comparison were all checked and accompanied by a decision plus notes. The
    aggregate status preserves the strongest finding: MISMATCH, then PARTIAL,
    then CONFIRMED; any incomplete case keeps the audit pending.
    """

    expected = [case["case_id"] for case in audit_scope["cases"]]
    audit_id = _clean_text(audit_scope.get("audit_id"))
    if audit_id and _clean_text(submission.get("audit_id")) != audit_id:
        return {
            "status": "HUMAN_LITERATURE_AUDIT_REQUIRED",
            "reason": "submission scope does not match the current literature audit",
            "audit_id": audit_id,
            "pending_case_ids": expected,
        }
    expected_snapshot = audit_scope.get("submission_scope_snapshot")
    if expected_snapshot is not None and submission.get("scope_snapshot") != expected_snapshot:
        return {
            "status": "HUMAN_LITERATURE_AUDIT_REQUIRED",
            "reason": "submission recommendation snapshot does not match the current audit output",
            "audit_id": audit_id,
            "pending_case_ids": expected,
        }
    reviewer_id = _clean_text(submission.get("reviewer_id"))
    reviews = submission.get("reviews")
    if not reviewer_id or not isinstance(reviews, list):
        return {
            "status": "HUMAN_LITERATURE_AUDIT_REQUIRED",
            "reason": "reviewer identity or review list is incomplete",
            "pending_case_ids": expected,
        }
    by_case = {str(review.get("case_id", "")): review for review in reviews}
    pending = []
    decisions = []
    items = []
    for case_id in expected:
        review = by_case.get(case_id)
        if review is None:
            pending.append(case_id)
            items.append({"case_id": case_id, "status": "PENDING", "reason": "case review is missing"})
            continue
        required_checks = ["source_verified", "actual_benchmarks_verified", "comparison_reviewed"]
        complete = all(review.get(field) is True for field in required_checks)
        decision = _clean_text(review.get("decision")).upper()
        notes = _clean_text(review.get("notes"))
        if not complete or decision not in AUDIT_DECISIONS or not notes:
            pending.append(case_id)
            items.append({"case_id": case_id, "status": "PENDING", "reason": "checks, judgement, or notes are incomplete"})
            continue
        decisions.append(decision)
        items.append({"case_id": case_id, "status": decision, "notes": notes})
    if pending:
        status = "HUMAN_LITERATURE_AUDIT_REQUIRED"
        reason = "at least one source-paper comparison is incomplete"
    elif "MISMATCH" in decisions:
        status = "LITERATURE_AUDIT_MISMATCH"
        reason = "the human audit found at least one benchmark-matching failure"
    elif "PARTIAL" in decisions:
        status = "LITERATURE_AUDIT_PARTIAL"
        reason = "the human audit found at least one partial benchmark match"
    else:
        status = "LITERATURE_AUDIT_CONFIRMED"
        reason = "the human audit confirmed every source-paper comparison"
    return {
        "status": status,
        "reason": reason,
        "reviewer_id": reviewer_id,
        "audit_id": audit_id or None,
        "expected_case_ids": expected,
        "pending_case_ids": pending,
        "items": items,
    }
