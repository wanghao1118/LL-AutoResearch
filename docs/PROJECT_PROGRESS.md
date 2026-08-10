# Project Progress

## 2026-08-05

- Initialized AutoResearch as an independent project.
- Implemented Auto Search MVP:
  - query planning
  - arXiv / OpenAlex / PubMed / CrossRef collectors
  - deduplication
  - explainable ranking
  - paper cards
  - field map
  - evidence-grounded gap report
- Smoke test passed with:
  - topic: `medical VLM temporal lesion change analysis`
  - query count: 10
  - source/query executions: 40
  - raw candidates: 185
  - source failures: 0
  - ranked papers: 20
  - paper cards: 20
  - generated gaps: 3
  - report: `outputs/medical-vlm-temporal-lesion-change-analysis/report.md`
- Added full-text reading pipeline:
  - fetches PDF/HTML for top-ranked papers
  - extracts plain text from PDFs with PyMuPDF
  - splits papers into sections such as abstract, methods, experiments, and limitations
  - feeds section-aware text into paper cards, dataset/metric extraction, and gap evidence
  - writes full-text records into `search_result.json` and a `Full-Text Reading` section in the report
- Full-text smoke test passed with:
  - full-text limit: 6
  - successful full-text reads: 5
  - recorded fetch failures: 1
  - ranked papers: 20
  - paper cards: 20
  - generated gaps: 3
- Added Paper Card v2 and Gap Evidence Scoring:
  - paper cards now include field-level evidence, extraction status, and coverage tags
  - gap finder now scores support/counter/unclear coverage across retrieved papers
  - confidence now includes score reasons and a full-text evidence count
  - report now shows coverage tags and gap coverage statistics
- Gap scoring smoke test passed on `medical VLM temporal lesion change analysis`:
  - lesion-level temporal gap: support `15/20`, counter `5/20`, confidence `0.73`
  - dataset/benchmark gap: support `16/20`, counter `4/20`, confidence `0.74`
  - metric gap: support `8/20`, counter `12/20`, confidence `0.38`
- Added Gap Evidence Chain v2:
  - Semantic Scholar enrichment adds citations, influential citations, references, venue, fields of study, and open-access PDF links
  - paper cards now include optional influence metadata
  - each gap now includes paper-level judgments with `support` / `counter` / `unclear` roles
  - judgments explain missing evidence and include influence score reasons
  - confidence is adjusted when counter-evidence papers have notable influence signals

## 2026-08-07

- Reframed the next core direction from rule-based gap detection to MOC-style gap discovery.
- Key insight:
  - AutoResearch should not find gaps only from single-paper limitations or keyword absence.
  - Strong gaps should emerge from a problem-space map: single-paper notes, topic MOC aggregation, cross-paper comparison, method-family abstraction, shared assumptions, shared bottlenecks, open questions, and experimentable ideas.
- Target thinking pipeline:
  - single-paper insight card
  - topic MOC aggregation
  - cross-paper comparison matrix
  - method pattern and assumption mapping
  - weakness/gap discovery
  - counter-evidence resolution
  - experimentable research opportunity
- Proposed new artifacts:
  - `topic_moc.md`
  - `comparison_matrix.md`
  - `weakness_report.md`
- Proposed Paper Insight Card fields:
  - problem
  - method core
  - evidence
  - assumption
  - limitation
  - relation to other papers
  - inspiration
  - experimentable gap
- Gap types to support:
  - coverage gap
  - assumption gap
  - benchmark gap
  - contradiction gap
  - experimentability gap
- Updated product direction:
  - AutoResearch should become a research-judgment tool that explains how research questions grow from paper relationships, not just a paper search and summary pipeline.
- Implemented MOC-style Gap Discovery v1:
  - added Paper Insight Cards with problem, method core, evidence, assumption, limitation, relation to other papers, inspiration, and experimentable gap
  - added Topic MOC generation for core concepts, paper groups, method patterns, shared assumptions, open questions, and related themes
  - added Cross-paper Comparison Matrix across paper groups, including solves, missing dimensions, assumptions, and benchmark/metric coverage
  - added Weakness Report focused on how each weakness emerges, evidence chain, counter evidence, why still open, experimentable idea, and verification plan
  - added JSON and Markdown artifacts: `paper_insights.json`, `topic_moc.json`, `topic_moc.md`, `comparison_matrix.json`, `comparison_matrix.md`, `weakness_report.md`
- MOC smoke test passed on `medical VLM temporal lesion change analysis`:
  - ranked papers: `12`
  - paper insights: `12`
  - topic MOC groups: `6`
  - comparison rows: `6`
  - generated weaknesses: `3`
  - note: arXiv returned multiple `429`/timeout errors during this run, but OpenAlex/PubMed/CrossRef kept the pipeline running
- Reordered the next roadmap:
  - expand information sources first
  - build and validate the minimum MOC demo
  - only then interpret weakness/gap outputs
- Implemented Source Expansion v1:
  - added Europe PMC as a medical/life-sciences search collector
  - added OpenReview lightweight search as an AI/ML venue collector
  - added Unpaywall DOI-based open-access enrichment for landing page and PDF links
  - added `source_coverage.md` to summarize source execution, ranked contribution, full-text/OA coverage, MOC group coverage, and warnings
  - marked `weakness_report.md` as preliminary and dependent on source/MOC validation
- Source Expansion smoke test passed on `medical VLM temporal lesion change analysis` with `--per-query-limit 1` and enrichment/full-text disabled:
  - source/query executions: `60`
  - sources represented: `arxiv`, `openalex`, `pubmed`, `europepmc`, `crossref`, `openreview`
  - raw results: `openalex=10`, `pubmed=8`, `europepmc=10`, `crossref=9`, `openreview=10`, `arxiv=0`
  - ranked papers: `8`
  - topic MOC groups: `5`
  - comparison rows: `5`
  - note: arXiv still returned `429`/timeout errors and should be handled by source cache/backoff next
