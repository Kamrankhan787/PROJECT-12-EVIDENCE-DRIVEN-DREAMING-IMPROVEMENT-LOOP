"""Test 8: Command execution tests (/goal, /loop, /schedule)."""

import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from main import main


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent

    def test_goal_command(self):
        """Verify /goal displays objectives and constraints."""
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = main(["main.py", "/goal"])
            self.assertEqual(ret, 0)
            output = fake_out.getvalue()
            self.assertIn("GOAL", output)
            self.assertIn("Real evidence required", output)
            self.assertIn("Minimum two occurrences", output)
            self.assertIn("Smallest improvement only", output)
            self.assertIn("Exactly one deletion candidate", output)
            self.assertIn("Human review required", output)
            self.assertIn("No automatic merge", output)

    def test_schedule_command_and_dry_run(self):
        """Verify /schedule displays configuration and executes dry-run simulation."""
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = main(["main.py", "/schedule"])
            self.assertEqual(ret, 0)
            output = fake_out.getvalue()
            self.assertIn("WEEKLY SCHEDULE CONFIGURATION", output)
            self.assertIn("Frequency:   Weekly", output)
            self.assertIn("human-gated", output)

        with patch("sys.stdout", new=io.StringIO()) as fake_out_dry:
            ret_dry = main(["main.py", "/schedule", "--dry-run"])
            self.assertEqual(ret_dry, 0)
            output_dry = fake_out_dry.getvalue()
            self.assertIn("Triggering scheduled dry-run execution", output_dry)
            self.assertIn("Main rules remained untouched", output_dry)

    def test_loop_dry_run_command(self):
        """Verify /loop --dry-run executes 10 stages without error."""
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = main(["main.py", "/loop", "--dry-run", "--force"])
            self.assertEqual(ret, 0)
            output = fake_out.getvalue()
            self.assertIn("[1/10] Loading state", output)
            self.assertIn("[2/10] Reading progress history", output)
            self.assertIn("[10/10] Updating state", output)
            self.assertIn("HUMAN APPROVAL REQUIRED", output)

    def test_unknown_command_help(self):
        """Verify that unknown commands output helpful guidance and return non-zero exit code."""
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            ret = main(["main.py", "/unknown"])
            self.assertEqual(ret, 1)
            output = fake_out.getvalue()
            self.assertIn("Error: Unknown command '/unknown'", output)
            self.assertIn("Usage:", output)


if __name__ == "__main__":
    unittest.main()
