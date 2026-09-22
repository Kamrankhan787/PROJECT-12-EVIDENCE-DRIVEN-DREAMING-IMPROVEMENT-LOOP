"""Test 3: Minimal proposal generation and scope constraint tests."""

from pathlib import Path
import unittest

from routines.dreaming_loop.analyzer import FailurePattern
from routines.dreaming_loop.evidence import EvidenceItem, EvidenceValidationResult
from routines.dreaming_loop.proposal import (
    generate_minimal_proposal,
    is_minimal_proposal,
)


class TestMinimalProposal(unittest.TestCase):
    def setUp(self):
        self.pattern = FailurePattern(
            pattern="Evidence validation was skipped",
            occurrences=2,
            runs=["041", "044"],
            dates=["2026-09-15", "2026-09-21"],
        )
        self.validation = EvidenceValidationResult(
            is_valid=True,
            status="APPROVED",
            reason="Traceable evidence verified.",
            pattern=self.pattern,
            items=[
                EvidenceItem("041", "2026-09-15", "Evidence validation was skipped.", "Manual validation performed"),
                EvidenceItem("044", "2026-09-21", "Evidence validation was skipped.", "Manual validation performed"),
            ],
        )

    def test_minimal_proposal_generation(self):
        """Verify that the generated proposal directly addresses the repeated failure."""
        proposal = generate_minimal_proposal(self.validation)

        self.assertIn("Evidence validation was skipped repeatedly", proposal.problem)
        self.assertEqual(proposal.frequency, 2)
        self.assertEqual(proposal.runs, ["041", "044"])
        self.assertIn("Add a mandatory evidence-validation checkpoint", proposal.minimal_change)
        self.assertIn("Both cited runs required the same corrective intervention", proposal.reason)
        self.assertTrue(proposal.branch_name.startswith("claude/"))

    def test_reject_broad_or_unrelated_proposals(self):
        """Verify that overly broad, bloated, or unrelated proposals are rejected."""
        broad_proposals = [
            "Improve the entire workflow.",
            "Rewrite all validation logic from scratch.",
            "Add extensive automation to handle all operations.",
            "Complete redesign of error handling framework.\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6",
        ]
        for broad in broad_proposals:
            self.assertFalse(
                is_minimal_proposal(broad),
                f"Should have rejected broad proposal: '{broad}'",
            )

    def test_accept_tightly_scoped_proposals(self):
        """Verify that concise, focused proposals pass the scope check."""
        valid_minimal = "Add a mandatory evidence-validation checkpoint before final output generation."
        self.assertTrue(is_minimal_proposal(valid_minimal))


if __name__ == "__main__":
    unittest.main()
