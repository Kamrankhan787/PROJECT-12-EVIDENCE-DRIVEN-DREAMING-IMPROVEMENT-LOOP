# Project 12 — Evidence-Driven Dreaming Improvement Loop

An autonomous, evidence-driven background improvement system that inspects dated operational history, discovers recurring failure patterns, extracts concrete evidence, formulates minimal rule updates on isolated branches, proposes candidate rule deletions, and enforces a strict human gate before any modification can reach the main operational rules.

---

## 1. Project Purpose

Complex systems that operate continuously often encounter intermittent edge cases, operational snags, and procedural ambiguities. When left unattended, manual interventions accumulate and procedures become stale.

Traditional automated improvement mechanisms frequently suffer from a fatal flaw: **speculative hallucination or guesswork**. An autonomous system that guesses improvements without empirical proof risks introducing operational regression and unpredictable behavior.

This project implements the core principle:

```text
NO EVIDENCE
    ↓
NO PROPOSAL
```

Rather than guessing:

```text
NO EVIDENCE
    ↓
GUESS
    ↓
CHANGE FUTURE BEHAVIOR  (PROHIBITED)
```

The system operates as an **Evidence-Driven Dreaming Improvement Loop**. In human cognition, "dreaming" during rest consolidates episodic memories, identifies patterns, and prunes unused pathways. Similarly, on a scheduled weekly cadence, this dreaming loop awakens, processes dated execution runs, validates that issues have repeated at least twice, drafts the smallest possible rule modification on a dedicated branch, proposes the deletion of an obsolete rule, and halts before the human gate.

---

## 2. Architecture

```text
+-------------------------------------------------------------------------------+
|                               OPERATIONAL SPINE                               |
|                                                                               |
|   progress.md (Run History) ------------+                                     |
|                                         |                                     |
|   dreaming-state.md (Boundary Tracking) +                                     |
|                                         |                                     |
|   rules/rules.md (Main Rules)           |                                     |
+-----------------------------------------|-------------------------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------+
|                       DREAMING IMPROVEMENT LOOP (MAKER)                       |
|                                                                               |
|   [1/10] Loading state                                                        |
|   [2/10] Reading progress history                                             |
|   [3/10] Filtering new entries                                                |
|   [4/10] Detecting failures                                                   |
|   [5/10] Verifying repeated patterns (Threshold >= 2 occurrences)             |
|   [6/10] Validating evidence (Traceable run IDs & dates)                      |
|   [7/10] Creating improvement proposal (Minimal scoped delta)                 |
|   [8/10] Creating deletion candidate (Exactly 1 unused rule)                   |
|   [9/10] Preparing PR (Branch: claude/* & proposals/)                         |
|   [10/10] Updating state (Advance boundary in dreaming-state.md)              |
+-------------------------------------------------------------------------------+
                                          |
                                          v
+-------------------------------------------------------------------------------+
|                                  HUMAN GATE                                   |
|                                                                               |
|                         [ STOP / REVIEW / DECIDE ]                            |
|                                                                               |
|        Human Checker Reviews Evidence -> Rejects or Merges PR to Main         |
+-------------------------------------------------------------------------------+
```

The system consists of three distinct tiers:
1. **The Operational Spine**: Authentic historical records (`progress.md`), boundary state tracking (`dreaming-state.md`), and active baseline rules (`rules/rules.md`).
2. **The Autonomous Dreaming Loop (Maker)**: Reads logs, aggregates recurring failures, verifies evidence, crafts minimal targeted improvements and a single deletion candidate, and outputs a pull request proposal.
3. **The Human Gate (Checker)**: Enforces maker-checker separation. The dreaming loop is strictly forbidden from directly modifying `rules/rules.md` on `main` or automatically merging its own proposal.

---

## 3. Concepts Demonstrated

* **Spine and Improvement Loop**: The operational history (`progress.md`) acts as an immutable chronological spine. The dreaming loop operates over this spine without mutating past history.
* **Maker-Checker**: The improvement loop functions strictly as the Maker (proposing changes backed by evidence). The human engineer functions as the Checker (evaluating evidence and approving or rejecting).
* **Schedule**: Execution runs on a predictable recurring weekly cadence defined in `config/schedule.json` (Sundays at 23:00) with full dry-run support.
* **Human Gate**: An absolute barrier blocking automatic merges. The system prepares a pull request on an isolated branch and stops completely.

