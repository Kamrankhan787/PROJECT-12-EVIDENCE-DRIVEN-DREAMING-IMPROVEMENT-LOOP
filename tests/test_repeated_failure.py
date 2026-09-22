"""Test 1: Repeated failure detection from historical logs."""

from pathlib import Path
import unittest

from routines.dreaming_loop.analyzer import analyze_progress


class TestRepeatedFailureDetection(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.progress_file = self.base_dir / "progress.md"

    def test_planted_repeated_failure_is_detected(self):
        """Verify analyzer discovers the planted repeated failure with occurrences=2 and runs 041, 044."""
        self.assertTrue(self.progress_file.exists(), "progress.md must exist")

        new_entries, repeated_patterns = analyze_progress(
            self.progress_file,
            last_processed_date="2026-09-14",
        )

        self.assertGreaterEqual(len(repeated_patterns), 1, "Must detect at least 1 repeated pattern")

        primary_pattern = repeated_patterns[0]

        # Verify pattern details
        self.assertIn("evidence validation was skipped", primary_pattern.pattern.lower())
        self.assertEqual(primary_pattern.occurrences, 2, "Expected exactly 2 occurrences")
        self.assertEqual(primary_pattern.runs, ["041", "044"], "Must cite runs 041 and 044")
        self.assertEqual(primary_pattern.dates, ["2026-09-15", "2026-09-21"])

    def test_single_occurrence_failure_is_not_treated_as_pattern(self):
        """Verify that single occurrence issues (e.g. Run 042 socket timeout) are not treated as repeated patterns."""
        new_entries, repeated_patterns = analyze_progress(
            self.progress_file,
            last_processed_date="2026-09-14",
        )

        detected_names = [p.pattern.lower() for p in repeated_patterns]
        for name in detected_names:
            self.assertNotIn("socket timeout", name)


if __name__ == "__main__":
    unittest.main()