- Implemented MOC v2 + Gap Evidence v1 execution plan:
  - expanded Paper Card v2 with `problem`, `method_family`, `core_assumption`, `evidence_type`,
    `missing_capability`, `relation_to_topic`, and `gap_hint`
  - upgraded Topic MOC from simple paper grouping to problem-space MOC nodes with representative
    papers, shared assumptions, method families, datasets/benchmarks, metrics, covered capabilities,
    missing capabilities, open questions, and possible experiments
  - upgraded Comparison Matrix with temporal-input, lesion-localization, change-evaluation, and
    location-consistency columns
  - added explicit `gap_evidence_chains.md`
  - added evidence-backed `research_opportunities.json` and `research_opportunities.md`
  - added source readiness gate: `ready_for_preliminary_gap_analysis` vs `needs_more_evidence`
  - added arXiv local cache, shorter arXiv timeout, and per-run source skipping after repeated
    consecutive failures
- MOC v2 smoke test passed on `medical VLM temporal lesion change analysis` with `--limit 8`,
  `--per-query-limit 1`, and enrichment/full-text disabled:
  - ranked papers: `8`
  - generated gaps: `3`
  - research opportunities: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - MOC groups: `5`
  - source/query rows: `60`
  - arXiv: `0 ok`, `3 failed`, `7 skipped`
  - raw results: `openalex=10`, `pubmed=8`, `europepmc=10`, `crossref=9`, `openreview=10`, `arxiv=0`
  - key artifacts: `source_coverage.md`, `topic_moc.md`, `comparison_matrix.md`,
    `gap_evidence_chains.md`, `research_opportunities.md`, `weakness_report.md`
- Implemented optional LLM-backed Paper Card extraction:
  - added OpenAI-compatible chat-completions integration controlled by `AUTORESEARCH_LLM_API_KEY`,
    `AUTORESEARCH_LLM_MODEL`, and optional `AUTORESEARCH_LLM_BASE_URL`
  - added CLI flags: `--llm-card-limit`, `--llm-model`, and `--llm-timeout`
  - LLM extraction is disabled by default and safe to skip when no key/model is configured
  - each LLM-updated field must cite existing evidence snippet IDs; unsupported fields are ignored
  - added `llm_extractions.json` and an LLM extraction section in `report.md`
  - added tests for fenced JSON parsing, evidence-id validation, and no-key skip behavior
- LLM extraction smoke test passed with API keys intentionally unset:
  - command used `--llm-card-limit 2 --llm-model test-model`
  - `llm_extractions.json` recorded `2` skipped records with a clear missing-key message
  - no external LLM request was made
  - source readiness correctly reported `needs_more_evidence` when the demo was limited to `5`
    ranked papers, validating the readiness gate behavior
- Implemented static Dashboard UI:
  - search runs now automatically write `dashboard.html`
  - added `autoresearch dashboard <output-dir-or-search_result.json>` for regenerating the UI from
    existing artifacts
  - Dashboard tabs: Overview, Papers, MOC, Gaps, Opportunities
  - Overview shows source health, readiness gate, and LLM extraction status
  - Papers view supports filtering and expands evidence snippets
  - MOC view shows problem spaces, shared assumptions, missing capabilities, open questions, and
    possible experiments
  - Gaps view shows confidence, support/counter coverage, and evidence chains
  - Opportunities view shows evidence-bound research question, method, evaluation, baselines,
    ablations, and risks
- Dashboard demo regenerated for `medical VLM temporal lesion change analysis`:
  - ranked papers: `8`
  - generated gaps: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - arXiv: `1 failed`, `9 skipped`
  - dashboard path: `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
- Localized Dashboard UI to Chinese:
  - translated navigation, metric cards, source table, readiness gate, paper-card field labels,
    MOC labels, Gap labels, and Research Opportunity labels
  - added Chinese mappings for common rule-generated signals such as problem spaces, method
    families, missing capabilities, gap claims, evidence roles, readiness reasons, evaluation
    items, baselines, ablations, and risks
  - preserved original paper titles and evidence snippets to avoid distorting source content
  - regenerated `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
- Improved Dashboard interaction for the research-review demo:
  - top actions now navigate within the Chinese dashboard instead of opening Markdown exports
  - Paper Cards, MOC problem spaces, Gap evidence chains, and Research Opportunities are expandable
    panels
  - added a top LLM extraction strip and a detailed LLM extraction table in Overview
  - added Chinese error hints for skipped or failed LLM extraction states
  - changed dashboard HTML language metadata to `zh-CN`
  - ignored repo-local `.cache/` search cache files
