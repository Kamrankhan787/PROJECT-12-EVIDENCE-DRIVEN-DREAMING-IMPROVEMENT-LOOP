"""Log analyzer for parsing progress history and detecting recurring patterns."""

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RunEntry:
    date: str
    run_id: str
    task: str = ""
    result: str = ""
    failure: str = ""
    correction: str = ""
    relevant_behavior: str = ""
    raw_text: str = ""

    def has_failure(self) -> bool:
        norm = self.failure.strip().lower()
        return bool(norm and norm not in ("none", "none.", "n/a", "no failure", "no failure."))


@dataclass
class FailurePattern:
    pattern: str
    occurrences: int
    runs: List[str]
    dates: List[str]
    corrections: List[str] = field(default_factory=list)
    relevant_behaviors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "occurrences": self.occurrences,
            "runs": self.runs,
            "dates": self.dates,
            "corrections": self.corrections,
            "relevant_behaviors": self.relevant_behaviors,
        }


def parse_progress_history(content: str) -> List[RunEntry]:
    """Parses progress.md markdown into structured RunEntry items."""
    entries: List[RunEntry] = []
    # Match headers like "## 2026-09-15 — Run 041" or "## 2026-09-15 - Run 041"
    header_pattern = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s+[—\-]\s+Run\s+([A-Za-z0-9_\-]+)", re.MULTILINE)
    matches = list(header_pattern.finditer(content))

    for idx, match in enumerate(matches):
        date_str = match.group(1)
        run_id = match.group(2)
        start_pos = match.end()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section = content[start_pos:end_pos].strip()

        # Parse key fields
        def extract_field(field_name: str) -> str:
            p = re.compile(rf"^{field_name}:\s*(.*?)(?=\n[A-Za-z ]+:|\n---|\Z)", re.DOTALL | re.MULTILINE | re.IGNORECASE)
            m = p.search(section)
            if m:
                return m.group(1).strip()
            return ""

        entry = RunEntry(
            date=date_str,
            run_id=run_id,
            task=extract_field("Task"),
            result=extract_field("Result"),
            failure=extract_field("Failure"),
            correction=extract_field("Correction"),
            relevant_behavior=extract_field("Relevant behavior"),
            raw_text=match.group(0) + "\n" + section,
        )
        entries.append(entry)

    return entries


def normalize_failure(failure_text: str) -> str:
    """Normalizes failure descriptions to cluster identical or near-identical issues."""
    text = failure_text.strip().rstrip(".").lower()
    # Normalize punctuation and extra spaces
    text = re.sub(r"\s+", " ", text)
    return text


def filter_entries_after_date(entries: List[RunEntry], last_date: Optional[str]) -> List[RunEntry]:
    """Filters run entries to those strictly after last_date (lexicographical ISO YYYY-MM-DD)."""
    if not last_date:
        return entries
    return [e for e in entries if e.date > last_date]


def analyze_progress(
    progress_file: str | Path,
    last_processed_date: Optional[str] = None,
    force_all: bool = False,
) -> Tuple[List[RunEntry], List[FailurePattern]]:
    """
    Parses progress.md, filters new entries since last_processed_date,
    and identifies repeated failure patterns (occurrences >= 2).
    """
    path = Path(progress_file)
    if not path.exists():
        return [], []

    content = path.read_text(encoding="utf-8")
    all_entries = parse_progress_history(content)

    if force_all or not last_processed_date:
        new_entries = all_entries
    else:
        new_entries = filter_entries_after_date(all_entries, last_processed_date)

    # Group failures
    failure_groups: Dict[str, List[RunEntry]] = {}
    for entry in new_entries:
        if entry.has_failure():
            norm_key = normalize_failure(entry.failure)
            failure_groups.setdefault(norm_key, []).append(entry)

    # Detect repeated patterns (occurrences >= 2)
    repeated_patterns: List[FailurePattern] = []
    for norm_key, grouped_entries in failure_groups.items():
        if len(grouped_entries) >= 2:
            # Pick representative canonical phrasing
            canonical_pattern = grouped_entries[0].failure.strip().rstrip(".")
            runs = [e.run_id for e in grouped_entries]
            dates = [e.date for e in grouped_entries]
            corrections = [e.correction.strip() for e in grouped_entries if e.correction]
            behaviors = [e.relevant_behavior.strip() for e in grouped_entries if e.relevant_behavior]

            repeated_patterns.append(
                FailurePattern(
                    pattern=canonical_pattern,
                    occurrences=len(grouped_entries),
                    runs=runs,
                    dates=dates,
                    corrections=corrections,
                    relevant_behaviors=behaviors,
                )
            )

    return new_entries, repeated_patterns
