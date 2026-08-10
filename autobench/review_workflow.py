"""Prepare independent, self-contained human review assignments."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Iterable

from .review_gate import REVIEWER_SLOTS, RUBRIC_DIMENSIONS, RUBRIC_GUIDANCE


def _portable_path(path: Path) -> str:
    """Represent a source artifact relative to the active workspace when possible."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def _candidate_context(plan: dict[str, Any], benchmark_id: str) -> dict[str, Any]:
    if benchmark_id == "NO_DIRECT_MATCH":
        return {
            "benchmark_id": benchmark_id,
            "name": "New benchmark synthesis proposal",
            "source_url": None,
            "selected_candidate": None,
            "metric_plan": [],
            "review_target": "Assess whether the proposed new benchmark and synthesis protocol fit the method.",
        }
    candidate = next(
        (item for item in plan["ranked_candidates"] if item["benchmark_id"] == benchmark_id),
        None,
    )
    if candidate is None:
        raise ValueError(f"selected benchmark {benchmark_id} is absent from ranked candidates")
    metric_plan = [item for item in plan["metric_plan"] if item["benchmark_id"] == benchmark_id]
    return {
        "benchmark_id": benchmark_id,
        "name": candidate["name"],
        "source_url": candidate["source_url"],
        "selected_candidate": candidate,
        "metric_plan": metric_plan,
        "review_target": "Assess direct suitability and any proposed adaptation for this benchmark.",
    }