---

## 4. Command Reference

### `/goal`
Displays the active system objective, operational constraints, and verification checklist.

```bash
python main.py /goal
```

**Output:**
```text
GOAL

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
```

### `/loop`
Executes one complete 10-stage dreaming cycle across progress history.

```bash
# Standard incremental run
python main.py /loop

# Dry-run mode (simulates analysis without modifying state or files)
python main.py /loop --dry-run

# Force full historical re-analysis regardless of last_processed_date
python main.py /loop --force
```

### `/schedule`
Displays or configures the weekly schedule.

```bash
# View current schedule
python main.py /schedule

# Run scheduled dry run simulation
python main.py /schedule --dry-run

# Update schedule time and day
python main.py /schedule --day Sunday --time 23:00
```

---

## 5. Project Structure

```text
PROJECT-12-DREAMING-IMPROVEMENT-LOOP/
│
├── README.md                           # Complete project documentation
├── main.py                             # CLI entry point routing commands
├── progress.md                         # Dated operational run history
├── dreaming-state.md                   # State and boundary tracking
├── .gitignore                          # Standard Python environment exclusions
│
├── rules/
│   └── rules.md                        # Operational baseline rules on main
│
├── skills/
│   └── improvement-skill.md            # Improvement loop guidelines & constraints
│
├── routines/
│   └── dreaming_loop/
│       ├── __init__.py                 # Package exports
│       ├── loop.py                     # 10-stage dreaming loop orchestrator
│       ├── analyzer.py                 # Log parser and failure clusterer
│       ├── evidence.py                 # Evidence verification & validation engine
│       ├── proposal.py                 # Minimal improvement proposal generator
│       ├── deletion.py                 # Exactly one deletion candidate selector
│       └── state.py                    # Dreaming state loader & serializer
│
├── commands/
│   ├── __init__.py                 # Command module exports
│   ├── goal.py                     # /goal command
│   ├── loop.py                     # /loop command
│   └── schedule.py                 # /schedule command
│
├── config/
│   └── schedule.json               # Weekly cron/schedule configuration
│
├── proposals/
│   └── .gitkeep                    # Storage directory for PR proposal artifacts
│
├── evidence/
│   ├── planted-failure.md          # Documentation of deliberate test failure
│   └── analysis-report.md          # Generated analysis audit report
│
└── tests/
    ├── __init__.py                 # Test package
    ├── test_repeated_failure.py    # Validates detection of planted failure
    ├── test_evidence_required.py   # Validates evidence verification & no-evidence safety
    ├── test_minimal_proposal.py    # Validates proposal scoping & broad rewrite rejection
    ├── test_deletion_candidate.py  # Validates exactly 1 deletion candidate
    ├── test_human_gate.py          # Validates stop-at-gate & maker-checker enforcement
    ├── test_branch_protection.py   # Validates branch prefix & main protection
    ├── test_state_update.py        # Validates state advancement & boundary tracking
    └── test_commands.py            # Validates CLI commands (/goal, /loop, /schedule)
```

---

## 6. Progress History (`progress.md`)

The progress file represents the historical spine of the system. It contains at least one week of authentic dated run entries spanning 2026-09-15 through 2026-09-22.

Each entry follows this standardized format:
```markdown
## 2026-09-15 — Run 041

Task:
Generate evidence-backed report.

Result:
Completed with manual correction.

Failure:
Evidence validation was skipped.

Correction:
Evidence validation was manually performed before final output.

Relevant behavior:
Evidence validation should occur before final output.
```

Runs recorded in the baseline log:
* **Run 041** (2026-09-15): Generate evidence-backed report — Failure: Evidence validation was skipped. (Correction applied).
* **Run 042** (2026-09-17): Sync distributed telemetry — Failure: Network socket timeout (Handled automatically on retry; single occurrence).
* **Run 043** (2026-09-18): Generate scheduled report — Success (No failure).
* **Run 044** (2026-09-21): Generate evidence-backed report — Failure: Evidence validation was skipped. (Correction applied).
* **Run 045** (2026-09-21): Archive weekly audit artifacts — Success (No failure).
* **Run 046** (2026-09-22): Reindex search catalog and verify indexes — Success (No failure; completed without manual formatting checks).

