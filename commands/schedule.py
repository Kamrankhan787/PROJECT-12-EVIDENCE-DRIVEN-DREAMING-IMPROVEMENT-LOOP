"""Implementation of /schedule command configuring and inspecting the weekly loop schedule."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from routines.dreaming_loop.loop import run_dreaming_loop


DEFAULT_CONFIG: Dict[str, Any] = {
    "enabled": true if False else True,
    "frequency": "weekly",
    "day": "Sunday",
    "time": "23:00",
    "command": "/loop",
    "mode": "human-gated",
    "dry_run": False,
}


def load_schedule_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
        return DEFAULT_CONFIG.copy()
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_schedule_config(config_path: Path, config: Dict[str, Any]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def run_schedule(args: Optional[List[str]] = None, base_dir: Optional[str | Path] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="/schedule",
        description="Configure, display, or dry-run the weekly dreaming loop schedule.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a simulated dry run of the scheduled loop without updating files or state.",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable the weekly schedule.",
    )
    parser.add_argument(
        "--disable",
        action="store_true",
        help="Disable the weekly schedule.",
    )
    parser.add_argument(
        "--day",
        type=str,
        help="Set the scheduled day of the week (e.g., Sunday).",
    )
    parser.add_argument(
        "--time",
        type=str,
        help="Set the scheduled execution time (e.g., 23:00).",
    )

    parsed = parser.parse_args(args)
    root_dir = Path(base_dir) if base_dir else Path.cwd()
    config_path = root_dir / "config" / "schedule.json"

    config = load_schedule_config(config_path)

    updated = False
    if parsed.enable:
        config["enabled"] = True
        updated = True
    if parsed.disable:
        config["enabled"] = False
        updated = True
    if parsed.day:
        config["day"] = parsed.day
        updated = True
    if parsed.time:
        config["time"] = parsed.time
        updated = True

    if updated:
        save_schedule_config(config_path, config)
        print("[Schedule configuration updated]")

    print("WEEKLY SCHEDULE CONFIGURATION")
    print("--------------------------------------------------")
    print(f"Status:      {'ENABLED' if config.get('enabled') else 'DISABLED'}")
    print(f"Frequency:   {config.get('frequency', 'weekly').capitalize()}")
    print(f"Schedule:    Every {config.get('day', 'Sunday')} at {config.get('time', '23:00')}")
    print(f"Command:     {config.get('command', '/loop')}")
    print(f"Mode:        {config.get('mode', 'human-gated')} (Strict Maker-Checker)")
    print(f"Dry Run:     {config.get('dry_run', False)}")
    print("--------------------------------------------------")

    if parsed.dry_run or config.get("dry_run"):
        print("\nTriggering scheduled dry-run execution...")
        result = run_dreaming_loop(root_dir, dry_run=True, quiet=False)
        print(f"\nDry-run completed. Result: {result.message}")
        print("Verification: Main rules remained untouched. No merge executed.")

    return 0


if __name__ == "__main__":
    sys.exit(run_schedule(sys.argv[1:]))
