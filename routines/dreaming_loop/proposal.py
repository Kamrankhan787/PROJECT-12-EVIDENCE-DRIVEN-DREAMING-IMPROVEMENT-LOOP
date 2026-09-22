"""Minimal improvement proposal generator."""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List
from .evidence import EvidenceValidationResult


@dataclass
class ImprovementProposal:
    problem: str
    frequency: int
    runs: List[str]
    dates: List[str]
    evidence_table: List[Dict[str, str]]
    minimal_change: str
    rule_diff: str
    target_rule_text: str
    reason: str
    branch_name: str
    raw_markdown: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem": self.problem,
            "frequency": self.frequency,
            "runs": self.runs,
            "dates": self.dates,
            "evidence_table": self.evidence_table,
            "minimal_change": self.minimal_change,
            "rule_diff": self.rule_diff,
            "target_rule_text": self.target_rule_text,
            "reason": self.reason,
            "branch_name": self.branch_name,
        }


def is_minimal_proposal(proposed_text: str) -> bool:
    """
    Guards against overly broad, speculative or bloated improvement proposals.
    Rejects proposals that attempt to rewrite entire workflows or add broad automation.
    """
    prohibited_phrases = [
        "improve the entire workflow",
        "rewrite all",
        "extensive automation",
        "overhaul",
        "complete redesign",
        "rewrite entire",
    ]
    lower = proposed_text.lower()
    for phrase in prohibited_phrases:
        if phrase in lower:
            return False
    # Ensure it is focused and concise
    if len(proposed_text.splitlines()) > 5:
        return False
    return True


def generate_branch_name(pattern_text: str) -> str:
    """Generates a safe claude/* branch name based on the problem topic."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", pattern_text.lower()).strip("-")
    slug = slug[:40].rstrip("-")
    if not slug:
        slug = "evidence-improvement"
    return f"claude/{slug}"


def generate_minimal_proposal(validation: EvidenceValidationResult) -> ImprovementProposal:
    """
    Constructs a minimal rule improvement proposal strictly derived from the validated evidence.
    """
    if not validation.is_valid or not validation.pattern:
        raise ValueError("Cannot generate proposal from invalid or rejected evidence.")

    pattern = validation.pattern
    evidence_rows: List[Dict[str, str]] = []
    for item in validation.items:
        evidence_rows.append(
            {
                "run": item.run_id,
                "date": item.date,
                "failure": item.failure,
                "correction": item.correction,
            }
        )

    # Derive focused minimal change based on the verified pattern and corrections
    problem_title = f"{pattern.pattern} repeatedly."
    branch_name = generate_branch_name(pattern.pattern)

    # Determine focused minimal change
    if "evidence" in pattern.pattern.lower() and "validation" in pattern.pattern.lower():
        minimal_change = "Add a mandatory evidence-validation checkpoint before final output generation."
        target_rule_text = "Enforce a mandatory evidence-validation checkpoint before final output generation."
    else:
        # Generic minimal rule derivation from pattern and correction
        correction_hint = validation.items[0].correction if validation.items else "apply manual check"
        minimal_change = f"Enforce corrective checkpoint to ensure {pattern.pattern.lower()} is prevented before output."
        target_rule_text = f"Enforce corrective validation to prevent: {pattern.pattern}."

    if not is_minimal_proposal(minimal_change):
        raise ValueError(f"Proposal '{minimal_change}' exceeds minimal scope boundaries.")

    reason = "Both cited runs required the same corrective intervention."

    # Build markdown diff representation
    rule_diff = (
        "```diff\n"
        " # Operational Rules\n"
        " ...\n"
        f"+8. {target_rule_text}\n"
        "```"
    )

    # Markdown format
    lines = [
        "Problem:",
        problem_title,
        "",
        "Evidence:",
    ]
    for row in evidence_rows:
        lines.append(f"Run {row['run']} — {row['date']}")
    lines.extend([
        "",
        "Frequency:",
        f"{validation.pattern.occurrences} occurrences.",
        "",
        "Minimal proposed change:",
        minimal_change,
        "",
        "Reason:",
        reason,
    ])

    return ImprovementProposal(
        problem=problem_title,
        frequency=validation.pattern.occurrences,
        runs=validation.pattern.runs,
        dates=validation.pattern.dates,
        evidence_table=evidence_rows,
        minimal_change=minimal_change,
        rule_diff=rule_diff,
        target_rule_text=target_rule_text,
        reason=reason,
        branch_name=branch_name,
        raw_markdown="\n".join(lines),
    )