---

## 7. Dreaming State (`dreaming-state.md`)

The dreaming state tracks what the improvement loop has already processed to prevent redundant re-analysis across historical runs.

```yaml
last_processed_date: 2026-09-14
last_run_id: null
previous_analysis: null
detected_patterns: []
proposed_changes: []
deletion_candidate: null
pr_branch: null
pr_status: idle
last_updated: null
```

After each successful `/loop` run, the state updates:
* `last_processed_date`: Advanced to the date of the latest run examined (e.g. `2026-09-22`).
* `last_run_id`: Advanced to the ID of the latest run examined (e.g. `"046"`).
* `previous_analysis`: Summary of the run and detected problems.
* `detected_patterns`: List of detected repeated failure patterns.
* `proposed_changes`: Proposed minimal rule updates.
* `deletion_candidate`: Candidate rule proposed for removal.
* `pr_branch`: Name of the prepared branch (`claude/...`).
* `pr_status`: Marked as `pending_human_review`.
* `last_updated`: Timestamp of execution.

---

## 8. Failure Detection

The analyzer in `routines/dreaming_loop/analyzer.py`:
1. Parses markdown headers and structured fields.
2. Filters entries strictly after `last_processed_date`.
3. Normalizes failure descriptions (casing, whitespace, punctuation).
4. Groups failures by normalized intent.
5. Calculates occurrence counts.
6. Filters for patterns where `occurrences >= 2`.

---

## 9. Evidence Verification

Implemented in `routines/dreaming_loop/evidence.py`. Every proposal must pass rigorous validation:
* **Traceable Run IDs**: Every cited run must exist in `progress.md`.
* **Traceable Dates**: Execution dates must match authentic run entries.
* **Failure Evidence**: Each cited run must record an actual failure matching the pattern.
* **Frequency Threshold**: The pattern must appear at least twice.
* **Rejection**: If any check fails, the proposal is rejected with a clear explanation:

```text
REJECTED:
Improvement proposal has insufficient evidence.

Required:
At least two traceable occurrences.

Found:
One occurrence.
```

---

## 10. Improvement Proposal

Implemented in `routines/dreaming_loop/proposal.py`.
The proposal must be the smallest reasonable change directly connected to the evidence:

```text
Problem:
Evidence validation was skipped repeatedly.

Evidence:
Run 041 — 2026-09-15
Run 044 — 2026-09-21

Frequency:
2 occurrences.

Minimal proposed change:
Add a mandatory evidence-validation checkpoint before final output generation.

Reason:
Both cited runs required the same corrective intervention.
```

Broad proposals (such as "Improve the entire workflow" or "Rewrite all validation logic") are rejected by validation guards.

---

## 11. Deletion Proposal

Implemented in `routines/dreaming_loop/deletion.py`.
The loop proposes **exactly one** deletion candidate based on evidence from recent runs:

```text
Deletion candidate:

Rule:
"Perform an additional manual formatting check after every run."

Evidence:
No recent run required this check.

Recent runs examined:
041
042
043
044
045
046

Recommendation:
Remove or simplify this rule.

Status:
PROPOSED — HUMAN REVIEW REQUIRED
```

The system **never automatically deletes** the rule. Deletion is proposed exclusively for human review.

---

## 12. Maker-Checker Workflow & Human Gate

The architecture enforces strict separation of duties:
* **Maker (Autonomous Loop)**: Analyzes logs -> Formulates proposal -> Formats PR description -> Prepares branch -> Generates audit report -> **STOPS**.
* **Checker (Human Engineer)**: Reads PR proposal -> Examines evidence -> Accepts or Rejects -> Merges to main if approved.

The loop **never** modifies `rules/rules.md` on `main` and **never** performs an automatic merge.

---

## 13. Branch Strategy & PR Workflow

* Every proposed improvement branch is prefixed with `claude/`:
  Example: `claude/evidence-validation-was-skipped`
