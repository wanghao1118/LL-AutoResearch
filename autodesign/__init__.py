"""Thin execution API for the Skill-first AutoDesign workflow."""

from .runner import STAGE_ORDER, execution_completion_errors, run_local_commands
from .skillflow import advance_skill_run, initialize_skill_run, inspect_skill_run, verify_skill_run
from .skillresults import ingest_skill_results, summarize_skill_results

__all__ = [
    "STAGE_ORDER",
    "advance_skill_run",
    "execution_completion_errors",
    "ingest_skill_results",
    "initialize_skill_run",
    "inspect_skill_run",
    "run_local_commands",
    "summarize_skill_results",
    "verify_skill_run",
]

__version__ = "0.3.0"
