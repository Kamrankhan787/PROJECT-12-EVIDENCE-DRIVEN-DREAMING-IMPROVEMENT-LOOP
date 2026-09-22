"""Implementation of /loop command executing the 10-stage dreaming cycle."""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from routines.dreaming_loop.loop import run_dreaming_loop


def run_loop(args: Optional[List[str]] = None, base_dir: Optional[str | Path] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="/loop",
        description="Run an evidence-driven improvement loop cycle over progress history.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the analysis, evidence validation, and PR preparation without updating files or state.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force full re-analysis across all historical records regardless of last_processed_date.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress intermediate stage output.",
    )

    parsed = parser.parse_args(args)
    root_dir = Path(base_dir) if base_dir else Path.cwd()

    if parsed.dry_run:
        print("[DRY-RUN MODE ACTIVE: No state or files will be modified]\n")

    result = run_dreaming_loop(
        base_dir=root_dir,
        dry_run=parsed.dry_run,
        force_all=parsed.force,
        quiet=parsed.quiet,
    )

    if not result.has_proposal:
        # No repeated pattern or insufficient evidence
        return 0

    if result.proposal and result.deletion_candidate:
        print("\n==================================================")
        print("SUMMARY OF EVIDENCE-BACKED IMPROVEMENT PROPOSAL")
        print("==================================================")
        print(f"Problem: {result.proposal.problem}")
        print(f"Frequency: {result.proposal.frequency} occurrences")
        print(f"Supporting runs: {', '.join(result.proposal.runs)}")
        print(f"Minimal change: {result.proposal.minimal_change}")
        print(f"PR Branch: {result.proposal.branch_name}")
        print("--------------------------------------------------")
        print(f"Deletion candidate: \"{result.deletion_candidate.rule_text}\"")
        print(f"Deletion status: {result.deletion_candidate.status}")
        print("--------------------------------------------------")
        print("Human Gate:")
        print("HUMAN APPROVAL REQUIRED. Proposal cannot be merged automatically.")
        print("Rules on main remain untouched.")
        print("==================================================\n")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(run_loop(sys.argv[1:]))