- Reran `medical VLM temporal lesion change analysis` with LLM extraction enabled for the top `3`
  paper cards:
  - ranked papers: `8`
  - generated gaps: `3`
  - research opportunities: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - source coverage: arXiv `1 ok / 1 failed / 8 skipped`, CrossRef `0 ok / 1 failed / 9 skipped`,
    OpenAlex `10 ok`, PubMed `10 ok`, Europe PMC `10 ok`, OpenReview `10 ok`
  - LLM extraction model: `gpt-4o-mini`
  - LLM extraction result: `3 failed`, `0 updated`
  - failure reason: OpenAI-compatible endpoint returned `429 Too Many Requests`
  - regenerated `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
- Implemented Domain Profile v1:
  - added `DomainProfile` and `CapabilityDimension` schema objects
  - added profile generation / loading utilities with `auto`, `medical-vlm`, `gui-agent`,
    `llm-agent`, and generic fallback profiles
  - added repository profile seeds: `profiles/medical-vlm.json` and `profiles/gui-agent.json`
  - added CLI command `autoresearch profile <topic>` to generate an inspectable profile JSON
  - added `--profile` to `autoresearch search`, accepting profile ids or custom JSON paths
  - query planning now expands from profile query terms, capability dimensions, benchmark keywords,
    and metric keywords
  - paper cards now receive profile-grounded capability tags such as
    `capability:lesion-level-temporal-change-reasoning` and
    `capability:real-world-long-horizon-workflow`
  - Gap Finder now creates profile-grounded coverage gaps plus generic benchmark and metric gaps
  - non-medical MOC grouping now uses profile capability dimensions instead of medical-only groups
  - dashboard and Markdown report now show the active Domain Profile
  - search runs now write `domain_profile.json`
- Domain Profile smoke tests:
  - `medical VLM temporal lesion change analysis --profile medical-vlm`: `8` papers, `4` gaps,
    dashboard regenerated at `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
  - Medical VLM gaps now include `lesion-level temporal change reasoning`,
    `paired-study benchmark coverage`, benchmark protocol, and target-capability metric coverage
  - `GUI agent benchmark real-world workflow --profile gui-agent`: `8` papers, `4` gaps,
    dashboard generated at `outputs/gui-agent-benchmark-real-world-workflow/dashboard.html`
  - GUI Agent gaps include `failure recovery and self-correction`, `environment reproducibility`,
    benchmark protocol, and target-capability metric coverage
  - limitation found: GUI Agent run still admits some adjacent medical/clinical agent papers because
    ranker and source selection are not fully profile-aware yet
- Implemented Codex-substituted synthesis layer for the later LLM analysis step:
  - added `SynthesisReport` and `SynthesisGapSummary` schema objects
  - added `src/autoresearch/synthesizer.py` to summarize Domain Profile, source quality, MOC
    takeaways, Gap evidence chains, research opportunities, limitations, and next steps in Chinese
  - search runs now write `synthesis.json` and `analysis_report.md`
  - added `autoresearch synthesize <output-dir-or-search_result.json>` to regenerate synthesis from
    existing artifacts
  - Dashboard now includes a Chinese `分析 / 综合分析` tab and a link to `analysis_report.md`
- Rebuilt synthesis demos:
  - Medical VLM analysis report:
    `outputs/medical-vlm-temporal-lesion-change-analysis/analysis_report.md`
  - GUI Agent analysis report:
    `outputs/gui-agent-benchmark-real-world-workflow/analysis_report.md`
- Fixed non-medical profile leakage in rule-based paper-card extraction:
  - GUI/LLM agent profiles no longer reuse medical-only task labels, method-family labels, gap
    hints, dataset fallbacks, metric fallbacks, or lesion localization coverage tags
  - regression test added to ensure a medical-looking paper mixed into a GUI Agent run is treated as
    adjacent evidence instead of forcing medical templates
  - remaining limitation: ranker and source selection can still retrieve adjacent clinical-agent
    papers; this is a source/ranking problem, not a paper-card template problem
- Reframed the near-term LLM strategy as Codex-in-the-loop as the main review path:
  - the program collects papers, extracts cards, builds rule-based MOC/Gaps, and packages evidence
  - Codex manually plays the expensive reasoning role: MOC refinement, Gap rewriting, counter-evidence
    resolution, research opportunity design, and next-step planning
  - local model backends are not part of the current plan; the project should stay controllable
    through explicit Codex Review packets and user-approved review results
- Implemented Codex Manual LLM Review v1:
  - added `autoresearch codex-packet <output-dir-or-search_result.json>` to export
    `codex_review_packet.md`, `codex_review_packet.json`, and `codex_review_result.template.json`
  - added `autoresearch codex-apply <output-dir-or-search_result.json> <codex_review_result.json>`
    to import Codex's structured judgment back into `synthesis`, `topic_moc`, `comparison_matrix`,
    `gaps`, `research_opportunities`, reports, and `dashboard.html`
  - added validation schemas for Codex MOC groups, refined gaps, opportunities, and synthesis fields
  - added tests for packet export and applying Codex review results
- Locked the current project direction:
  - AutoResearch should focus on automated evidence collection plus Codex-reviewed research judgment
  - the next small-step workflow is documented in `docs/CODEX_REVIEW_WORKFLOW.md`
  - Dashboard now makes the judgment source visible: `Rule-generated` vs `Codex-reviewed`
- Planned Profile-Aware Source / Ranker v1 without changing ranking behavior yet:
  - documented the current drift cause: every profile uses the same sources and ranker still has
    hard-coded medical/VLM/temporal assumptions
  - defined source policy, evidence policy, and paper-level evidence tiers:
    `core`, `adjacent`, `noise`, and `unknown`
  - proposed an intentionally small implementation order: relevance fixtures, profile policy schema,
    standalone evidence-tier scoring, then ranker/pipeline/dashboard integration
  - plan is documented in `docs/PROFILE_AWARE_SOURCE_RANKER_PLAN.md`
- Implemented the first three Profile-Aware Source / Ranker steps without changing ranking behavior:
  - added `SourcePolicy` and `EvidencePolicy` to `DomainProfile` with backward-compatible defaults
  - seeded GUI Agent, Medical VLM, LLM Agent, and generic profiles with source/evidence policies
  - added relevance fixtures for GUI Agent and Medical VLM core/adjacent/noise judgments
  - added `score_evidence_tier(paper, profile)` in `src/autoresearch/relevance.py`
  - added tests for profile policy loading, legacy profile compatibility, and fixture tier judgments
  - validation passed: `.venv/bin/pytest` -> 28 passed; `.venv/bin/ruff check .` -> all checks passed

