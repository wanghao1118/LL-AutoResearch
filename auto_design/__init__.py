"""Thin execution API for the AutoDesign design-then-run workflow."""

from .effects import check_design, compare_effects, validate_expected_effects
from .results import ingest_results, summarize_results
from .runner import STAGE_ORDER, execution_completion_errors, run_local_commands
from .state import advance_run, initialize_run, inspect_run

__all__ = [
    "STAGE_ORDER",
    "advance_run",
    "check_design",
    "compare_effects",
    "execution_completion_errors",
    "ingest_results",
    "initialize_run",
    "inspect_run",
    "run_local_commands",
    "summarize_results",
    "validate_expected_effects",
]

__version__ = "0.4.0"