def build_review_items(plan_paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    """Build full-context items without opening hidden blind-test labels."""

    items: list[dict[str, Any]] = []
    for raw_path in sorted((Path(path) for path in plan_paths), key=lambda path: str(path)):
        plan = json.loads(raw_path.read_text(encoding="utf-8"))
        visible_input = plan.get("visible_input")
        if not isinstance(visible_input, dict):
            raise ValueError(f"plan lacks matcher-visible Introduction and Method: {raw_path}")
        benchmark_ids = plan["selected_benchmarks"] or ["NO_DIRECT_MATCH"]
        for benchmark_id in benchmark_ids:
            items.append(
                {
                    "case_id": plan["case_id"],
                    "benchmark_id": benchmark_id,
                    "visible_input": visible_input,
                    "route": plan["route"],
                    "route_reason": plan["route_reason"],
                    "coverage_ratio": plan["coverage_ratio"],
                    "profile": plan["profile"],
                    "candidate": _candidate_context(plan, benchmark_id),
                    "ranked_candidates": plan["ranked_candidates"],
                    "catalog_admission_proposals": plan.get("catalog_admission_proposals", []),
                    "adaptation_plan": plan["adaptation_plan"],
                    "synthesis_plan": plan["synthesis_plan"],
                    "matching_provenance": {
                        "input_fields": plan["provenance"]["input_fields"],
                        "blind_gold_loaded": plan["provenance"]["blind_gold_loaded"],
                        "leakage_scan": plan["provenance"]["leakage_scan"],
                        "catalog_records": plan["provenance"]["catalog_records"],
                        "online_search": plan["provenance"]["online_search"],
                        "decision_backend": plan["provenance"]["decision_backend"],
                    },
                    "source_plan": _portable_path(raw_path),
                }
            )
    if not items:
        raise ValueError("no benchmark plans were supplied for human review")
    return items


def _blank_review(item: dict[str, Any], reviewer_slot: str) -> dict[str, Any]:
    return {
        "case_id": item["case_id"],
        "benchmark_id": item["benchmark_id"],
        "reviewer_slot": reviewer_slot,
        "reviewer_id": None,
        "scores": {dimension: None for dimension in RUBRIC_DIMENSIONS},
        "provenance_confirmed": None,
        "independence_attested": None,
        "decision": None,
        "notes": None,
    }


def _write_master_csv(path: Path, items: list[dict[str, Any]]) -> int:
    rows = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "case_id",
                "benchmark_id",
                "reviewer_slot",
                "reviewer_id",
                *RUBRIC_DIMENSIONS,
                "provenance_confirmed",
                "independence_attested",
                "decision",
                "notes",
            ]
        )
        for item in items:
            for reviewer_slot in REVIEWER_SLOTS:
                writer.writerow(
                    [
                        item["case_id"],
                        item["benchmark_id"],
                        reviewer_slot,
                        "",
                        *([""] * len(RUBRIC_DIMENSIONS)),
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                rows += 1
    return rows


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def render_reviewer_html(assignment: dict[str, Any]) -> str:
    """Render a local, dependency-free reviewer form with full evidence."""

    slot = assignment["reviewer_slot"]
    data = _json_for_script(assignment)
    title = html.escape(f"Auto-Bench Independent Review · {slot}")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#5d687d; --line:#d8deea; --paper:#f6f8fc; --card:#fff; --accent:#3157d5; --good:#17754d; --warn:#a45a00; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    header {{ background:linear-gradient(120deg,#172033,#3157d5); color:white; padding:36px max(24px,calc((100vw - 1180px)/2)); }}
    header h1 {{ margin:0 0 8px; font-size:30px; }}
    header p {{ margin:0; max-width:900px; opacity:.9; }}
    main {{ max-width:1180px; margin:24px auto 80px; padding:0 24px; }}
    .panel,.item {{ background:var(--card); border:1px solid var(--line); border-radius:14px; box-shadow:0 6px 22px rgba(29,43,76,.07); }}
    .panel {{ padding:22px; margin-bottom:20px; }}
    .item {{ margin:24px 0; overflow:hidden; }}
    .item-head {{ padding:20px 22px; background:#edf2ff; border-bottom:1px solid var(--line); }}
    .item-body {{ padding:22px; }}
    h2,h3,h4 {{ line-height:1.25; }}
    h2 {{ margin:0 0 6px; }}
    h3 {{ margin:24px 0 10px; }}
    .meta {{ color:var(--muted); }}
    .pill {{ display:inline-block; margin:4px 7px 4px 0; padding:3px 9px; border-radius:999px; background:#e7ecfa; font-size:13px; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; background:#f7f8fb; border:1px solid var(--line); padding:14px; border-radius:10px; }}
    details {{ margin:10px 0; border:1px solid var(--line); border-radius:10px; padding:10px 12px; }}
    summary {{ cursor:pointer; font-weight:650; }}
    .rubric {{ display:grid; grid-template-columns:minmax(230px,1fr) 130px; gap:10px 18px; align-items:center; padding:13px 0; border-bottom:1px solid #edf0f5; }}
    .rubric:last-child {{ border-bottom:0; }}
    .rubric label {{ font-weight:650; }}
    .rubric small {{ display:block; color:var(--muted); font-weight:400; }}
    input[type="number"],input[type="text"],select,textarea {{ width:100%; border:1px solid #b8c1d3; border-radius:8px; padding:9px 10px; background:white; color:var(--ink); font:inherit; }}
    textarea {{ min-height:110px; resize:vertical; }}
    .check {{ display:flex; gap:9px; align-items:flex-start; margin:12px 0; }}
    .check input {{ margin-top:5px; }}
    .actions {{ position:sticky; bottom:0; display:flex; gap:12px; align-items:center; background:rgba(255,255,255,.96); border:1px solid var(--line); border-radius:12px; padding:14px 16px; box-shadow:0 -5px 24px rgba(29,43,76,.10); }}
    button {{ border:0; border-radius:9px; padding:10px 16px; background:var(--accent); color:white; cursor:pointer; font-weight:700; }}
    button.secondary {{ background:#e9edf7; color:var(--ink); }}
    #message {{ color:var(--warn); font-weight:650; }}
    a {{ color:var(--accent); }}
    @media (max-width:700px) {{ .rubric {{ grid-template-columns:1fr; }} .actions {{ flex-wrap:wrap; }} }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p>每位评审独立检查完整的 Introduction、Method、候选证据、指标、适配与合成方案；本页面不包含另一位评审的答案，也不包含论文隐藏实验标签。</p>
  </header>
  <main>
    <section class="panel">
      <h2>评审身份与独立性</h2>
      <p class="meta">评审槽位：<strong>{html.escape(slot)}</strong>。请输入可稳定区分真实评审者的姓名缩写或内部编号，模板占位符不会通过门禁。</p>
      <label for="reviewer-id"><strong>Reviewer ID</strong></label>
      <input id="reviewer-id" type="text" autocomplete="off" placeholder="请输入真实评审者标识">
      <label class="check"><input id="independence" type="checkbox"><span>我确认本次判断由本人独立完成，填写时未查看另一位评审的评分或结论。</span></label>
    </section>
    <section class="panel">
      <h2>评分规则</h2>
      <p>每个维度按 1–5 分评分。通过条件：总均分至少 4.0、每个维度均分至少 3.0、两位评审每个维度差值至多 1.0、来源确认和显式批准均完成。</p>
      <div id="rubric-guide"></div>
    </section>
    <div id="items"></div>
    <div class="actions">
      <button id="download" type="button">校验并下载 JSON</button>
      <button id="copy" class="secondary" type="button">校验并复制 JSON</button>
      <span id="progress"></span>
      <span id="message" role="status"></span>
    </div>
  </main>
  <script id="assignment-data" type="application/json">{data}</script>
  <script>
    const assignment = JSON.parse(document.getElementById('assignment-data').textContent);
    const dimensions = assignment.rubric_dimensions;
    const guide = document.getElementById('rubric-guide');
    dimensions.forEach((dimension) => {{
      const row = document.createElement('div');
      row.className = 'rubric';
      const label = document.createElement('div');
      label.innerHTML = '<strong>' + dimension + '</strong><small></small>';
      label.querySelector('small').textContent = assignment.rubric_guidance[dimension];
      const scale = document.createElement('div');
      scale.textContent = '1 = weak · 5 = strong';
      row.append(label, scale);
      guide.appendChild(row);
    }});

    function jsonBlock(value) {{
      const pre = document.createElement('pre');
      pre.textContent = JSON.stringify(value, null, 2);
      return pre;
    }}

    function addDetails(parent, title, value, open) {{
      const details = document.createElement('details');
      details.open = Boolean(open);
      const summary = document.createElement('summary');
      summary.textContent = title;
      details.append(summary, jsonBlock(value));
      parent.appendChild(details);
    }}

    function renderItems() {{
      const root = document.getElementById('items');
      assignment.items.forEach((item, index) => {{
        const article = document.createElement('article');
        article.className = 'item';
        article.dataset.index = String(index);
        const head = document.createElement('div');
        head.className = 'item-head';
        const heading = document.createElement('h2');
        heading.textContent = (index + 1) + '. ' + item.case_id + ' / ' + item.benchmark_id;
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = 'Route: ' + item.route + ' · Coverage: ' + Number(item.coverage_ratio * 100).toFixed(1) + '%';
        head.append(heading, meta);
        const body = document.createElement('div');
        body.className = 'item-body';

        const inputTitle = document.createElement('h3');
        inputTitle.textContent = 'Matcher-visible Introduction';
        body.append(inputTitle, jsonBlock(item.visible_input.introduction));
        const methodTitle = document.createElement('h3');
        methodTitle.textContent = 'Matcher-visible Method';
        body.append(methodTitle, jsonBlock(item.visible_input.method));

        const candidateTitle = document.createElement('h3');
        candidateTitle.textContent = 'Review target: ' + item.candidate.name;
        body.appendChild(candidateTitle);
        if (item.candidate.source_url) {{
          const link = document.createElement('a');
          link.href = item.candidate.source_url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = '打开候选 Benchmark 的主来源';
          body.appendChild(link);
        }}
        addDetails(body, 'Capability profile', item.profile, true);
        addDetails(body, 'Selected candidate evidence and metric plan', item.candidate, true);
        addDetails(body, 'All ranked candidates', item.ranked_candidates, false);
        addDetails(body, 'Catalog admission proposals', item.catalog_admission_proposals, false);
        addDetails(body, 'Adaptation plan', item.adaptation_plan, true);
        addDetails(body, 'Synthesis plan', item.synthesis_plan, true);
        addDetails(body, 'Matching provenance', item.matching_provenance, false);

        const scoreTitle = document.createElement('h3');
        scoreTitle.textContent = 'Human suitability scores';
        body.appendChild(scoreTitle);
        dimensions.forEach((dimension) => {{
          const row = document.createElement('div');
          row.className = 'rubric';
          const label = document.createElement('label');
          label.htmlFor = 'score-' + index + '-' + dimension;
          label.textContent = dimension;
          const small = document.createElement('small');
          small.textContent = assignment.rubric_guidance[dimension];
          label.appendChild(small);
          const input = document.createElement('input');
          input.type = 'number';
          input.min = '1';
          input.max = '5';
          input.step = '1';
          input.id = 'score-' + index + '-' + dimension;
          input.dataset.dimension = dimension;
          input.addEventListener('input', updateProgress);
          row.append(label, input);
          body.appendChild(row);
        }});

        const provenanceLabel = document.createElement('label');
        provenanceLabel.className = 'check';
        provenanceLabel.innerHTML = '<input type="checkbox" data-field="provenance"><span>我已打开并核对候选 Benchmark 的主来源及所列指标；对于新合成方案，我已核对其 base 数据来源与变换记录。</span>';
        provenanceLabel.querySelector('input').addEventListener('change', updateProgress);
        body.appendChild(provenanceLabel);

        const decisionLabel = document.createElement('label');
        decisionLabel.innerHTML = '<strong>Decision</strong>';
        const select = document.createElement('select');
        select.dataset.field = 'decision';
        select.innerHTML = '<option value="">请选择</option><option value="APPROVE">APPROVE</option><option value="REJECT">REJECT</option>';
        select.addEventListener('change', updateProgress);
        decisionLabel.appendChild(select);
        body.appendChild(decisionLabel);

        const notesLabel = document.createElement('label');
        notesLabel.innerHTML = '<strong>Concrete justification</strong>';
        const notes = document.createElement('textarea');
        notes.dataset.field = 'notes';
        notes.placeholder = '写明至少一个与方法能力、任务覆盖、指标或数据质量直接相关的判断依据。';
        notes.addEventListener('input', updateProgress);
        notesLabel.appendChild(notes);
        body.appendChild(notesLabel);
        article.append(head, body);
        root.appendChild(article);
      }});
    }}

    function collect(validate) {{
      const reviewerId = document.getElementById('reviewer-id').value.trim();
      const independence = document.getElementById('independence').checked;
      const errors = [];
      if (!reviewerId) errors.push('Reviewer ID 未填写');
      if (['reviewer_1','reviewer_2','reviewer1','reviewer2','r1','r2','anonymous','anon','placeholder'].includes(reviewerId.toLowerCase().replaceAll('-', '_').replaceAll(' ', '_'))) errors.push('Reviewer ID 仍是模板占位符');
      if (!independence) errors.push('独立评审声明未确认');
      const reviews = assignment.items.map((item, index) => {{
        const article = document.querySelector('.item[data-index="' + index + '"]');
        const scores = {{}};
        dimensions.forEach((dimension) => {{
          const raw = article.querySelector('[data-dimension="' + dimension + '"]').value;
          scores[dimension] = raw === '' ? null : Number(raw);
          if (validate && (scores[dimension] === null || scores[dimension] < 1 || scores[dimension] > 5)) errors.push(item.case_id + '/' + item.benchmark_id + ': ' + dimension + ' 需要 1–5 分');
        }});
        const provenance = article.querySelector('[data-field="provenance"]').checked;
        const decision = article.querySelector('[data-field="decision"]').value;
        const notes = article.querySelector('[data-field="notes"]').value.trim();
        if (validate && !provenance) errors.push(item.case_id + '/' + item.benchmark_id + ': 来源确认未勾选');
        if (validate && !decision) errors.push(item.case_id + '/' + item.benchmark_id + ': Decision 未填写');
        if (validate && !notes) errors.push(item.case_id + '/' + item.benchmark_id + ': 判断依据未填写');
        return {{
          case_id: item.case_id,
          benchmark_id: item.benchmark_id,
          reviewer_slot: assignment.reviewer_slot,
          reviewer_id: reviewerId || null,
          scores: scores,
          provenance_confirmed: provenance,
          independence_attested: independence,
          decision: decision || null,
          notes: notes || null
        }};
      }});
      return {{reviews: reviews, errors: errors}};
    }}

    function checkedItemCount() {{
      const result = collect(false).reviews;
      return result.filter((review) => dimensions.every((dimension) => review.scores[dimension] !== null) && review.provenance_confirmed && review.decision && review.notes).length;
    }}

    function updateProgress() {{
      document.getElementById('progress').textContent = '完成 ' + checkedItemCount() + ' / ' + assignment.items.length;
    }}

    function validatedPayload() {{
      const result = collect(true);
      const message = document.getElementById('message');
      if (result.errors.length) {{
        message.textContent = '尚有 ' + result.errors.length + ' 项：' + result.errors.join('；');
        return null;
      }}
      message.textContent = '校验通过';
      return {{
        schema_version: assignment.schema_version,
        reviewer_slot: assignment.reviewer_slot,
        reviews: result.reviews
      }};
    }}

    document.getElementById('download').addEventListener('click', () => {{
      const payload = validatedPayload();
      if (!payload) return;
      const blob = new Blob([JSON.stringify(payload, null, 2) + '\\n'], {{type:'application/json'}});
      const anchor = document.createElement('a');
      anchor.href = URL.createObjectURL(blob);
      anchor.download = assignment.reviewer_slot.toLowerCase() + '_submission.json';
      anchor.click();
      URL.revokeObjectURL(anchor.href);
    }});

    document.getElementById('copy').addEventListener('click', async () => {{
      const payload = validatedPayload();
      if (!payload) return;
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2) + '\\n');
      document.getElementById('message').textContent = '校验通过并已复制';
    }});

    document.getElementById('reviewer-id').addEventListener('input', updateProgress);
    document.getElementById('independence').addEventListener('change', updateProgress);
    renderItems();
    updateProgress();
  </script>
</body>
</html>
"""


def prepare_review_bundle(plan_paths: Iterable[str | Path], output_dir: str | Path) -> dict[str, Any]:
    """Write frozen scope, separate assignments, forms, and merge templates."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    items = build_review_items(plan_paths)
    scope = {
        "schema_version": 1,
        "reviewer_slots": list(REVIEWER_SLOTS),
        "pairs": [
            {
                "case_id": item["case_id"],
                "benchmark_id": item["benchmark_id"],
                "route": item["route"],
                "source_plan": item["source_plan"],
            }
            for item in items
        ],
    }
    scope_path = root / "review_scope.json"
    scope_path.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_path = root / "master_review_packet.csv"
    row_count = _write_master_csv(csv_path, items)
    template = [
        _blank_review(item, reviewer_slot)
        for item in items
        for reviewer_slot in REVIEWER_SLOTS
    ]
    template_path = root / "review_submission_template.json"
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assignment_paths: dict[str, str] = {}
    html_paths: dict[str, str] = {}
    for reviewer_slot in REVIEWER_SLOTS:
        stem = reviewer_slot.casefold()
        assignment = {
            "schema_version": 1,
            "reviewer_slot": reviewer_slot,
            "independence_protocol": {
                "do_not_share_other_review": True,
                "hidden_paper_benchmarks_excluded": True,
                "actual_reviewer_identity_required": True,
            },
            "score_range": [1, 5],
            "rubric_dimensions": list(RUBRIC_DIMENSIONS),
            "rubric_guidance": RUBRIC_GUIDANCE,
            "items": items,
        }
        assignment_path = root / f"{stem}_assignment.json"
        assignment_path.write_text(
            json.dumps(assignment, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        html_path = root / f"{stem}_packet.html"
        html_path.write_text(render_reviewer_html(assignment), encoding="utf-8")
        assignment_paths[reviewer_slot] = str(assignment_path)
        html_paths[reviewer_slot] = str(html_path)

    return {
        "item_count": len(items),
        "review_row_count": row_count,
        "scope": str(scope_path),
        "master_csv": str(csv_path),
        "submission_template": str(template_path),
        "assignments": assignment_paths,
        "html_packets": html_paths,
    }