## 2026-08-08

- Integrated Profile-Aware Evidence Tier scoring into the real search path:
  - extended `RankedPaper` and `PaperCard` with `evidence_tier`,
    `evidence_tier_score_delta`, and `evidence_tier_reasons`
  - updated `rank_papers(..., profile=None)` so legacy calls keep old behavior while profile-aware
    calls add `score_evidence_tier` deltas and reasons
  - updated `pipeline.py` to pass the active `domain_profile` into the ranker
  - propagated evidence tiers from ranked papers into paper cards and Codex Review packets
  - added ranker tests for legacy compatibility, GUI Agent medical-noise downranking, Medical VLM
    GUI-noise downranking, and Paper Card tier propagation
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed
- Ran a small GUI Agent demo with profile-aware ranking:
  - command used `--profile gui-agent --limit 12 --per-query-limit 3 --full-text-limit 0`
  - output: `.cache/profile-ranker-demo/gui-agent-benchmark-real-world-workflow`
  - top ranked papers were all labeled `core`
  - `MobileUse`, `GUI-ReWalk`, and `LongHorizonUI` appeared in the ranked set with positive
    evidence-tier deltas
  - OpenAlex returned `429 Too Many Requests` and was skipped after the existing failure threshold
  - Codex Review Packet generation succeeded and includes paper-level evidence tiers
- Added Dashboard evidence-tier display:
  - summary metrics now include core/adjacent/noise evidence counts
  - overview page shows a Chinese evidence-tier distribution table with tier meanings
  - paper cards show `核心证据` / `相邻证据` / `噪声/需降权` / `未判定`
  - expanded paper cards show ranking delta and translated tier reasons such as matched core
    keywords and source-policy decisions
  - regenerated and visually checked the GUI Agent dashboard through a local preview server
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed
- Added a clearer Dashboard mainline page after reviewing the desired MOC-style gap workflow and
  public research-assistant UI patterns:
  - new default `主线` tab presents `核心结论 -> 论文到 Gap 的链条 -> Gap 优先级 -> 推荐切入点`
  - evidence is grouped into core / adjacent / noise columns before the user opens detailed paper cards
  - Gap priority table puts support and counter-evidence next to each candidate weakness
  - the page separates `Rule-generated` from `Codex-reviewed` so users can see whether a claim has
    passed manual Codex review
  - applied the existing Codex Review result to the GUI Agent demo so the visible mainline now
    emphasizes `failure-conditioned GUI workflow benchmark / evaluation`
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed
- Added the first deployment surface for public demos:
  - added a read-only `autoresearch-server` / `autoresearch_server.py` web entrypoint
  - the server lists generated runs and can default to the GUI Agent dashboard mainline
  - added `deploy.sh` modeled after the previous Bench Analysis Workbench deployment pattern
  - added Nginx template for `autoresearch.sugarclaw.top -> 127.0.0.1:8766`
  - documented ECS deployment, output sync, and the current boundary that online job submission is
    not part of this step
  - adjusted deployment to create the virtual environment with Python 3.11 on Ubuntu 22.04 ECS

## 2026-08-10

- Re-scoped the near-term project target from full Gap discovery to evidence-grounded Weakness
  discovery:
  - current target: `Search -> Paper Cards -> MOC -> Weakness Evidence Chain`
  - deferred targets: `Weakness -> Gap -> Design -> Benchmark -> Writing`
  - rationale: a weakness is easier to verify than a final research gap, and it can be inspected with
    support evidence, counter-evidence, evidence quality, and next validation steps
- Appendix: related AutoResearch / Research Agent projects and benchmarks surveyed for positioning:

### Appendix A: Project Landscape

This appendix records adjacent projects found during the AutoResearch positioning discussion. The
main lesson is that many systems already cover literature search, scientific QA, idea generation,
experiment execution, paper replication, and full paper drafting. AutoResearch should therefore avoid
competing as a generic "automatic paper writer" and instead specialize in finding evidence-grounded
weaknesses in a research area.

| Project / System | Link | Main Focus | Relevance To AutoResearch |
|---|---|---|---|
| The AI Scientist | https://arxiv.org/abs/2408.06292 | End-to-end automated ML research: idea generation, code, experiments, figures, paper writing, and simulated review. | Important comparison point, but broader and more end-to-end than the current Weakness Finder target. |
| The AI Scientist-v2 | https://arxiv.org/abs/2504.08066 | Workshop-level automated scientific discovery with more agentic search. | Shows the field is moving toward full-cycle autonomous research, but not specifically weakness evidence chains. |
| AI-Researcher | https://arxiv.org/abs/2505.18705 | Autonomous scientific innovation from literature review and hypothesis generation to implementation and manuscript drafting. | Similar pipeline ambition; useful for understanding end-to-end claims and Scientist-Bench style evaluation. |
| Agent Laboratory | https://arxiv.org/abs/2501.04227 | Research assistant pipeline with literature review, experimentation, and report writing. | Close workflow reference, but assumes the user already provides a research idea; our focus is finding weaknesses before idea design. |
| Karpathy autoresearch | https://github.com/karpathy/autoresearch | Iterative experiment loop: modify code, run short experiments, keep improvements by metric. | Useful inspiration for evidence-preserving loops, but it optimizes a known scalar metric rather than discovering literature weaknesses. |
| OpenResearcher | https://arxiv.org/html/2408.06941v1 | RAG-based scientific research assistant for literature search, filtering, QA, and self-refinement. | Relevant to the search and synthesis layer, but less focused on MOC-style weakness discovery. |
| OpenScholar | https://arxiv.org/abs/2411.14199 | Retrieval-augmented scientific synthesis over a large open-access paper corpus with citation-backed answers. | Strong reference for citation-grounded literature synthesis and evidence attribution. |
| Ai2 ScholarQA | https://allenai.org/blog/ai2-scholarqa | Scientific question answering and literature synthesis across multiple papers. | Useful baseline for citation-backed scientific QA. |
| FutureHouse Crow / Falcon / Owl / Phoenix | https://www.futurehouse.org/research-announcements/launching-futurehouse-platform-ai-agents | Specialized science agents for retrieval, deep literature review, precedent checking, and chemistry workflows. | Strong product reference for task-specific research agents; Owl's "has anyone done X?" is especially relevant to counter-evidence search. |
| Elicit | https://elicit.com/ | Literature review, screening, and structured data extraction for systematic reviews. | Product reference for paper search and extraction UI. |
| SciSpace Deep Review | https://scispace.com/search | Agentic literature review and deep research over academic sources. | Product reference for large-scale literature collection and review generation. |
| BioDiscoveryAgent | https://arxiv.org/abs/2405.17631 | Closed-loop biological experiment design and hypothesis-space navigation. | Domain-specific example of research automation beyond literature review. |

