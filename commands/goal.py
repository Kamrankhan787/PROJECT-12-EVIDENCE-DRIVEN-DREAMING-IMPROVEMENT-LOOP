"""Implementation of /goal command."""

import sys


GOAL_TEXT = """GOAL

Analyze recent progress history and identify repeated failures.

Requirements:
✓ Real evidence required
✓ Minimum two occurrences
✓ Smallest improvement only
✓ Exactly one deletion candidate
✓ No unsupported guesses
✓ Proposal must use claude/ branch
✓ Human review required
✓ No automatic merge
"""


def run_goal() -> int:
    """Displays system objective, core principles, and operational constraints."""
    print(GOAL_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(run_goal())
