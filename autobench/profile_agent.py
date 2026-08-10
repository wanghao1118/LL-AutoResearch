"""Agent 1: infer evaluation requirements from method and introduction only."""

from __future__ import annotations

import re
from collections import defaultdict

from .models import CapabilityProfile, MethodInput


TASK_RULES: dict[str, tuple[str, ...]] = {
    "knowledge_intensive_qa": (
        "question answering",
        "answer questions",
        "knowledge retrieval",
        "external knowledge",
        "wikipedia",
        "multi-hop",
        "reasoning questions",
    ),
    "fact_verification": ("fact verification", "verify claims", "evidence for a claim", "factual claim"),
    "embodied_household": (
        "household",
        "embodied",
        "text-based game",
        "navigate and interact",
        "common household environments",
    ),
    "web_navigation": (
        "webpage navigation",
        "web navigation",
        "website",
        "browser",
        "online shopping",
        "web interaction",
    ),
    "code_issue_resolution": (
        "software engineering problem",
        "software issue",
        "issue description",
        "bug report",
        "codebase revision",
        "software repository",
        "code repository",
        "repository-level repair",
        "repository patch",
        "code patch",
        "patch generation",
        "generate a patch",
        "test suite",
    ),
    "code_generation": (
        "generate code",
        "generating code",
        "program synthesis",
        "including programming",
        "programming task",
        "coding task",
        "function implementation",
        "function body",
        "code generation",
    ),
    "code_debugging": (
        "debugging",
        "repair code",
        "fix code",
        "failing tests",
        "bug fix",
        "code syntax checker",
        "code linter",
        "format errors",
        "edit function",
    ),
    "sequential_decision_making": (
        "sequential decision",
        "long horizon",
        "action choices",
        "action-observation",
        "trajectory",
        "sparse reward",
        "interactive environment",
    ),
    "math_reasoning": (
        "math word problem",
        "mathematical reasoning",
        "mathematical program synthesis",
        "arithmetic reasoning",
        "mathematical skills",
        "precise calculations",
        "line of equation",
        "quantitative skills",
        "math tasks",
    ),
    "math_word_problem": (
        "math word problem",
        "mathematical word problem",
        "multi-step arithmetic problem",
        "values of intermediate variables",
        "subquestion about an unknown intermediate variable",
    ),
    "tabular_math_reasoning": (
        "tabular mathematical reasoning",
        "tabular math",
        "mathematical benchmark involving diverse tabular contexts",
        "mathematical reasoning task involving diverse tabular contexts",
        "table-based math",
        "table inputs",
        "linearize a table",
        "text+table",
        "input formats including text, tables",
        "text, tables, and conversation",
    ),
    "toxicity_reduction": (
        "toxicity reduction",
        "toxic content",
        "nonoffensive text",
        "detoxification",
        "toxicity mitigation",
    ),
    "general_assistant": ("general assistant", "real-world question", "tool-augmented assistant"),
    "computer_use": ("computer use", "desktop", "graphical user interface", "screenshot"),
    "api_tool_use": ("api call", "tool call", "api interaction", "multi-tool"),
    "scientific_experiment_planning": (
        "laboratory protocol",
        "experimental procedure",
        "wet lab",
        "reagent",
        "assay",
    ),
}