* Target branches such as `main`, `master`, or `develop` are protected and rejected if targeted.
* The PR proposal is saved to `proposals/` and includes an evidence table, problem statement, minimal diff, deletion candidate, and explicit human gate declaration.

---

## 14. Planted Failure

Documented in `evidence/planted-failure.md`:
* Deliberate failure: `Evidence validation was skipped.`
* First occurrence: Run 041 (2026-09-15).
* Second occurrence: Run 044 (2026-09-21).
* The analyzer discovers this pattern dynamically from `progress.md` without hardcoding.

---

## 15. Dry-Run Mode

Dry-run mode (`/loop --dry-run` or `/schedule --dry-run`) executes the full pipeline:
* Reads and parses `progress.md`.
* Detects recurring failures and validates evidence.
* Generates the minimal improvement proposal and deletion candidate.
* Simulates branch and PR preparation.
* **Guarantees**: Does not write to `dreaming-state.md`, does not write files to `rules/`, and performs no git commits.

---

## 16. Test Strategy

The test suite in `tests/` verifies all critical safety constraints:

| Test File | Safety Invariant Tested |
|---|---|
| `test_repeated_failure.py` | Detects planted failure (Runs 041 & 044, occurrences = 2). Ignores single failures. |
| `test_evidence_required.py` | Rejects fake/untraceable runs. Verifies "No evidence -> No proposal" safety behavior. |
| `test_minimal_proposal.py` | Verifies minimal change generation and rejects broad/unscoped proposals. |
| `test_deletion_candidate.py` | Confirms exactly one deletion candidate is produced with human review status. |
| `test_human_gate.py` | Verifies system stops at gate and marks PR status as `pending_human_review`. |
| `test_branch_protection.py` | Enforces `claude/*` branch prefix and verifies `rules/rules.md` on `main` is untouched. |
| `test_state_update.py` | Verifies `dreaming-state.md` boundary advancement and prevents redundant re-runs. |
| `test_commands.py` | Verifies `/goal`, `/loop`, `/schedule`, `--dry-run`, and error handling. |

To run all tests:
```bash
python -m unittest discover -s tests -v
```

---

## 17. Limitations

1. **Structured Log Format**: The analyzer expects dated headers and key-value sections in `progress.md`. Unstructured free-form notes require manual normalization.
2. **Offline Git Fallback**: When operating in environments without an active git repository, branch operations are safely recorded in `proposals/` artifacts.
3. **Single Deletion Scope**: The system targets one obsolete rule per cycle to maintain controlled, incremental policy evolution.

---

## 18. Example Execution Walkthrough

```bash
# 1. Inspect active goals and constraints
$ python main.py /goal
GOAL
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

# 2. Check weekly schedule
$ python main.py /schedule
WEEKLY SCHEDULE CONFIGURATION
--------------------------------------------------
Status:      ENABLED
Frequency:   Weekly
Schedule:    Every Sunday at 23:00
Command:     /loop
Mode:        human-gated (Strict Maker-Checker)
Dry Run:     False
--------------------------------------------------

# 3. Run the improvement loop
$ python main.py /loop
[1/10] Loading state
[2/10] Reading progress history
[3/10] Filtering new entries (after 2026-09-14)
[4/10] Detecting failures in 6 entries
[5/10] Verifying repeated patterns (1 candidate patterns found)
[6/10] Validating evidence for: 'Evidence validation was skipped'
[7/10] Creating improvement proposal
[8/10] Creating deletion candidate
[9/10] Preparing PR on branch claude/evidence-validation-was-skipped
[10/10] Updating state in dreaming-state.md

==================================================
SUMMARY OF EVIDENCE-BACKED IMPROVEMENT PROPOSAL
==================================================
Problem: Evidence validation was skipped repeatedly.
Frequency: 2 occurrences
Supporting runs: 041, 044
Minimal change: Add a mandatory evidence-validation checkpoint before final output generation.
PR Branch: claude/evidence-validation-was-skipped
--------------------------------------------------
Deletion candidate: "Perform an additional manual formatting check after every run."
Deletion status: PROPOSED — HUMAN REVIEW REQUIRED
--------------------------------------------------
Human Gate:
HUMAN APPROVAL REQUIRED. Proposal cannot be merged automatically.
Rules on main remain untouched.
==================================================
```
