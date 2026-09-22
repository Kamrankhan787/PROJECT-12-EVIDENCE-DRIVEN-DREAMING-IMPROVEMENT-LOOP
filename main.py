#!/usr/bin/env python3
"""
Main entry point for Project 12: Evidence-Driven Dreaming Improvement Loop.

Supported Commands:
  /goal      - Display the current system objective and operational constraints.
  /loop      - Run a 10-stage dreaming cycle over progress history.
  /schedule  - View, configure, or dry-run the scheduled weekly loop.
"""

from pathlib import Path
import sys
from typing import List

# Ensure UTF-8 output encoding across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from commands.goal import run_goal
from commands.loop import run_loop
from commands.schedule import run_schedule


HELP_TEXT = """Evidence-Driven Dreaming Improvement Loop

Usage:
  python main.py /goal               Display objectives, requirements, and constraints
  python main.py /loop [options]     Execute an improvement loop cycle
  python main.py /schedule [options] Configure, inspect, or dry-run weekly schedule

Commands:
  /goal                  Show project goals and maker-checker constraints.
  /loop                  Run the 10-stage evidence-driven analysis cycle.
    --dry-run            Simulate analysis and PR generation without writing state.
    --force              Process all history regardless of last_processed_date.
    --quiet              Suppress stage logging output.
  /schedule              Display weekly schedule configuration.
    --dry-run            Run a scheduled simulation cycle.
    --enable / --disable Toggle scheduled runs.
    --day <Day>          Update scheduled day (e.g., Sunday).
    --time <Time>        Update scheduled time (e.g., 23:00).

Note: Commands can be prefixed with '/' (e.g., /loop) or invoked directly (e.g., loop).
"""


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(HELP_TEXT)
        return 0

    cmd = argv[1].strip().lower()
    # Normalize optional leading slash
    normalized_cmd = cmd.lstrip("/")
    sub_args = argv[2:]

    base_dir = Path(__file__).resolve().parent

    if normalized_cmd == "goal":
        return run_goal()
    elif normalized_cmd == "loop":
        return run_loop(sub_args, base_dir=base_dir)
    elif normalized_cmd == "schedule":
        return run_schedule(sub_args, base_dir=base_dir)
    elif normalized_cmd in ("help", "-h", "--help"):
        print(HELP_TEXT)
        return 0
    else:
        print(f"Error: Unknown command '{cmd}'.\n")
        print(HELP_TEXT)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