UNCOVERED_TASK_RULES: dict[str, tuple[str, ...]] = {
    "dialogue_response_generation": (
        "dialogue response generation",
        "generate conversational responses",
        "open-domain dialogue response generation",
    ),
    "code_optimization": (
        "code optimization",
        "optimize code",
        "optimizing code",
        "enhancing program efficiency",
    ),
    "code_readability": (
        "code readability",
        "program readability",
        "improving the readability of code",
        "enhancing program readability",
    ),
    "sorting": (
        "sorting task",
        "sorting numbers",
        "sorted subarrays",
        "sorted array",
    ),
    "set_intersection": ("set intersection", "set operations"),
    "keyword_counting": ("keyword counting", "counting keywords"),
    "document_merging": ("document merging", "merge input documents"),
    "classical_planning": (
        "for plan generation",
        "plan generation task",
        "classical planner",
        "classical planning",
        "planning domain definition language",
        "pddl",
        "optimal plan",
        "action plans to move blocks",
        "configuration of blocks",
        "blocks to a target state",
    ),
    "logical_reasoning": (
        "logical reasoning",
        "logical inference",
        "logical rules",
        "next deduction",
    ),
    "multimodal_science_qa": (
        "multi-modal question answering",
        "multimodal question answering",
        "science question answering",
        "scientific topics and contexts",
    ),
    "symbolic_reasoning": (
        "symbolic reasoning",
        "symbolic reasoning task",
        "symbolic reasoning benchmark",
    ),
    "algorithmic_reasoning": (
        "algorithmic reasoning",
        "algorithmic task",
        "object counting",
        "repeat copy",
    ),
    "tool_augmented_nlp": (
        "tool augmented llm",
        "tool augmented language model",
        "augmented language model",
        "knowledge intensive nlp benchmark",
        "multi step and knowledge intensive nlp",
        "external tools via simple apis",
        "use external tools",
        "use different tools by means of api calls",
    ),
    "language_modeling": (
        "language modeling abilities",
        "language modeling objective",
        "language modeling dataset",
        "core language modeling",
    ),
    "financial_numerical_qa": (
        "financial problem",
        "financial dataset",
        "financial question",
        "financial qa",
        "math driven financial",
    ),
    "image_editing": (
        "image editing",
        "language guided image editing",
        "edit images",
        "image manipulation",
    ),
    "creative_writing": (
        "creative writing",
        "writing plan",
        "paragraph of writing",
        "coherent passage",
    ),
    "word_puzzle": (
        "word puzzle",
        "lexical reasoning",
        "words to fill in for clues",
        "word clues",
        "letter constraints",
    ),
    "visual_reasoning": (
        "complex visual query",
        "complex visual task",
        "visual input and a textual query",
        "visual grounding",
        "compositional visual",
        "compositional image question answering",
        "image or videos as inputs",
        "image or video inputs",
    ),
    "audio_music_generation": (
        "music generation",
        "polyphonic music",
        "multi-track audio",
        "multitrack audio",
        "audio generation",
    ),
    "speech_recognition": ("speech recognition", "speech transcription", "automatic transcription"),
    "image_generation": ("image generation", "text-to-image", "generate images"),
    "video_generation": ("video generation", "text-to-video", "generate videos"),
    "time_series_forecasting": ("time series forecasting", "temporal forecasting"),
    "molecule_generation": ("molecule generation", "molecular generation", "de novo molecule"),
    "robot_manipulation": (
        "robot manipulation",
        "robotic manipulation",
        "robot planning",
        "robot task planning",
        "robotic task planning",
        "robotic control",
        "physical robot",
        "robot arm",
        "mobile manipulation",
        "tabletop manipulation",
        "tabletop task",
        "tabletop rearrangement",
        "pick and place",
        "grasp and place",
    ),
}

CAPABILITY_RULES: dict[str, tuple[str, ...]] = {
    "reasoning_action_interleaving": (
        "reasoning and acting",
        "reasoning and action",
        "thought-action-observation",
        "interleave",
    ),
    "external_information_retrieval": ("retrieve", "search", "external knowledge", "information gathering"),
    "evidence_grounding": ("grounded", "evidence", "factual", "verify"),
    "long_horizon_planning": ("long horizon", "subgoal", "plan", "trajectory"),
    "self_reflection": ("self-reflection", "verbal reflection", "reflective feedback", "self-evaluation"),
    "episodic_memory": ("episodic memory", "memory buffer", "prior experiences"),
    "iterative_improvement": ("retry", "future episode", "improve generation", "feedback loop"),
    "repository_navigation": ("repository", "codebase", "search files", "file viewer"),
    "code_editing": (
        "edit code",
        "code editing",
        "repository patch",
        "code patch",
        "patch generation",
        "generate a patch",
        "modify files",
        "editing files",
        "edit function",
        "file editor",
        "code linter",
    ),
    "test_based_verification": ("unit tests", "test suite", "tests pass", "compiler"),
    "multilingual_code_generation": (
        "multiple programming languages",
        "programming languages",
        "language ports",
        "multilingual code generation",
    ),
    "tool_use": ("action", "tool", "api", "shell", "browser", "computer"),
}

TASK_COUNT_ALIASES: dict[str, tuple[str, ...]] = {
    "knowledge_intensive_qa": (
        "qa",
        "question answering",
        "free form question answering",
        "free-form question answering",
    ),
    "math_reasoning": (
        "math",
        "mwp",
        "mathematical reasoning",
        "mathematical program synthesis",
        "arithmetic reasoning",
    ),
    "math_word_problem": ("math word problem", "mathematical word problem"),
    "tabular_math_reasoning": ("tabular math", "tabular mathematical reasoning"),
    "code_generation": ("programming", "code generation"),
    "web_navigation": ("web navigation", "web interaction"),
    "toxicity_reduction": ("toxicity", "toxicity reduction"),
}

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}