### Appendix B: Benchmark Landscape

The benchmark landscape is fragmented by research-stage capability. This is good news for
AutoResearch: instead of inventing a full benchmark immediately, the project can first borrow
evaluation ideas from literature discovery, citation grounding, limitation detection, idea generation,
code execution, and reproducibility benchmarks.

| Benchmark | Link | What It Measures | How It Informs AutoResearch |
|---|---|---|---|
| AutoResearchBench | https://arxiv.org/abs/2604.25256 | Autonomous scientific literature discovery through Deep Research and Wide Research tasks. | Best short-term reference for testing whether AutoResearch can find the right papers before claiming weaknesses. |
| AstaBench | https://arxiv.org/abs/2510.21652 | Broad scientific research-agent ability across 2400+ problems and multiple research stages. | Holistic reference for scientific agent evaluation, tools, cost accounting, and controlled leaderboards. |
| ScholarQABench | https://arxiv.org/abs/2411.14199 | Literature-search and citation-backed scientific synthesis. | Useful for evaluating whether weakness explanations are grounded in retrievable evidence. |
| ResearchQA | https://arxiv.org/abs/2607.11074 | Citation-grounded QA over scientific papers, including lookup, comprehension, multi-hop, and adversarial questions. | Relevant to evidence quality: answers should cite passages and refuse unsupported claims. |
| DeepResearch Bench | https://deepresearch-bench.github.io/ | PhD-level deep research tasks across many fields, with report quality and citation trustworthiness evaluation. | Useful for report-level evaluation, but broader than the current Weakness Finder scope. |
| AI Idea Bench 2025 | https://arxiv.org/abs/2504.14191 | AI research idea generation using target papers and inspired works. | Later-stage reference for evaluating weakness-to-idea conversion after Weakness Finder is stable. |
| IdeaBench | https://arxiv.org/html/2411.02429v1 | Research idea generation, novelty, feasibility, semantic similarity, and idea overlap. | Helps evaluate whether generated opportunities are novel and feasible, but should come after weakness validation. |
| LiveIdeaBench | https://www.nature.com/articles/s41467-026-70245-1 | Scientific idea generation under divergent-thinking criteria. | Useful later for idea diversity, originality, feasibility, fluency, flexibility, and clarity. |
| LIMITGEN | https://aclanthology.org/2025.acl-long.1009.pdf | Identification of critical limitations in scientific research papers. | Closest benchmark family to the new Weakness Finder target. |
| FLAWS | https://arxiv.org/html/2511.21843v1 | Error identification and localization in scientific papers / reviews. | Useful for testing whether the system can find specific weaknesses rather than generic criticism. |
| MLAgentBench | https://arxiv.org/abs/2310.03302 | ML experimentation agents that write code, run experiments, and improve models. | Later-stage reference if AutoResearch adds experiment execution. |
| MLE-bench | https://openai.com/index/mle-bench/ | Machine-learning engineering over Kaggle-style competitions. | Later-stage benchmark for experiment and model-building capability. |
| ResearchCodeBench | https://arxiv.org/html/2506.02314v1 | Implementing novel ML research contributions as executable code. | Later-stage reference for paper-to-code implementation, not current Weakness Finder. |
| PaperBench | https://arxiv.org/abs/2504.01848 | Replicating 20 ICML 2024 papers from scratch with hierarchical rubrics. | Useful for future Auto Design / Auto Experiment, but too heavy for the current MVP. |
| CORE-Bench | https://arxiv.org/abs/2409.11363 | Computational reproducibility across 90 papers and 270 tasks. | Important future reference for verifying whether claimed methods and evidence are reproducible. |
| ScienceAgentBench | https://arxiv.org/abs/2410.05080 | Data-driven scientific discovery tasks extracted from peer-reviewed papers. | Reference for evaluating research workflow subtasks with executable outputs and expert validation. |
| DiscoveryBench | https://arxiv.org/html/2407.01725v1 | Data-driven discovery from datasets, combining statistical analysis and semantic reasoning. | Relevant later if AutoResearch moves from weakness discovery to data-backed hypothesis validation. |
| LABBench2 | https://arxiv.org/html/2604.09554v2 | Practical biology research tasks such as literature retrieval, figure/table understanding, protocols, and database access. | Domain-specific example of agentic research-task benchmarking. |
| LifeSciBench | https://openai.com/index/introducing-life-sci-bench/ | Realistic life-science workflows across evidence handling, analysis, design, reasoning, validation, translation, and communication. | Useful example of workflow taxonomy design for a research-agent benchmark. |
| AIRS-Bench | https://arxiv.org/abs/2602.06855 | Frontier AI research science-agent tasks across the research lifecycle. | Reference for full-lifecycle research-agent evaluation once the project goes beyond weakness discovery. |
| SciAgentArena | https://arxiv.org/abs/2606.12736 | Real-world scientific research scenarios with stepwise verification and interactive evaluation. | Useful future reference for stepwise verification of agent research outputs. |

