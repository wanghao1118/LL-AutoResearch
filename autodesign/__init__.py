"""Thin execution API for the AutoDesign design-then-run workflow."""

from .effects import check_design, compare_effects, validate_expected_effects
from .runner import STAGE_ORDER, execution_completion_errors, run_local_commands
from .skillflow import advance_skill_run, initialize_skill_run, inspect_skill_run
from .skillresults import ingest_skill_results, summarize_skill_results

__all__ = [
    "STAGE_ORDER",
    "advance_skill_run",
    "check_design",
    "compare_effects",
    "execution_completion_errors",
    "ingest_skill_results",
    "initialize_skill_run",
    "inspect_skill_run",
    "run_local_commands",
    "summarize_skill_results",
    "validate_expected_effects",
]

__version__ = "0.4.0"
