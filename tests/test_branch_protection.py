"""Test 6: Branch protection and isolation verification."""

from pathlib import Path
import tempfile
import unittest

from routines.dreaming_loop.loop import prepare_git_branch, run_dreaming_loop
from routines.dreaming_loop.proposal import generate_branch_name


class TestBranchProtection(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent

    def test_branch_name_starts_with_claude_prefix(self):
        """Every generated branch must strictly begin with 'claude/'."""
        branch = generate_branch_name("Evidence validation was skipped")
        self.assertTrue(branch.startswith("claude/"))
        self.assertNotIn("main", branch)
        self.assertNotIn("master", branch)
        self.assertNotIn("develop", branch)

    def test_reject_unprotected_branch_names(self):
        """Direct attempts to target protected branches must fail."""
        prohibited = ["main", "master", "develop", "feature/unprotected"]
        for b in prohibited:
            with self.assertRaises(ValueError) as ctx:
                prepare_git_branch(b, self.base_dir)
            self.assertIn("Violation of Branch Requirement", str(ctx.exception))

    def test_main_rules_remain_unmodified_on_disk(self):
        """Verify that rules/rules.md on main is never modified by the loop."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rules_dir = tmp_path / "rules"
            rules_dir.mkdir(parents=True)
            original_rules = "# Main Rules\n1. Initial rule\n"
            rules_file = rules_dir / "rules.md"
            rules_file.write_text(original_rules, encoding="utf-8")

            (tmp_path / "progress.md").write_text((self.base_dir / "progress.md").read_text(encoding="utf-8"), encoding="utf-8")
            (tmp_path / "dreaming-state.md").write_text((self.base_dir / "dreaming-state.md").read_text(encoding="utf-8"), encoding="utf-8")

            result = run_dreaming_loop(base_dir=tmp_path, force_all=True, quiet=True)

            self.assertTrue(result.success)
            self.assertTrue(result.has_proposal, "Expected a proposal to be generated")
            self.assertTrue(result.proposal.branch_name.startswith("claude/"))
            self.assertEqual(rules_file.read_text(encoding="utf-8"), original_rules)


if __name__ == "__main__":
    unittest.main()