### Appendix C: Positioning Decision

- Near-term positioning:
  - AutoResearch should become a `Weakness Finder`, not a full automatic paper-writing system.
  - Its first useful output should be a ranked list of weaknesses with support papers, counter
    papers, MOC origin, evidence quality, and validation steps.
- Differentiation:
  - Compared with search and QA systems, AutoResearch should focus on cross-paper weakness
    judgment rather than answer generation.
  - Compared with idea-generation benchmarks, AutoResearch should first prove that the weakness is
    real before proposing ideas.
  - Compared with experiment agents, AutoResearch should stop at research planning until the
    weakness evidence chain is reliable.
- Candidate future internal benchmark:
  - `WeaknessBench-mini`
  - input: a research direction plus a controlled paper set
  - output: 3 candidate weaknesses with support evidence, counter-evidence, evidence quality, and
    validation plan
  - evaluation dimensions: specificity, evidence grounding, counter-evidence handling, novelty of
    the weakness, and whether the weakness can be validated by a benchmark or ablation

### Appendix D: Paper-Idea Analysis Pattern

- IdeaBench-style retrospective insight:
  - A high-quality paper's idea usually grows out of its cited reference set, not from an isolated
    keyword search.
  - IdeaBench evaluates whether an LLM can read the target paper's reference papers and generate an
    idea comparable to the true target-paper idea.
  - AutoResearch can borrow this pattern without becoming an idea-generation benchmark.
- Proposed AutoResearch adaptation:
  - input: a target paper or a research direction
  - if a target paper is given, collect its reference papers first
  - read only the reference set, then build paper cards, comparison tables, and a MOC
  - infer the weaknesses that could motivate the target paper
  - compare the inferred weaknesses/opportunities with the target paper's introduction,
    motivation, and contribution
- Why this matters:
  - Reference sets are a cleaner field map than blind keyword search.
  - They usually contain classic works, competing routes, datasets, benchmarks, metrics, and the
    exact prior work the target paper positions against.
  - This mode can validate whether AutoResearch is learning to recover research motivation from
    prior literature instead of merely summarizing papers.
- Candidate validation metric:
  - `Research Motivation Recovery Score`
  - measures whether the generated weakness aligns with the target paper motivation, whether the
    proposed opportunity aligns with the target contribution, and whether each claim is grounded in
    reference-paper evidence.

### Appendix E: Quote-First Weakness Finder Principle

- ScholarQA-inspired principle:
  - extract evidence first, summarize second
  - every important answer or weakness claim should be backed by source snippets
  - paper comparison tables should keep methods, datasets, metrics, findings, and evidence links
    next to each other
- AutoResearch adaptation:
  - retrieve papers or reference papers
  - extract quotes/snippets from abstract, introduction, methods, experiments, limitations, and
    discussion sections
  - cluster snippets into evidence themes
  - build a comparison table before generating any weakness
  - generate candidate weaknesses only after support and counter snippets are available
- Terminology decision:
  - `quote`: a short verbatim source passage from a paper
  - `snippet`: a broader evidence fragment, which may be lightly cleaned or section-bounded
  - user-facing UI can call both `evidence snippets` to avoid confusing readers
- Weakness card target structure:
  - weakness statement
  - support snippets
  - counter snippets
  - comparison-table origin
  - MOC origin
  - evidence quality
  - verdict: valid, partially valid, evidence insufficient, or already covered

### Appendix F: Big Gap Narrowing Logic From Meeting Notes

- Key meeting correction:
  - counter-evidence should not simply kill a gap.
  - if an existing paper solves part of a broad gap, AutoResearch should use that paper to narrow
    the gap.
  - the remaining unsolved part becomes the useful narrow gap.
- Updated reasoning chain:
  - find a broad important problem
  - map what existing papers already solved
  - identify which subparts are only partially solved
  - narrow the broad gap into a smaller remaining gap
  - derive 2-3 concrete weaknesses from that remaining gap
  - check whether any newer or adjacent papers already cover those weaknesses
- Example pattern:
  - broad gap: a field lacks capability `X`
  - existing work: papers A/B solve parts of `X`
  - narrow gap: `X` is still weak under condition `Y`, dataset `Z`, metric `M`, or workflow `W`
  - weakness points: the remaining gap can be criticized through missing assumptions,
    under-specified metrics, limited benchmarks, poor robustness, or missing failure analysis
- Product implication:
  - the current `support / counter / unclear` structure is useful but incomplete.
  - the next Weakness Finder should add `covered_parts`, `partially_solved_parts`, and
    `remaining_narrow_gap`.
  - MOC should show where existing routes stop, not only which papers belong to which group.

### Appendix G: Boundary With Existing Research-Agent Systems

- AI Scientist and AI Scientist-v2:
  - use idea-first workflows: generate ideas, run novelty checks, execute experiments, then use
    reviewer-style feedback to find weaknesses in the generated paper or experiment.
  - useful lessons: novelty checking, automated review rubrics, and experiment failure feedback.
  - limitation for AutoResearch: they do not primarily discover field-level weaknesses from
    literature relationships.