def _normalize(text: str) -> str:
    text = text.casefold().replace("–", "-").replace("—", "-")
    text = re.sub(r"(?<=[a-z0-9])-(?=[a-z0-9])", " ", text)
    return re.sub(r"\s+", " ", text)


def _rule_hits(text: str, rules: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for label, phrases in rules.items():
        matched = [phrase for phrase in phrases if _normalize(phrase) in text]
        if matched:
            hits[label] = matched
    return hits


BACKGROUND_TASK_MARKERS = (
    "previous work",
    "previous approaches",
    "recent approaches",
    "existing approaches",
    "prior work",
    "has shown",
    "have shown",
    "has demonstrated",
    "have demonstrated",
    "was shown",
    "were shown",
    "broad set of tasks",
)

OWN_TASK_MARKERS = (
    "we evaluate",
    "we evaluated",
    "we study",
    "we consider",
    "we focus",
    "we demonstrate",
    "we showcase",
    "we illustrate",
    "our experiments",
    "our method",
    "our framework",
    "method_x",
    "applications of",
)


def _drop_background_only_tasks(
    text: str,
    task_hits: dict[str, list[str]],
    uncovered_task_hits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Drop generic prior-work task mentions when owned use cases are explicit.

    Method papers often list broad capabilities of earlier systems before
    naming their own concrete use cases. The filter activates only when at
    least two specific uncovered tasks are visible, retaining the original
    recall-oriented behavior for sparse method descriptions.
    """

    if len(uncovered_task_hits) < 2:
        return task_hits
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text)]
    retained: dict[str, list[str]] = {}
    for label, phrases in task_hits.items():
        phrase_sentences = [
            sentence
            for sentence in sentences
            if any(_normalize(phrase) in sentence for phrase in phrases)
        ]
        owned = any(_contains_any(sentence, OWN_TASK_MARKERS) for sentence in phrase_sentences)
        background_only = bool(phrase_sentences) and all(
            _contains_any(sentence, BACKGROUND_TASK_MARKERS) for sentence in phrase_sentences
        )
        if background_only and not owned:
            continue
        retained[label] = phrases
    return retained


def _drop_background_only_uncovered_tasks(
    text: str,
    uncovered_task_hits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Drop uncovered-task phrases that occur only in prior-work sentences."""

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text)]
    retained: dict[str, list[str]] = {}
    for label, phrases in uncovered_task_hits.items():
        phrase_sentences = [
            sentence
            for sentence in sentences
            if any(_normalize(phrase) in sentence for phrase in phrases)
        ]
        owned = any(_contains_any(sentence, OWN_TASK_MARKERS) for sentence in phrase_sentences)
        background_only = bool(phrase_sentences) and all(
            _contains_any(sentence, BACKGROUND_TASK_MARKERS) for sentence in phrase_sentences
        )
        if background_only and not owned:
            continue
        retained[label] = phrases
    return retained


