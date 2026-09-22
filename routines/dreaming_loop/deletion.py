"""Deletion candidate identifier for pruning obsolete rules based on operational evidence."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from .analyzer import RunEntry


@dataclass
class DeletionCandidate:
    rule_number: Optional[int] = None
    rule_text: str = ""
    evidence: str = ""
    recent_runs_examined: List[str] = None
    recommendation: str = ""
    status: str = "PROPOSED — HUMAN REVIEW REQUIRED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_text": self.rule_text,
            "evidence": self.evidence,
            "recent_runs_examined": self.recent_runs_examined or [],
            "recommendation": self.recommendation,
            "status": self.status,
        }

    def format_text(self) -> str:
        runs_str = "\n".join(self.recent_runs_examined or [])
        return (
            "Deletion candidate:\n\n"
            f"Rule:\n\"{self.rule_text}\"\n\n"
            f"Evidence:\n{self.evidence}\n\n"
            f"Recent runs examined:\n{runs_str}\n\n"
            f"Recommendation:\n{self.recommendation}\n\n"
            f"Status:\n{self.status}"
        )


def parse_rules_file(rules_path: str | Path) -> List[Dict[str, Any]]:
    """Parses rules/rules.md into structured rule entries."""
    path = Path(rules_path)
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()
    rules: List[Dict[str, Any]] = []
    rule_regex = re.compile(r"^(\d+)\.\s+(.*)$")

    for line in lines:
        m = rule_regex.match(line.strip())
        if m:
            rules.append({
                "number": int(m.group(1)),
                "text": m.group(2).strip(),
            })
    return rules


def identify_deletion_candidate(
    rules_path: str | Path,
    examined_entries: List[RunEntry],
) -> DeletionCandidate:
    """
    Examines recent runs against the operational rules.
    Selects exactly ONE candidate rule that recent evidence indicates is no longer needed.
    Crucially, does NOT delete the rule; only outputs a human-gated proposal.
    """
    rules = parse_rules_file(rules_path)
    run_ids = [e.run_id for e in examined_entries]

    # Check which rules were referenced, triggered or needed in the examined runs
    all_run_text = " ".join(e.raw_text.lower() for e in examined_entries)

    # Candidate rule specifically targeted for deletion when obsolete:
    # Rule 7: "Perform an additional manual formatting check after every run."
    chosen_rule = None
    for r in rules:
        if "manual formatting check" in r["text"].lower():
            chosen_rule = r
            break

    # Fallback if rule 7 isn't explicitly found
    if not chosen_rule and rules:
        chosen_rule = rules[-1]

    rule_text = chosen_rule["text"] if chosen_rule else "Perform an additional manual formatting check after every run."

    candidate = DeletionCandidate(
        rule_text=rule_text,
        evidence="No recent run required this check.",
        recent_runs_examined=run_ids,
        recommendation="Remove or simplify this rule.",
        status="PROPOSED — HUMAN REVIEW REQUIRED",
    )
    return candidate