- Agent Laboratory:
  - starts from a user-provided research idea, then performs literature review, planning,
    experiments, writing, and review.
  - useful lessons: after a weakness becomes an idea, a downstream agent can execute experiments
    and produce a report.
  - limitation for AutoResearch: it does not strongly validate whether the original idea is
    motivated by a real, unresolved weakness.
- FutureHouse and ScholarQA:
  - strong at retrieval, literature synthesis, citation-grounded answers, and prior-art checking.
  - useful lessons: prior-art/counter-evidence search, quote-first answering, and evidence-backed
    comparison tables.
  - limitation for AutoResearch: they are not mainly designed as MOC-based weakness discovery
    engines.
- Current differentiation:
  - AutoResearch should sit before Auto Design and Auto Writing.
  - Its first job is to determine what weakness is real enough to deserve a research idea.

- Implemented Weakness Evidence Completion v1:
  - added `WeaknessCard` as the user-facing result layer on top of existing `GapEvidence`
  - each weakness now records `verdict`, `evidence_quality`, checked paper count, checked full-text
    count, checked source count, support papers, counter papers, covered parts, missing parts,
    remaining narrow weakness, MOC origin, and verification queries
  - added `weakness_cards.json` and `weakness_completion.md`
  - `dashboard.html` now opens with `Weakness 首页` instead of `Gap 首页`
  - the dashboard mainline now shows final-style verdicts: `成立`, `部分成立`, `已被覆盖`, or
    `证据不足`
  - the dashboard explicitly states the search boundary: AutoResearch does not read every paper in a
    field; it performs multi-source recall, ranks candidates, and verifies the top-ranked subset
  - `codex-apply` now rebuilds `WeaknessCard` after refined gaps are written back
- Tightened evidence-quality rules:
  - without successful full-text reads, a weakness cannot be marked as medium/strong evidence
  - metadata-only runs therefore produce `weak` evidence quality even if support/counter counts are
    available
- Improved full-text fetching safety:
  - added concurrent full-text fetching with a shorter request timeout
  - restricted v1 full-text candidates to direct PDFs, arXiv PDFs, and PMC pages instead of generic
    DOI or publisher landing pages
- Medical VLM Weakness Finder run regenerated with a stable metadata-only configuration:
  - topic: `medical VLM temporal lesion change analysis`
  - query count: `10`
  - source/query executions: `60`
  - ranked papers: `8`
  - weakness cards: `4`
  - full-text reads: `0`
  - checked sources: `6`
  - evidence quality: `weak` because no full text was read in this stable run
  - artifacts: `weakness_cards.json`, `weakness_completion.md`, `dashboard.html`
- New limitation discovered:
  - full-text fetching still needs a hard wall-clock deadline and better per-paper failure logging
    before it can safely be enabled as the default evidence-completion path
  - source/query execution is still serial and should be parallelized or cached for larger domains

### Appendix H: AlphaXiv as an AI/ML Literature Source

- Context:
  - Senior collaborator recommended https://www.alphaxiv.org/ as a possible paper-discovery source.
  - AlphaXiv should be treated as an arXiv-centered discovery and discussion layer, not as a
    general scholarly database.
- What AlphaXiv appears useful for:
  - discovering and reading arXiv papers, especially AI/ML/CS papers
  - replacing an `arxiv.org` paper URL with an `alphaxiv.org` paper page for enhanced reading and
    discussion context
  - semantic or multi-hop discovery around a research question, method name, benchmark, author, or
    paper title
  - finding newer or related arXiv papers that may act as counter-evidence for a proposed weakness
  - reading paper content or asking paper-specific questions when AlphaXiv tools are available
- Likely retrieval logic to model:
  - user question plus focused keywords
  - keyword search for exact method / benchmark / author / title matches
  - semantic search for concept-level matches
  - optional follow-up retrieval rounds for hard questions
  - ranking by relevance, recency, and possibly community/activity signals
- How AutoResearch should use it:
  - add AlphaXiv as an AI/ML-focused collector or enrichment source
  - use it in `Counter-evidence Search` for questions such as:
    - has anyone already solved this weakness?
    - is there already a benchmark for this capability?
    - which recent arXiv papers directly challenge this claim?
  - use it as a full-text or paper-QA helper when extracting limitations, datasets, metrics,
    benchmark protocols, failure cases, and future-work statements
- Boundaries:
  - AlphaXiv should not replace OpenAlex, Semantic Scholar, CrossRef, PubMed, Europe PMC,
    OpenReview, or Papers With Code.
  - It is likely strongest for arXiv-heavy AI/ML areas and weaker for clinical, biomedical,
    social-science, and paywalled literature.
  - Community signals are useful for discovery but should not be treated as evidence that a
    weakness is scientifically valid.
- Product implication:
  - AlphaXiv fits the new Weakness Finder direction because it can help retrieve both supporting
    papers and recent counter-evidence.
  - The first implementation should be read-only and evidence-preserving: collect candidates,
    store source URLs, and mark AlphaXiv-derived papers as one source among several.

### Appendix I: Bench Module Direction From Meeting Notes

- Source:
  - `自动化科研流程.docx` is a speech-to-text transcript with many recognition errors, but the
    Bench-related intent is still recoverable.
- Meeting-level interpretation:
  - AutoResearch was originally discussed as four serial modules:
    `Auto Search -> Auto Design -> Auto Bench / Auto Benchmark -> Auto Writing`.
  - The current project should stay focused on Search / Weakness first, but the Bench module is an
    important downstream evidence layer.
