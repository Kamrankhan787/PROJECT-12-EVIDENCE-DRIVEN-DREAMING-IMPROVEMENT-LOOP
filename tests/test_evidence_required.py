"""Test 2 & 24: Evidence required and no-evidence safety test."""

from pathlib import Path
import tempfile
import unittest

from routines.dreaming_loop.analyzer import FailurePattern
from routines.dreaming_loop.evidence import validate_evidence
from routines.dreaming_loop.loop import run_dreaming_loop


class TestEvidenceRequired(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.progress_file = self.base_dir / "progress.md"

    def test_fake_untraceable_run_is_rejected(self):
        """Proposals citing non-existent run IDs must be strictly rejected."""
        fake_pattern = FailurePattern(
            pattern="Evidence validation was skipped",
            occurrences=2,
            runs=["999", "998"],  # Non-existent run IDs
            dates=["2026-09-15", "2026-09-21"],
        )

        result = validate_evidence(fake_pattern, self.progress_file)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "REJECTED")
        self.assertIn("REJECTED:", result.reason)
        self.assertIn("insufficient evidence", result.reason.lower())
        self.assertIn("Run 999 is not present in progress.md", result.reason)

    def test_single_occurrence_pattern_is_rejected(self):
        """A pattern with only 1 occurrence must be rejected by evidence validation."""
        single_pattern = FailurePattern(
            pattern="Network socket timeout",
            occurrences=1,
            runs=["042"],
            dates=["2026-09-17"],
        )

        result = validate_evidence(single_pattern, self.progress_file)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "REJECTED")
        self.assertIn("At least two traceable occurrences", result.reason)

    def test_no_evidence_safety_behavior_single_failure_log(self):
        """
        Section 24: Mandatory safety test.
        When logs contain only one occurrence of a failure:
        The system must output:
          No evidence-backed improvement identified.
          Reason: The detected issue occurred only once.
          Action: No rules change proposed.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "rules.md").write_text("# Rules\n1. Rule 1\n", encoding="utf-8")

            # Create log with only one single failure
            single_failure_progress = (
                "# Progress\n\n"
                "## 2026-09-15 — Run 101\n"
                "Task: Build report\n"
                "Result: Failed\n"
                "Failure: Unexpected memory spike.\n"
                "Correction: Worker process was restarted.\n"
                "Relevant behavior: Worker process lifecycle.\n\n"
                "---\n\n"
                "## 2026-09-16 — Run 102\n"
                "Task: Process batch\n"
                "Result: Completed successfully\n"
                "Failure: None\n"
                "Correction: None\n"
                "Relevant behavior: Batch processing completed.\n"
            )
            (tmp_path / "progress.md").write_text(single_failure_progress, encoding="utf-8")
            (tmp_path / "dreaming-state.md").write_text("last_processed_date: null\n", encoding="utf-8")

            res = run_dreaming_loop(base_dir=tmp_path, quiet=True)

            self.assertTrue(res.success)
            self.assertFalse(res.has_proposal)
            self.assertIn("No evidence-backed improvement identified.", res.message)
            self.assertIn("Reason:\nThe detected issue occurred only once.", res.message)
            self.assertIn("Action:\nNo rules change proposed.", res.message)
            self.assertIsNone(res.proposal)
            self.assertIsNone(res.pr_branch)


if __name__ == "__main__":
    unittest.main()