def _apply_uncovered_task_precedence(
    uncovered_task_hits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Prefer an explicit downstream operation over background model families."""

    retained = dict(uncovered_task_hits)
    if "image_editing" in retained:
        retained.pop("image_generation", None)
    return retained


def _apply_specific_task_precedence(
    text: str,
    task_hits: dict[str, list[str]],
    uncovered_task_hits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Prefer explicit evaluation subtypes over generic method capabilities."""

    retained = dict(task_hits)
    if retained.get("code_generation") == ["program synthesis"]:
        without_math_program_synthesis = text.replace("mathematical program synthesis", "")
        if "program synthesis" not in without_math_program_synthesis:
            retained.pop("code_generation", None)
    if {"code_optimization", "code_readability"} & set(uncovered_task_hits):
        retained.pop("code_generation", None)
    if "multimodal_science_qa" in uncovered_task_hits:
        retained.pop("knowledge_intensive_qa", None)
    if "robot_manipulation" in uncovered_task_hits:
        generics = ["knowledge_intensive_qa", "sequential_decision_making"]
        if not _contains_any(
            text,
            (
                "household tasks",
                "virtual household environment",
                "household simulator",
            ),
        ):
            generics.append("embodied_household")
        for generic in generics:
            retained.pop(generic, None)
    if "classical_planning" in uncovered_task_hits:
        retained.pop("sequential_decision_making", None)
    if "visual_reasoning" in uncovered_task_hits:
        for implementation_detail in (
            "code_generation",
            "code_issue_resolution",
            "knowledge_intensive_qa",
        ):
            retained.pop(implementation_detail, None)
    if "tool_augmented_nlp" in uncovered_task_hits:
        retained.pop("sequential_decision_making", None)
    return retained


def _apply_specific_capability_precedence(
    capability_hits: dict[str, list[str]],
    uncovered_task_hits: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Remove implementation mechanisms that would masquerade as evaluation tasks."""

    retained = dict(capability_hits)
    if "visual_reasoning" in uncovered_task_hits:
        for implementation_detail in (
            "code_editing",
            "multilingual_code_generation",
            "repository_navigation",
            "test_based_verification",
        ):
            retained.pop(implementation_detail, None)
    return retained


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Match fixed phrases under the same hyphen and whitespace normalization."""

    return any(_normalize(phrase) in text for phrase in phrases)


def _fallback_uncovered_task(text: str) -> dict[str, list[str]]:
    """Extract one explicit task phrase when no known task taxonomy matches."""

    patterns = (
        r"\bwe (?:study|address|investigate|consider|evaluate)\s+(.+?)(?=\s+(?:using|with|through|via|by|from)\b|[.;])",
        r"\b(?:system|model|method|approach|agent)\s+(?:that\s+|can\s+|aims to\s+)?"
        r"((?:generates?|predicts?|classifies?|detects?|translates?|segments?|synthesizes?|reconstructs?)\s+.+?)"
        r"(?=\s+(?:using|with|through|via|by|from|while)\b|[.;])",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        phrase = re.sub(r"^(?:a|an|the)\s+", "", match.group(1).strip())
        tokens = re.findall(r"[a-z0-9]+", phrase)[:8]
        if len(tokens) < 2:
            continue
        label = "_".join(tokens)
        return {label: [" ".join(tokens)]}
    return {}


def _explicit_api_evaluation_task(text: str) -> bool:
    """Distinguish an API-use evaluation task from APIs used by the method.

    Tool-augmented methods often mention API calls as implementation details
    while evaluating question answering, mathematics, or generation. API
    benchmarks are proposed only when the visible paper text explicitly names
    tool/API use as the task or benchmark construct.
    """

    markers = (
        "api use task",
        "api-use task",
        "api tool use",
        "api interaction task",
        "tool use task",
        "tool-use task",
        "tool use benchmark",
        "tool-use benchmark",
        "multi-tool task",
        "evaluate api use",
        "evaluation of api use",
        "evaluate tool use",
        "evaluation of tool use",
    )
    return _contains_any(text, markers)


def _explicit_task_benchmark_counts(
    text: str,
    task_families: set[str],
) -> dict[str, int]:
    """Extract visible per-task evaluation breadth from Introduction/Method.

    Papers sometimes disclose that they evaluate on, for example, three QA
    tasks and three mathematical-reasoning tasks even when benchmark names are
    redacted. Those counts are legitimate matcher-visible evidence and should
    determine portfolio breadth instead of being discarded by a global Top-6
    limit. Counts are capped to ten to keep malformed prose from creating an
    unbounded recommendation list.
    """

    number_pattern = r"(?P<count>\d+|" + "|".join(NUMBER_WORDS) + r")"
    counts: dict[str, int] = {}
    for task in sorted(task_families):
        aliases = TASK_COUNT_ALIASES.get(task, ())
        for alias in sorted(aliases, key=len, reverse=True):
            pattern = (
                rf"\b{number_pattern}\s+(?:distinct\s+)?"
                rf"{re.escape(_normalize(alias))}\s+"
                rf"(?:benchmarks?|datasets?|tasks?)\b"
            )
            match = re.search(pattern, text)
            if not match:
                continue
            raw_count = match.group("count")
            count = int(raw_count) if raw_count.isdigit() else NUMBER_WORDS[raw_count]
            counts[task] = max(1, min(count, 10))
            break
    return counts


EVALUATION_OWNERSHIP_MARKERS = (
    "we evaluate",
    "we evaluated",
    "to evaluate",
    "we conduct experiments",
    "we conducted experiments",
    "we demonstrate",
    "we show",
    "our experiments",
    "comprehensive testing",
)


def _declared_evaluation_breadth(text: str) -> tuple[int, list[str]]:
    """Extract a paper-owned total suite size without reading benchmark names.

    Only sentences that explicitly attribute an evaluation or experiment to
    the proposed method are eligible. Counts describing prompts, examples,
    models, parameters, or training records are rejected. The value controls
    portfolio breadth but never identifies a hidden benchmark.
    """

    number_pattern = r"(?P<count>\d+|" + "|".join(NUMBER_WORDS) + r")"
    pattern = re.compile(
        rf"\b(?:all\s+)?{number_pattern}\s+(?P<scope>(?:[a-z]+\s+){{0,8}}?)"
        r"(?P<unit>benchmarks?|datasets?|tasks?)\b"
    )
    rejected_scope_terms = {"example", "examples", "prompt", "prompts", "model", "models"}
    candidates: list[tuple[int, str]] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if not _contains_any(sentence, EVALUATION_OWNERSHIP_MARKERS):
            continue
        sentence_counts: list[int] = []
        for match in pattern.finditer(sentence):
            scope_terms = set(match.group("scope").split())
            if scope_terms & rejected_scope_terms:
                continue
            raw_count = match.group("count")
            count = int(raw_count) if raw_count.isdigit() else NUMBER_WORDS[raw_count]
            if 1 <= count <= 50:
                sentence_counts.append(count)
        if sentence_counts:
            candidates.append((min(sum(sentence_counts), 50), sentence.strip()))
    if not candidates:
        return 0, []
    breadth = max(count for count, _ in candidates)
    evidence = sorted({sentence for count, sentence in candidates if count == breadth})
    return breadth, evidence


def build_profile(method_input: MethodInput) -> CapabilityProfile:
    """Build an inspectable capability profile using deterministic rules.

    The deterministic backend is the reproducible default used by blind tests.
    Prompt templates in ``prompts/`` allow the same typed contract to be filled
    by an LLM provider later without changing downstream matching logic.
    """

    text = _normalize(f"{method_input.introduction}\n{method_input.method}")
    task_hits = _rule_hits(text, TASK_RULES)
    uncovered_task_hits = _rule_hits(text, UNCOVERED_TASK_RULES)
    uncovered_task_hits = _drop_background_only_uncovered_tasks(text, uncovered_task_hits)
    uncovered_task_hits = _apply_uncovered_task_precedence(uncovered_task_hits)
    task_hits = _drop_background_only_tasks(text, task_hits, uncovered_task_hits)
    task_hits = _apply_specific_task_precedence(text, task_hits, uncovered_task_hits)
    if not task_hits and not uncovered_task_hits:
        uncovered_task_hits = _fallback_uncovered_task(text)
    if "api_tool_use" in task_hits and not _explicit_api_evaluation_task(text):
        task_hits.pop("api_tool_use")
    capability_hits = _rule_hits(text, CAPABILITY_RULES)
    capability_hits = _apply_specific_capability_precedence(capability_hits, uncovered_task_hits)
    task_benchmark_counts = _explicit_task_benchmark_counts(text, set(task_hits))
    declared_evaluation_breadth, breadth_evidence = _declared_evaluation_breadth(text)

    modalities = {"text"}
    code_tasks = {
        "code_issue_resolution",
        "code_generation",
        "code_debugging",
    } & set(task_hits)
    uncovered_code_tasks = {"code_optimization", "code_readability"} & set(uncovered_task_hits)
    if code_tasks or uncovered_code_tasks:
        modalities.add("code")
    if _contains_any(text, ("webpage", "website", "browser", "online shopping", "web navigation")):
        modalities.add("web")
    if (
        set(uncovered_task_hits) & {"visual_reasoning", "multimodal_science_qa", "image_editing"}
    ) or _contains_any(
        text,
        (
            "image input",
            "input image",
            "visual input",
            "visual observation",
            "screenshot",
            "image understanding",
            "image captioner",
            "visual reasoning",
            "vision-language",
        )
    ):
        modalities.add("image")
    if set(uncovered_task_hits) & {"audio_music_generation", "speech_recognition"} or _contains_any(
        text,
        ("audio input", "audio output", "acoustic", "music", "timbre", "waveform"),
    ):
        modalities.add("audio")
    if _contains_any(text, ("video", "temporal frames", "moving images")):
        modalities.add("video")

    interactions: set[str] = set()
    if _contains_any(
        text,
        ("action-observation", "interactive environment", "interactive simulator", "sequential action", "trajectory"),
    ):
        interactions.add("interactive_environment")
    if _contains_any(text, ("retrieve", "search", "wikipedia", "external knowledge", "api call")):
        interactions.add("retrieval_tool")
    if _contains_any(text, ("webpage", "website", "browser", "online shopping", "web navigation")):
        interactions.add("browser")
    if "code_issue_resolution" in task_hits and _contains_any(
        text, ("shell", "repository", "codebase", "command")
    ):
        interactions.add("shell")
    if not interactions:
        interactions.add("static")

    outputs: set[str] = set()
    if "knowledge_intensive_qa" in task_hits:
        outputs.add("short_answer")
    if "fact_verification" in task_hits:
        outputs.update(("classification_label", "supporting_evidence"))
    if any(task in task_hits for task in ("sequential_decision_making", "embodied_household", "web_navigation")):
        outputs.add("action_trajectory")
    if "code_issue_resolution" in task_hits:
        outputs.add("repository_patch")
    if "code_generation" in task_hits:
        outputs.add("function_implementation")
    if "code_debugging" in task_hits:
        outputs.add("repaired_program")
    if "tabular_math_reasoning" in task_hits:
        outputs.add("short_answer")
    if "toxicity_reduction" in task_hits:
        outputs.add("safe_text_continuation")
    if _contains_any(text, ("finalizing a purchase", "purchase a product", "online shopping")):
        outputs.add("selected_product")
    if "audio_music_generation" in uncovered_task_hits:
        outputs.add("generated_audio")
    if "speech_recognition" in uncovered_task_hits:
        outputs.add("transcription")
    if "image_generation" in uncovered_task_hits:
        outputs.add("generated_image")
    if "video_generation" in uncovered_task_hits:
        outputs.add("generated_video")
    if "dialogue_response_generation" in uncovered_task_hits:
        outputs.add("generated_response")
    if "code_optimization" in uncovered_task_hits:
        outputs.add("optimized_program")
    if "code_readability" in uncovered_task_hits:
        outputs.add("refactored_program")
    if set(uncovered_task_hits) & {"sorting", "set_intersection", "keyword_counting"}:
        outputs.add("structured_answer")
    if "document_merging" in uncovered_task_hits:
        outputs.add("merged_document")
    if set(uncovered_task_hits) & {"classical_planning", "logical_reasoning"}:
        outputs.add("reasoning_trace")
    if "multimodal_science_qa" in uncovered_task_hits:
        outputs.add("short_answer")
    if set(uncovered_task_hits) & {"symbolic_reasoning", "algorithmic_reasoning"}:
        outputs.add("structured_answer")
    if "tool_augmented_nlp" in uncovered_task_hits:
        outputs.add("short_answer")
    if "robot_manipulation" in uncovered_task_hits:
        outputs.add("action_trajectory")
    if "visual_reasoning" in uncovered_task_hits:
        outputs.add("visual_answer")
    if "language_modeling" in uncovered_task_hits:
        outputs.add("text_continuation")
    if "financial_numerical_qa" in uncovered_task_hits:
        outputs.add("short_answer")
    if "image_editing" in uncovered_task_hits:
        outputs.add("edited_image")
    if "creative_writing" in uncovered_task_hits:
        outputs.add("generated_passage")
    if "word_puzzle" in uncovered_task_hits:
        outputs.add("puzzle_solution")
    if not outputs:
        outputs.add("task_answer")

    environments: set[str] = set()
    if _contains_any(text, ("wikipedia", "external knowledge")):
        environments.add("knowledge_base")
    if _contains_any(text, ("household", "text-based game")):
        environments.add("household_simulator")
    if _contains_any(text, ("webpage", "website", "browser", "online shopping", "web navigation")):
        environments.add("website")
    if _contains_any(text, ("finalizing a purchase", "purchase a product", "online shopping")):
        environments.add("online_store")
    if "code_issue_resolution" in task_hits:
        environments.add("software_repository")
    if code_tasks or uncovered_code_tasks:
        environments.add("code_executor")
    if "tabular_math_reasoning" in task_hits:
        environments.add("structured_table")
    if "robot_manipulation" in uncovered_task_hits:
        environments.add("robot_environment")
    if "classical_planning" in uncovered_task_hits:
        environments.add("planning_domain")
    if "visual_reasoning" in uncovered_task_hits:
        environments.add("visual_media")

    metrics: set[str] = set()
    if "knowledge_intensive_qa" in task_hits:
        metrics.update(("exact_match", "token_f1"))
    if "fact_verification" in task_hits:
        metrics.update(("label_accuracy", "evidence_score"))
    if any(task in task_hits for task in ("sequential_decision_making", "embodied_household", "web_navigation")):
        metrics.update(("task_success_rate", "trajectory_efficiency"))
    if any(task in task_hits for task in ("code_issue_resolution", "code_generation", "code_debugging")):
        metrics.update(("pass_at_1", "test_pass_rate"))
    if set(task_hits) & {"math_reasoning", "math_word_problem", "tabular_math_reasoning"}:
        metrics.add("task_accuracy")
    if "toxicity_reduction" in task_hits:
        metrics.update(("toxicity_probability", "fluency", "generation_diversity"))
    if "audio_music_generation" in uncovered_task_hits:
        metrics.update(("audio_quality", "condition_alignment", "long_range_structure"))
    if "speech_recognition" in uncovered_task_hits:
        metrics.add("word_error_rate")
    if "image_generation" in uncovered_task_hits:
        metrics.update(("condition_alignment", "perceptual_quality"))
    if "video_generation" in uncovered_task_hits:
        metrics.update(("condition_alignment", "temporal_consistency", "perceptual_quality"))
    if "dialogue_response_generation" in uncovered_task_hits:
        metrics.update(("preference_win_rate", "response_quality"))
    if "code_optimization" in uncovered_task_hits:
        metrics.update(("runtime_improvement", "functional_correctness"))
    if "code_readability" in uncovered_task_hits:
        metrics.add("readability_quality")
    if set(uncovered_task_hits) & {"sorting", "set_intersection", "keyword_counting"}:
        metrics.add("error_count")
    if "document_merging" in uncovered_task_hits:
        metrics.update(("information_retention", "redundancy"))
    if "classical_planning" in uncovered_task_hits:
        metrics.add("plan_success_rate")
    if "logical_reasoning" in uncovered_task_hits:
        metrics.update(("answer_accuracy", "proof_accuracy"))
    if "multimodal_science_qa" in uncovered_task_hits:
        metrics.add("answer_accuracy")
    if set(uncovered_task_hits) & {"symbolic_reasoning", "algorithmic_reasoning"}:
        metrics.add("answer_accuracy")
    if "tool_augmented_nlp" in uncovered_task_hits:
        metrics.update(("answer_accuracy", "tool_execution_success"))
    if "robot_manipulation" in uncovered_task_hits:
        metrics.update(("task_success_rate", "plan_success_rate"))
    if "visual_reasoning" in uncovered_task_hits:
        metrics.add("answer_accuracy")
    if "language_modeling" in uncovered_task_hits:
        metrics.add("perplexity")
    if "financial_numerical_qa" in uncovered_task_hits:
        metrics.add("answer_accuracy")
    if "image_editing" in uncovered_task_hits:
        metrics.update(("edit_accuracy", "semantic_correctness"))
    if "creative_writing" in uncovered_task_hits:
        metrics.add("coherence_score")
    if "word_puzzle" in uncovered_task_hits:
        metrics.update(("letter_accuracy", "word_accuracy", "puzzle_success_rate"))
    if not metrics:
        metrics.add("task_accuracy")

    evidence: dict[str, list[str]] = defaultdict(list)
    for label, phrases in task_hits.items():
        evidence[f"task:{label}"].extend(phrases)
    for label, phrases in uncovered_task_hits.items():
        evidence[f"uncovered_task:{label}"].extend(phrases)
    for label, phrases in capability_hits.items():
        evidence[f"capability:{label}"].extend(phrases)
    if breadth_evidence:
        evidence["evaluation:declared_breadth"].extend(breadth_evidence)

    return CapabilityProfile(
        task_families=sorted(task_hits),
        task_benchmark_counts=task_benchmark_counts,
        uncovered_task_families=sorted(uncovered_task_hits),
        modalities=sorted(modalities),
        interactions=sorted(interactions),
        output_types=sorted(outputs),
        environments=sorted(environments),
        capabilities=sorted(capability_hits),
        suggested_metrics=sorted(metrics),
        evidence_terms=dict(sorted(evidence.items())),
        declared_evaluation_breadth=declared_evaluation_breadth,
    )
