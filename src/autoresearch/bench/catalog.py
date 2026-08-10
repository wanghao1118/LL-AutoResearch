from __future__ import annotations

from .schema import BenchCard, BenchModelResult, BenchSource

SEED_BENCHES: list[BenchCard] = [
    BenchCard(
        bench_name="DeepLesion",
        aliases=["Deep Lesion"],
        domain=["medical imaging", "CT", "lesion"],
        keywords=["medical", "ct", "lesion", "localization", "detection"],
        source_urls=[
            BenchSource(
                title="DeepLesion dataset paper",
                url="https://arxiv.org/abs/1710.01766",
                source_type="paper",
                note="Large-scale lesion annotations on CT images.",
            )
        ],
        evaluated_capabilities=["lesion detection", "lesion localization"],
        task_format="CT lesion detection and localization annotations.",
        case_examples=["CT image with lesion bounding box / annotation."],
        dataset_schema={
            "image": "CT slice or volume reference",
            "label": "lesion annotation",
            "localization": "bounding box / lesion location",
        },
        metrics=["sensitivity", "localization accuracy"],
        scoring_protocol="Detection/localization style evaluation over lesion annotations.",
        judge_type="automatic",
        strengths=["Direct lesion-level annotations are useful for localization evidence."],
        weaknesses=[
            "不能直接评估配对时序病灶变化。",
            "没有定义 VLM 指令跟随式评估协议。",
        ],
        suitable_for=["lesion localization weakness", "medical imaging grounding"],
        not_suitable_for=["temporal change reasoning", "paired-study VLM evaluation"],
        evidence_snippets=[
            "DeepLesion is useful as lesion-level data evidence, but not as a temporal VLM benchmark.",
        ],
    ),
    BenchCard(
        bench_name="MIMIC-CXR",
        aliases=["MIMIC CXR"],
        domain=["medical imaging", "radiology", "chest x-ray"],
        keywords=["medical", "radiology", "report", "cxr", "chest x-ray"],
        source_urls=[
            BenchSource(
                title="MIMIC-CXR dataset",
                url="https://physionet.org/content/mimic-cxr/",
                source_type="dataset",
                note="Chest radiograph dataset with reports.",
            )
        ],
        evaluated_capabilities=["radiology report generation", "image-text alignment"],
        task_format="Chest X-ray images paired with radiology reports.",
        case_examples=["CXR image with associated report text."],
        dataset_schema={"image": "chest radiograph", "text": "radiology report"},
        metrics=["BLEU", "ROUGE", "BERTScore", "clinical label accuracy"],
        scoring_protocol="Report-generation or image-text downstream evaluation.",
        judge_type="automatic / clinical label extraction",
        strengths=["Strong source for report-generation and image-text alignment experiments."],
        weaknesses=[
            "报告级指标不一定能证明病灶级定位能力。",
            "不是为配对时序病灶变化评估设计的 benchmark。",
        ],
        suitable_for=["medical report generation", "image-text alignment"],
        not_suitable_for=["lesion-level temporal reasoning", "change-direction evaluation"],
    ),
    BenchCard(
        bench_name="RadGraph",
        aliases=[],
        domain=["medical NLP", "radiology", "clinical graph"],
        keywords=["medical", "radiology", "finding", "relation", "graph", "report"],
        source_urls=[
            BenchSource(
                title="RadGraph paper",
                url="https://arxiv.org/abs/2106.14463",
                source_type="paper",
                note="Radiology report entity and relation extraction benchmark.",
            )
        ],
        evaluated_capabilities=["finding extraction", "location relation extraction"],
        task_format="Radiology report entities and relations.",
        dataset_schema={"text": "radiology report", "labels": "entities and relations"},
        metrics=["F1"],
        scoring_protocol="Entity/relation extraction evaluation.",
        judge_type="automatic",
        strengths=["Can support finding/location consistency checks in report text."],
        weaknesses=[
            "只评估文本，不能直接评估视觉 grounding。",
            "单独使用时不能评估时序图像对的变化推理。",
        ],
        suitable_for=["report-level finding consistency"],
        not_suitable_for=["visual lesion tracking", "paired temporal VLM evaluation"],
    ),
    BenchCard(
        bench_name="OSWorld",
        aliases=[],
        domain=["GUI agent", "desktop", "computer use"],
        keywords=["gui", "agent", "desktop", "computer", "workflow", "long-horizon"],
        source_urls=[
            BenchSource(
                title="OSWorld paper",
                url="https://arxiv.org/abs/2404.07972",
                source_type="paper",
                note="Benchmark for multimodal agents in real computer environments.",
            )
        ],
        evaluated_capabilities=["desktop task completion", "computer-use agent"],
        task_format="Open-ended desktop software tasks in virtual environments.",
        metrics=["success rate"],
        scoring_protocol="Task completion checked by environment-specific evaluators.",
        judge_type="automatic / task-specific",
        strengths=["Desktop workflows are closer to real computer-use agents than toy UI tasks."],
        weaknesses=[
            "聚合成功率可能掩盖感知、规划、执行和恢复等不同失败类型。",
            "只覆盖桌面环境，不能解决跨平台 benchmark 可比性问题。",
        ],
        suitable_for=["desktop GUI agent evaluation", "real computer-use task completion"],
        not_suitable_for=["cross-benchmark failure taxonomy", "mobile/web/desktop unified scoring"],
    ),
    BenchCard(
        bench_name="AndroidWorld",
        aliases=[],
        domain=["GUI agent", "mobile", "Android"],
        keywords=["gui", "agent", "android", "mobile", "app", "workflow"],
        source_urls=[
            BenchSource(
                title="AndroidWorld paper",
                url="https://arxiv.org/abs/2405.14573",
                source_type="paper",
                note="Dynamic Android environment for autonomous agents.",
            )
        ],
        evaluated_capabilities=["mobile app task completion", "Android agent"],
        task_format="Android app tasks in a dynamic mobile environment.",
        metrics=["task success"],
        scoring_protocol="Task-level success in Android environment.",
        judge_type="automatic / task-specific",
        strengths=["Useful for mobile GUI agent evaluation."],
        weaknesses=[
            "只覆盖移动端，不能单独统一 web、mobile、desktop 的分数口径。",
            "只看任务成功率时，很难解释具体失败类型。",
        ],
        suitable_for=["mobile GUI agent evaluation"],
        not_suitable_for=["cross-platform diagnostic metrics"],
    ),
    BenchCard(
        bench_name="BrowserGym",
        aliases=[],
        domain=["web agent", "browser", "benchmark suite"],
        keywords=["web", "browser", "agent", "webarena", "visualwebarena", "benchmark"],
        source_urls=[
            BenchSource(
                title="BrowserGym paper",
                url="https://arxiv.org/abs/2412.05467",
                source_type="paper",
                note="Gym environment and benchmark suite for web task automation.",
            )
        ],
        evaluated_capabilities=["web agent evaluation", "benchmark unification"],
        task_format="Unified interface over web automation benchmarks.",
        metrics=["task success", "benchmark-specific metrics"],
        scoring_protocol="Runs agents through a shared browser interface with task-specific scoring.",
        judge_type="automatic / benchmark-specific",
        strengths=["Strong counter-evidence for claims that web-agent benchmarks are completely fragmented."],
        weaknesses=[
            "主要面向 web agent，不能完整覆盖 mobile 和 desktop GUI agent。",
            "做跨 benchmark 结论时，仍需要谨慎处理不同 benchmark 的指标口径。",
        ],
        suitable_for=["web agent benchmark comparison"],
        not_suitable_for=["full cross-platform GUI benchmark comparability"],
    ),
    BenchCard(
        bench_name="GUI-RobustEval",
        aliases=["RoTS"],
        domain=["GUI agent", "robustness", "error recovery"],
        keywords=["gui", "agent", "failure", "error", "recovery", "robustness", "trajectory"],
        source_urls=[
            BenchSource(
                title="GUI-RobustEval paper",
                url="https://arxiv.org/abs/2605.29447",
                source_type="paper",
                note="Benchmarking robust GUI agents with policy-induced errors.",
            )
        ],
        evaluated_capabilities=["error awareness", "post-error recovery", "robust GUI execution"],
        task_format="GUI trajectories with injected or policy-induced errors.",
        metrics=["Error-Awareness Rate", "Post-Error Success Rate"],
        scoring_protocol="Measures whether agents detect and recover after error conditions.",
        judge_type="automatic / trajectory evaluator",
        model_results=[
            BenchModelResult(model="GPT-4-class models", organization="OpenAI", metric="reported", score="reported")
        ],
        strengths=["Directly targets GUI-agent error recovery and failure-conditioned evaluation."],
        weaknesses=[
            "不一定能解决所有 GUI benchmark 家族之间的跨平台分数可比性。",
            "如果要做更宽泛结论，还需要和 web/mobile/desktop benchmark 对照。",
        ],
        suitable_for=["failure recovery evaluation", "GUI robustness"],
        not_suitable_for=["all benchmark comparability questions"],
    ),
    BenchCard(
        bench_name="GDPval",
        aliases=["GDP val"],
        domain=["real-world work", "professional services", "economics"],
        keywords=["real-world", "professional", "deliverable", "expert", "workflow", "openai"],
        source_urls=[
            BenchSource(
                title="OpenAI GDPval announcement",
                url="https://openai.com/index/gdpval/",
                source_type="official",
                note="Real-world professional deliverable benchmark.",
            )
        ],
        evaluated_capabilities=["professional deliverable generation", "expert-judged work quality"],
        task_format="One-shot professional deliverables with reference files.",
        metrics=["expert preference", "win rate", "rubric score"],
        scoring_protocol="Expert blind comparison against human deliverables with rubric support.",
        judge_type="human expert / experimental automated grader",
        model_results=[
            BenchModelResult(model="OpenAI frontier models", organization="OpenAI", metric="expert preference", score="reported")
        ],
        strengths=["Good example of real-work artifact evaluation beyond short-answer QA."],
        weaknesses=[
            "完整任务集并未完全公开。",
            "私有任务和专家评审成本会限制完全可复现对比。",
            "专家评估复现实验成本较高。",
            "自动评分还不是唯一成熟的评分路径。",
        ],
        suitable_for=["real-world work artifact quality"],
        not_suitable_for=["fully public reproducible leaderboard comparison"],
    ),
    BenchCard(
        bench_name="FAB",
        aliases=["Finance Agent Benchmark", "FAB v2"],
        domain=["finance", "agent", "financial analysis"],
        keywords=["finance", "agent", "financial", "sec", "edgar", "filing", "search", "workflow"],
        source_urls=[
            BenchSource(
                title="FAB leaderboard",
                url="https://vals.ai/benchmarks/fabv2",
                source_type="leaderboard",
                note="Finance Agent Benchmark v2 leaderboard.",
            ),
            BenchSource(
                title="Finance Agent Benchmark paper",
                url="https://arxiv.org/abs/2508.00828",
                source_type="paper",
                note="Finance agent benchmark paper.",
            ),
        ],
        evaluated_capabilities=["financial research", "filing lookup", "finance agent tool use"],
        task_format="Finance questions requiring search and public filing access.",
        metrics=["accuracy", "score"],
        scoring_protocol="Answers are compared to expert-reviewed finance answers.",
        judge_type="automatic benchmark grading with expert-reviewed items",
        strengths=["Directly relevant to finance-agent workflow evaluation."],
        weaknesses=[
            "版本差异很重要，v1/v2 不能随意合并比较。",
            "榜单设置和 tool harness 细节需要回到来源逐项核验。",
        ],
        suitable_for=["finance agent benchmark comparison"],
        not_suitable_for=["general real-world work scoring outside finance"],
    ),
    BenchCard(
        bench_name="SpreadsheetBench v2",
        aliases=["SpreadsheetBench 2"],
        domain=["spreadsheet", "business workflow", "agent"],
        keywords=["spreadsheet", "excel", "workflow", "business", "agent", "long-horizon"],
        source_urls=[
            BenchSource(
                title="SpreadsheetBench v2 paper",
                url="https://arxiv.org/abs/2606.29955",
                source_type="paper",
                note="End-to-end business spreadsheet workflow benchmark.",
            )
        ],
        evaluated_capabilities=["spreadsheet workflow execution", "multi-sheet reasoning", "debugging"],
        task_format="Multi-sheet spreadsheet workflow tasks.",
        metrics=["Task Accuracy", "Modification Accuracy"],
        scoring_protocol="Compares generated/modified spreadsheets with expected workbook outcomes.",
        judge_type="automatic / task-specific",
        strengths=["Useful for long-horizon spreadsheet and business workflow evaluation."],
        weaknesses=[
            "它是 spreadsheet 专项 benchmark，外推到金融或通用工作流时需要限定范围。",
            "大体量表格产物会让复现和输出检查变得更重要。",
        ],
        suitable_for=["spreadsheet workflow agents", "business artifact workflow"],
        not_suitable_for=["non-spreadsheet finance research"],
    ),
]


def list_seed_benches() -> list[BenchCard]:
    return list(SEED_BENCHES)
