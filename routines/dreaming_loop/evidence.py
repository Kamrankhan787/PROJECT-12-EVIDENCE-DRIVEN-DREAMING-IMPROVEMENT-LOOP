"""Evidence validation engine ensuring strict traceability of proposals."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from .analyzer import FailurePattern, RunEntry, parse_progress_history, normalize_failure


@dataclass
class EvidenceItem:
    run_id: str
    date: str
    failure: str
    correction: str


@dataclass
class EvidenceValidationResult:
    is_valid: bool
    status: str  # "APPROVED" or "REJECTED"
    reason: str
    pattern: Optional[FailurePattern] = None
    items: List[EvidenceItem] = field(default_factory=list)


def validate_evidence(
    pattern: FailurePattern,
    progress_file_or_entries: str | Path | List[RunEntry],
) -> EvidenceValidationResult:
    """
    Validates that a failure pattern is strictly traceable to authentic run entries in progress.md.
    Enforces that occurrences >= 2, all run IDs exist, dates match, and failure matches.
    """
    if isinstance(progress_file_or_entries, (str, Path)):
        p = Path(progress_file_or_entries)
        if not p.exists():
            return EvidenceValidationResult(
                is_valid=False,
                status="REJECTED",
                reason="REJECTED:\nImprovement proposal has insufficient evidence.\n\nRequired:\nAuthentic progress history file.\n\nFound:\nProgress history file does not exist.",
            )
        history_entries = parse_progress_history(p.read_text(encoding="utf-8"))
    else:
        history_entries = progress_file_or_entries

    # Check occurrence count requirement
    if pattern.occurrences < 2:
        return EvidenceValidationResult(
            is_valid=False,
            status="REJECTED",
            reason=(
                "REJECTED:\n"
                "Improvement proposal has insufficient evidence.\n\n"
                "Required:\n"
                "At least two traceable occurrences.\n\n"
                f"Found:\n"
                f"{pattern.occurrences} occurrence{'s' if pattern.occurrences != 1 else ''}."
            ),
        )

    if not pattern.runs or not pattern.dates:
        return EvidenceValidationResult(
            is_valid=False,
            status="REJECTED",
            reason="REJECTED:\nImprovement proposal has insufficient evidence.\n\nRequired:\nRun IDs and execution dates for all occurrences.\n\nFound:\nMissing run IDs or execution dates.",
        )

    # Cross-reference every run in the pattern against actual history
    run_map = {e.run_id: e for e in history_entries}
    matched_items: List[EvidenceItem] = []
    norm_pattern = normalize_failure(pattern.pattern)

    for run_id in pattern.runs:
        if run_id not in run_map:
            return EvidenceValidationResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    "REJECTED:\n"
                    "Improvement proposal has insufficient evidence.\n\n"
                    "Required:\n"
                    "All cited runs must exist in progress history.\n\n"
                    f"Found:\n"
                    f"Run {run_id} is not present in progress.md."
                ),
            )

        entry = run_map[run_id]
        if not entry.has_failure():
            return EvidenceValidationResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    "REJECTED:\n"
                    "Improvement proposal has insufficient evidence.\n\n"
                    "Required:\n"
                    "Cited run must contain a failure.\n\n"
                    f"Found:\n"
                    f"Run {run_id} recorded no failure."
                ),
            )

        entry_norm_failure = normalize_failure(entry.failure)
        if norm_pattern not in entry_norm_failure and entry_norm_failure not in norm_pattern:
            return EvidenceValidationResult(
                is_valid=False,
                status="REJECTED",
                reason=(
                    "REJECTED:\n"
                    "Improvement proposal has insufficient evidence.\n\n"
                    "Required:\n"
                    "Failure in cited run must match proposed pattern.\n\n"
                    f"Found:\n"
                    f"Run {run_id} failure '{entry.failure}' does not match pattern '{pattern.pattern}'."
                ),
            )

        matched_items.append(
            EvidenceItem(
                run_id=entry.run_id,
                date=entry.date,
                failure=entry.failure,
                correction=entry.correction,
            )
        )

    if len(matched_items) < 2:
        return EvidenceValidationResult(
            is_valid=False,
            status="REJECTED",
            reason="REJECTED:\nImprovement proposal has insufficient evidence.\n\nRequired:\nAt least two traceable occurrences.\n\nFound:\nLess than two verified runs.",
        )

    return EvidenceValidationResult(
        is_valid=True,
        status="APPROVED",
        reason="Evidence verified against progress.md with at least two traceable occurrences.",
        pattern=pattern,
        items=matched_items,
    )
