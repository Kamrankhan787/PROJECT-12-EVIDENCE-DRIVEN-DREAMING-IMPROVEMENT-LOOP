"""State management for the dreaming improvement loop."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json


def _parse_yaml_value(val: str) -> Any:
    val = val.strip()
    if val in ("null", "~", "None", ""):
        return None
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        items = [i.strip().strip("'\"") for i in inner.split(",")]
        return [i for i in items if i]
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]
    if len(val) > 1 and val.startswith("0") and val[1].isdigit():
        # Preserve numbers with leading zeros (like run IDs "041", "046") as strings
        return val
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def load_state(file_path: str | Path) -> Dict[str, Any]:
    """Loads dreaming-state.md into a Python dictionary."""
    path = Path(file_path)
    if not path.exists():
        return {
            "last_processed_date": None,
            "last_run_id": None,
            "previous_analysis": None,
            "detected_patterns": [],
            "proposed_changes": [],
            "deletion_candidate": None,
            "pr_branch": None,
            "pr_status": "idle",
            "last_updated": None,
        }

    lines = path.read_text(encoding="utf-8").splitlines()
    state: Dict[str, Any] = {}
    current_list_key: Optional[str] = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("- ") and current_list_key:
            item_val = line[2:].strip().strip("'\"")
            state[current_list_key].append(item_val)
            continue

        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val:
                state[key] = []
                current_list_key = key
            else:
                current_list_key = None
                state[key] = _parse_yaml_value(val)

    defaults = {
        "last_processed_date": None,
        "last_run_id": None,
        "previous_analysis": None,
        "detected_patterns": [],
        "proposed_changes": [],
        "deletion_candidate": None,
        "pr_branch": None,
        "pr_status": "idle",
        "last_updated": None,
    }
    for k, v in defaults.items():
        if k not in state:
            state[k] = v

    return state


def save_state(file_path: str | Path, state: Dict[str, Any]) -> None:
    """Serializes the state dictionary into dreaming-state.md in clean YAML format."""
    path = Path(file_path)
    lines: List[str] = []

    def format_scalar(v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v)
        if len(s) > 1 and s.startswith("0") and s[1].isdigit():
            return f'"{s}"'
        if any(c in s for c in (":", "#", "[", "]", "{", "}")) or "\n" in s:
            s_escaped = s.replace('"', '\\"')
            return f'"{s_escaped}"'
        return s

    for key, value in state.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"  - {json.dumps(item)}")
                    else:
                        lines.append(f"  - {format_scalar(item)}")
        else:
            lines.append(f"{key}: {format_scalar(value)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
