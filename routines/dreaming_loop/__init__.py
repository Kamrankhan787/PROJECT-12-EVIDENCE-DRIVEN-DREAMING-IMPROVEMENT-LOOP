"""Dreaming Improvement Loop package."""

from .loop import run_dreaming_loop
from .state import load_state, save_state
from .analyzer import analyze_progress
from .evidence import validate_evidence
from .proposal import generate_minimal_proposal
from .deletion import identify_deletion_candidate

__all__ = [
    "run_dreaming_loop",
    "load_state",
    "save_state",
    "analyze_progress",
    "validate_evidence",
    "generate_minimal_proposal",
    "identify_deletion_candidate",
]
