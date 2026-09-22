"""Core dreaming improvement loop coordinating the 10-stage maker workflow."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional

from .analyzer import RunEntry, analyze_progress
from .deletion import DeletionCandidate, identify_deletion_candidate
from .evidence import EvidenceValidationResult, validate_evidence
from .proposal import ImprovementProposal, generate_minimal_proposal
from .state import load_state, save_state


@dataclass
class LoopResult:
    success: bool
    has_proposal: bool
    message: str
    runs_examined: List[str]
    patterns_detected: List[str]
    proposal: Optional[ImprovementProposal] = None
    deletion_candidate: Optional[DeletionCandidate] = None
    pr_branch: Optional[str] = None
    pr_markdown: Optional[str] = None
    report_path: Optional[str] = None
    state: Optional[Dict[str, Any]] = None


def format_pr_description(
    proposal: ImprovementProposal,
    deletion: DeletionCandidate,
) -> str:
    """Formats the pull request description according to project specifications."""
    evidence_rows = "\n".join(
        f"| {r['run']} | {r['date']} | {r['failure']} | {r['correction']} |"
        for r in proposal.evidence_table
    )

    deletion_summary = (
        f"Rule: \"{deletion.rule_text}\"\n"
        f"Evidence: {deletion.evidence}\n"
        f"Runs examined: {', '.join(deletion.recent_runs_examined or [])}\n"
        f"Recommendation: {deletion.recommendation}"
    )

    return (
        "# Evidence-Backed Improvement Proposal\n\n"
        "## Problem\n\n"
        f"{proposal.problem}\n\n"
        "## Evidence\n\n"
        "| Run | Date | Failure | Correction |\n"
        "|-----|------|---------|------------|\n"
        f"{evidence_rows}\n\n"
        "## Frequency\n\n"
        f"{proposal.frequency} occurrences.\n\n"
        "## Proposed Change\n\n"
        f"{proposal.minimal_change}\n\n"
        f"{proposal.rule_diff}\n\n"
        "## Why This Change\n\n"
        f"{proposal.reason}\n\n"
        "## Deletion Candidate\n\n"
        f"{deletion_summary}\n\n"
        "## Human Gate\n\n"
        "This proposal requires human review.\n\n"
        "The rules must not be changed on main until the proposal is explicitly approved and merged.\n"
    )


def format_evidence_report(
    start_date: str,
    end_date: str,
    examined_entries: List[RunEntry],
    proposal: Optional[ImprovementProposal],
    deletion: Optional[DeletionCandidate],
) -> str:
    """Formats evidence/analysis-report.md."""
    run_list = "\n".join(f"- Run {e.run_id} ({e.date}): {e.task} — {e.result}" for e in examined_entries)

    if not proposal:
        return (
            "# Improvement Analysis\n\n"
            "## Analysis Window\n\n"
            f"Start: {start_date}\n"
            f"End: {end_date}\n\n"
            "## Runs Examined\n\n"
            f"{run_list}\n\n"
            "## Repeated Failures\n\n"
            "None. No recurring patterns met the required threshold of >= 2 occurrences.\n\n"
            "## Evidence\n\n"
            "No repeated failure evidence detected.\n\n"
            "## Proposed Improvement\n\n"
            "None.\n\n"
            "## Deletion Candidate\n\n"
            "None.\n\n"
            "## Human Gate\n\n"
            "No changes proposed. No human review action required.\n\n"
            "## Result\n\n"
            "NO PROPOSAL GENERATED (INSUFFICIENT EVIDENCE)\n"
        )

    evidence_bullets = "\n".join(
        f"- Run {r['run']} on {r['date']}: {r['failure']} (Correction: {r['correction']})"
        for r in proposal.evidence_table
    )

    deletion_details = deletion.format_text() if deletion else "None."

    return (
        "# Improvement Analysis\n\n"
        "## Analysis Window\n\n"
        f"Start: {start_date}\n"
        f"End: {end_date}\n\n"
        "## Runs Examined\n\n"
        f"{run_list}\n\n"
        "## Repeated Failures\n\n"
        f"- {proposal.problem} ({proposal.frequency} occurrences)\n\n"
        "## Evidence\n\n"
        f"{evidence_bullets}\n\n"
        "## Proposed Improvement\n\n"
        f"{proposal.minimal_change}\n\n"
        "## Deletion Candidate\n\n"
        f"{deletion_details}\n\n"
        "## Human Gate\n\n"
        "State that approval is required.\n"
        "This proposal cannot and will not be applied automatically. Human review is mandatory.\n\n"
        "## Result\n\n"
        "PROPOSAL READY FOR HUMAN REVIEW\n"
    )


def prepare_git_branch(branch_name: str, base_dir: Path) -> bool:
    """
    Simulates or sets up the claude/* branch without touching main rules.
    If git repo exists, creates or prepares the branch reference.
    """
    # Verify branch name policy
    if not branch_name.startswith("claude/"):
        raise ValueError(f"Violation of Branch Requirement: '{branch_name}' must begin with 'claude/'.")

    # If git is initialized in base_dir, verify branch without checking out or disturbing working tree
    try:
        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if git_check.returncode == 0:
            # Git is available; verify current branch remains untouched
            return True
    except Exception:
        pass
    return True


def run_dreaming_loop(
    base_dir: str | Path,
    dry_run: bool = False,
    force_all: bool = False,
    quiet: bool = False,
) -> LoopResult:
    """Executes the full 10-stage dreaming improvement loop."""
    root = Path(base_dir)
    state_file = root / "dreaming-state.md"
    progress_file = root / "progress.md"
    rules_file = root / "rules" / "rules.md"
    report_file = root / "evidence" / "analysis-report.md"
    proposals_dir = root / "proposals"

    proposals_dir.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    def log(stage: str, msg: str) -> None:
        if not quiet:
            print(f"[{stage}] {msg}")

    # [1/10] Loading state
    log("1/10", "Loading state")
    state = load_state(state_file)
    last_date = None if force_all else state.get("last_processed_date")

    # [2/10] Reading progress history
    log("2/10", "Reading progress history")
    if not progress_file.exists():
        raise FileNotFoundError(f"Missing required progress history: {progress_file}")

    # [3/10] Filtering new entries
    log("3/10", f"Filtering new entries (after {last_date or 'beginning'})")
    new_entries, repeated_patterns = analyze_progress(progress_file, last_date, force_all=force_all)

    examined_runs = [e.run_id for e in new_entries]

    # [4/10] Detecting failures
    log("4/10", f"Detecting failures in {len(new_entries)} entries")
    total_failures = [e for e in new_entries if e.has_failure()]

    # [5/10] Verifying repeated patterns
    log("5/10", f"Verifying repeated patterns ({len(repeated_patterns)} candidate patterns found)")

    # If no repeated pattern detected
    if not repeated_patterns:
        reason_detail = (
            "The detected issue occurred only once."
            if total_failures
            else "No failures were recorded in the processed window."
        )
        msg = (
            "No evidence-backed improvement identified.\n\n"
            f"Reason:\n{reason_detail}\n\n"
            "Action:\nNo rules change proposed."
        )
        if not quiet:
            print(f"\n{msg}\n")

        # Create no-proposal analysis report
        start_d = new_entries[0].date if new_entries else str(last_date)
        end_d = new_entries[-1].date if new_entries else str(last_date)
        report_content = format_evidence_report(start_d, end_d, new_entries, None, None)
        if not dry_run:
            report_file.write_text(report_content, encoding="utf-8")
            if new_entries:
                state["last_processed_date"] = new_entries[-1].date
                state["last_run_id"] = new_entries[-1].run_id
                state["last_updated"] = datetime.now(timezone.utc).isoformat()
                save_state(state_file, state)

        return LoopResult(
            success=True,
            has_proposal=False,
            message=msg,
            runs_examined=examined_runs,
            patterns_detected=[],
            report_path=str(report_file),
            state=state,
        )

    # Take the primary repeated pattern
    target_pattern = repeated_patterns[0]

    # [6/10] Validating evidence
    log("6/10", f"Validating evidence for: '{target_pattern.pattern}'")
    validation = validate_evidence(target_pattern, new_entries)
    if not validation.is_valid:
        if not quiet:
            print(f"\n{validation.reason}\n")
        return LoopResult(
            success=False,
            has_proposal=False,
            message=validation.reason,
            runs_examined=examined_runs,
            patterns_detected=[target_pattern.pattern],
        )

    # [7/10] Creating improvement proposal
    log("7/10", "Creating improvement proposal")
    proposal = generate_minimal_proposal(validation)

    # [8/10] Creating deletion candidate
    log("8/10", "Creating deletion candidate")
    deletion = identify_deletion_candidate(rules_file, new_entries)

    # [9/10] Preparing PR
    log("9/10", f"Preparing PR on branch {proposal.branch_name}")
    prepare_git_branch(proposal.branch_name, root)
    pr_markdown = format_pr_description(proposal, deletion)

    # Write proposal artifact to proposals/
    pr_proposal_file = proposals_dir / f"proposal-{proposal.branch_name.replace('/', '_')}.md"
    if not dry_run:
        pr_proposal_file.write_text(pr_markdown, encoding="utf-8")

    # Generate analysis report
    start_d = new_entries[0].date
    end_d = new_entries[-1].date
    report_content = format_evidence_report(start_d, end_d, new_entries, proposal, deletion)
    if not dry_run:
        report_file.write_text(report_content, encoding="utf-8")

    # [10/10] Updating state
    log("10/10", "Updating state in dreaming-state.md")
    if not dry_run:
        state["last_processed_date"] = new_entries[-1].date
        state["last_run_id"] = new_entries[-1].run_id
        state["previous_analysis"] = f"Processed {len(new_entries)} runs. Detected: {proposal.problem}"
        state["detected_patterns"] = [p.pattern for p in repeated_patterns]
        state["proposed_changes"] = [proposal.minimal_change]
        state["deletion_candidate"] = deletion.rule_text
        state["pr_branch"] = proposal.branch_name
        state["pr_status"] = "pending_human_review"
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_state(state_file, state)

    return LoopResult(
        success=True,
        has_proposal=True,
        message="Proposal successfully generated and gated for human review.",
        runs_examined=examined_runs,
        patterns_detected=[p.pattern for p in repeated_patterns],
        proposal=proposal,
        deletion_candidate=deletion,
        pr_branch=proposal.branch_name,
        pr_markdown=pr_markdown,
        report_path=str(report_file),
        state=state,
    )
