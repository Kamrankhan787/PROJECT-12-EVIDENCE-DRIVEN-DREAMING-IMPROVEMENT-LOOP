"""Test 7: Dreaming state update and boundary tracking tests."""

from pathlib import Path
import tempfile
import unittest

from routines.dreaming_loop.loop import run_dreaming_loop
from routines.dreaming_loop.state import load_state


class TestStateUpdate(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent

    def test_state_updates_after_successful_loop(self):
        """Verify dreaming-state.md fields are updated after processing entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "rules.md").write_text("# Rules\n7. Perform an additional manual formatting check after every run.\n", encoding="utf-8")

            (tmp_path / "progress.md").write_text((self.base_dir / "progress.md").read_text(encoding="utf-8"), encoding="utf-8")

            initial_state_content = (
                "last_processed_date: 2026-09-14\n"
                "last_run_id: null\n"
                "previous_analysis: null\n"
                "detected_patterns: []\n"
                "proposed_changes: []\n"
                "deletion_candidate: null\n"
                "pr_branch: null\n"
                "pr_status: idle\n"
                "last_updated: null\n"
            )
            state_file = tmp_path / "dreaming-state.md"
            state_file.write_text(initial_state_content, encoding="utf-8")

            result = run_dreaming_loop(base_dir=tmp_path, quiet=True)
            self.assertTrue(result.success)

            updated_state = load_state(state_file)

            # Check boundary advancement
            self.assertEqual(updated_state["last_processed_date"], "2026-09-22")
            self.assertEqual(updated_state["last_run_id"], "046")
            self.assertIsNotNone(updated_state["last_updated"])
            self.assertIn("Evidence validation was skipped", updated_state["detected_patterns"][0])
            self.assertIn("mandatory evidence-validation checkpoint", updated_state["proposed_changes"][0])
            self.assertEqual(updated_state["pr_status"], "pending_human_review")
            self.assertTrue(updated_state["pr_branch"].startswith("claude/"))

    def test_avoid_redundant_reprocessing(self):
        """A second run immediately following a successful cycle should find no new entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir(parents=True)
            (rules_dir / "rules.md").write_text("# Rules\n7. Perform an additional manual formatting check after every run.\n", encoding="utf-8")
            (tmp_path / "progress.md").write_text((self.base_dir / "progress.md").read_text(encoding="utf-8"), encoding="utf-8")
            (tmp_path / "dreaming-state.md").write_text("last_processed_date: 2026-09-14\n", encoding="utf-8")

            # First run: processes entries through 2026-09-22
            first_run = run_dreaming_loop(base_dir=tmp_path, quiet=True)
            self.assertTrue(first_run.has_proposal)

            # Second run: boundary is now 2026-09-22, so no new entries exist
            second_run = run_dreaming_loop(base_dir=tmp_path, quiet=True)
            self.assertFalse(second_run.has_proposal)
            self.assertEqual(len(second_run.runs_examined), 0)
            self.assertIn("No evidence-backed improvement identified", second_run.message)

            # Third run with force_all=True: forces re-analysis
            third_run = run_dreaming_loop(base_dir=tmp_path, force_all=True, quiet=True)
            self.assertTrue(third_run.has_proposal)
            self.assertGreater(len(third_run.runs_examined), 0)


if __name__ == "__main__":
    unittest.main()