- What the Bench module is expected to do:
  - given a contribution, innovation point, method, or paper introduction/method section, find
    existing datasets, benchmarks, and metrics that can evaluate the claimed effect
  - determine which public benchmarks can be used as base benchmarks
  - if no suitable benchmark exists, propose or construct a new benchmark or benchmark slice for
    the specific contribution
  - explain why a benchmark is suitable or unsuitable for validating the contribution
  - support manual evaluation of whether the generated benchmark recommendation is useful
- Important distinction:
  - Bench is not only a standalone "benchmark website".
  - In AutoResearch, Bench should answer whether a proposed weakness or contribution can be
    evaluated, and whether existing benchmarks already cover it.
- Connection to the current Weakness Finder direction:
  - Paper Weakness Finder asks: what is not well solved in existing work?
  - Bench module asks: is there an evaluation tool that can prove this weakness?
  - Bench Weakness Finder asks: do the available benchmarks themselves miss the key capability,
    rely on weak metrics, lack public data, lack model coverage, or fail to expose failure modes?
- Meeting-derived workflow:
  - start from a broad gap or contribution
  - search for existing papers/benchmarks that partially address it
  - use those papers as narrowing evidence rather than simply treating them as refutations
  - identify the remaining narrow weakness
  - ask whether any benchmark can measure that remaining weakness
  - if not, propose a benchmark design or dataset construction plan
- Proposed Bench module output:
  - relevant benchmark list
  - benchmark cards with source links, paper, code, dataset, leaderboard, task format, metrics,
    model results, and evidence snippets
  - benchmark suitability judgment for the target weakness/contribution
  - benchmark weakness notes: missing capability, proxy metric, weak scoring protocol,
    reproducibility issue, limited leaderboard/model coverage, or missing failure analysis
  - optional generated benchmark proposal if no existing benchmark is suitable
- Existing project to reuse:
  - `/Users/zwx/Documents/文献阅读/bench-analysis-workbench`
  - current positioning: `Benchmark Understanding / Benchmark Intelligence Workbench`
  - reusable assets:
    - `BenchProfile` / benchmark card schema
    - source discovery for official pages, papers, GitHub, Hugging Face datasets, and leaderboards
    - paper-level benchmark analysis fields: motivation, benchmark design, rubric/scoring,
      model results, conclusions, failure modes, reliability notes
    - model result extraction: model, metric, score, source, verification status
    - seed library for benchmark names, aliases, manual sources, and latest reports
    - gold-note annotation guideline and `data/gold_notes/template.json`
- Recommended integration stance:
  - do not merge the old workbench wholesale into AutoResearch immediately
  - first extract a small `BenchCard` / `BenchProfile` module into AutoResearch
  - keep the old web UI as a reference implementation and source of tested heuristics
  - make Bench output serve Weakness Cards, not replace the Paper/MOC pipeline
- Near-term Bench MVP:
  - input: benchmark name, paper URL, Hugging Face dataset URL, or a target paper's
    introduction/method text
  - output: one structured BenchCard and a Chinese explanation page
  - fields: what it measures, cases/schema, metrics/scoring, who has evaluated on it, source
    evidence, suitability for a weakness, and benchmark limitations
- Later Auto Benchmark goal:
  - once Search / Weakness Finder is stable, use Bench Cards to recommend evaluation protocols,
    baselines, metrics, ablations, and, when necessary, new benchmark construction plans.

## 2026-08-10

- Implemented Paper Seed Library v1:
  - added seed schemas for `PaperSeedRecord`, `TopicSeed`, and `SeedLibrarySelection`
  - added file-based seed data under `data/paper_seed/`
  - added a first medical VLM temporal lesion seed topic:
    `medical-vlm-temporal-lesion`
  - added seed papers for dataset / benchmark-context / baseline roles
  - added a seed loader that matches the user topic to a topic seed, expands search queries,
    and converts matched seed papers into normal `PaperRecord` objects
  - integrated seed papers into the main search pipeline before deduplication and ranking
  - wrote seed metadata to `seed_selection.json` and `search_result.json`
- Implemented Full-text Provider v2:
  - replaced generic URL attempts with provider-ordered candidates
  - provider order now prioritizes PMC XML / PMC HTML for PMCID papers, then arXiv PDF,
    direct PDF, and direct HTML
  - added per-paper hard timeout to avoid one bad PDF or webpage blocking the whole run
  - added provider, attempted provider list, attempted URL list, and failure stage to
    `FullTextRecord`
  - added JATS/XML section extraction so medical PMC papers can expose Abstract, Methods,
    Results, Discussion, and related sections more reliably than PDF parsing
- Updated the UI and reports:
  - dashboard homepage now shows seed paper count and full-text success count
  - system page now shows Paper Seed Library details and Full-text Provider status
  - source coverage / report markdown now records seed status and provider-level full-text coverage
- Current positioning after this update:
  - Paper Seed Library improves the starting point and makes the project accumulative
  - Full-text Provider v2 improves evidence depth and failure transparency
  - Weakness Finder remains the main target; Design / Benchmark / Writing are still downstream

## Next

- Run a small medical VLM search with `full_text_limit > 0` and inspect whether PMC XML
  increases evidence quality.
- Add manual seed editing commands so the user can add / review / retire seed papers without
  hand-editing JSONL.
- Add source-quality reporting: source -> core / adjacent / noise contribution counts.
- Add Codex-reviewed PaperInsight and MOC refinement with strict evidence references.
- Add review/evaluation fixtures to compare rule-generated vs Codex-reviewed extraction quality.
- Add LitSearch-style evaluation for search/ranking quality.
- Later: add BenchCard / BenchProfile integration using the existing `bench-analysis-workbench`
  assets as the first AutoResearch Bench module.
