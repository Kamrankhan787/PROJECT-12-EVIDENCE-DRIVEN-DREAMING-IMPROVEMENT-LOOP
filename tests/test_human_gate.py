"""Test 5: Human gate verification and maker-checker separation."""

from pathlib import Path
import tempfile
import unittest

from routines.dreaming_loop.loop import run_dreaming_loop
from routines.dreaming_loop.state import load_state


class TestHumanGate(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent

    def test_human_gate_blocks_auto_merge(self):
        """Verify that loop execution stops at PR creation and marks status as pending human review."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir(parents=True)
            original_rules = (
                "# Operational Rules\n\n"
                "1. Validate evidence before producing a final output.\n\n"
                "2. Do not claim success without supporting evidence.\n\n"
                "7. Perform an additional manual formatting check after every run.\n"
            )
            rules_file = rules_dir / "rules.md"
            rules_file.write_text(original_rules, encoding="utf-8")

            # Copy progress.md and initial state
            (tmp_path / "progress.md").write_text((self.base_dir / "progress.md").read_text(encoding="utf-8"), encoding="utf-8")
            (tmp_path / "dreaming-state.md").write_text((self.base_dir / "dreaming-state.md").read_text(encoding="utf-8"), encoding="utf-8")

            result = run_dreaming_loop(base_dir=tmp_path, force_all=True, quiet=True)

            self.assertTrue(result.success)
            self.assertTrue(result.has_proposal)

            # State check: pr_status must NOT be merged or completed; it must require human review
            state = load_state(tmp_path / "dreaming-state.md")
            self.assertEqual(state["pr_status"], "pending_human_review")
            self.assertNotEqual(state["pr_status"], "merged")
            self.assertNotEqual(state["pr_status"], "auto_merged")

            # Rules check: main rules must NOT have been modified
            self.assertEqual(rules_file.read_text(encoding="utf-8"), original_rules)

            # PR markdown check: Must include explicit Human Gate section
            self.assertIn("## Human Gate", result.pr_markdown)
            self.assertIn("This proposal requires human review.", result.pr_markdown)
            self.assertIn("The rules must not be changed on main until the proposal is explicitly approved and merged.", result.pr_markdown)


if __name__ == "__main__":
    unittest.main()
