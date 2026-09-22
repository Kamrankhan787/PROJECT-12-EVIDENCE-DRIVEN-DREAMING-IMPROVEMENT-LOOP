"""Test 4: Deletion candidate selection and human gate preservation."""

from pathlib import Path
import unittest

from routines.dreaming_loop.analyzer import parse_progress_history
from routines.dreaming_loop.deletion import (
    identify_deletion_candidate,
    parse_rules_file,
)


class TestDeletionCandidate(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.rules_file = self.base_dir / "rules" / "rules.md"
        self.progress_file = self.base_dir / "progress.md"

    def test_exactly_one_deletion_candidate_produced(self):
        """Verify that exactly one deletion candidate is identified based on recent run history."""
        self.assertTrue(self.rules_file.exists())
        self.assertTrue(self.progress_file.exists())

        entries = parse_progress_history(self.progress_file.read_text(encoding="utf-8"))
        candidate = identify_deletion_candidate(self.rules_file, entries)

        self.assertIsNotNone(candidate)
        self.assertIn("manual formatting check", candidate.rule_text.lower())
        self.assertEqual(candidate.status, "PROPOSED — HUMAN REVIEW REQUIRED")
        self.assertEqual(candidate.recommendation, "Remove or simplify this rule.")
        self.assertIn("No recent run required this check", candidate.evidence)
        self.assertGreaterEqual(len(candidate.recent_runs_examined), 5)

    def test_rules_file_is_not_automatically_mutated(self):
        """Verify that identifying a deletion candidate does NOT delete or modify rules.md."""
        original_content = self.rules_file.read_text(encoding="utf-8")
        entries = parse_progress_history(self.progress_file.read_text(encoding="utf-8"))

        _ = identify_deletion_candidate(self.rules_file, entries)

        current_content = self.rules_file.read_text(encoding="utf-8")
        self.assertEqual(original_content, current_content, "rules/rules.md must never be mutated during analysis")


if __name__ == "__main__":
    unittest.main()
