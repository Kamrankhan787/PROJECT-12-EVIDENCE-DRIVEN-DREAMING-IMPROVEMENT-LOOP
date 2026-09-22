# Evidence-Backed Improvement Proposal

## Problem

Evidence validation was skipped repeatedly.

## Evidence

| Run | Date | Failure | Correction |
|-----|------|---------|------------|
| 041 | 2026-09-15 | Evidence validation was skipped. | Evidence validation was manually performed before final output. |
| 044 | 2026-09-21 | Evidence validation was skipped. | Evidence validation was manually performed before final output. |

## Frequency

2 occurrences.

## Proposed Change

Add a mandatory evidence-validation checkpoint before final output generation.

```diff
 # Operational Rules
 ...
+8. Enforce a mandatory evidence-validation checkpoint before final output generation.
```

## Why This Change

Both cited runs required the same corrective intervention.

## Deletion Candidate

Rule: "Perform an additional manual formatting check after every run."
Evidence: No recent run required this check.
Runs examined: 041, 042, 043, 044, 045, 046
Recommendation: Remove or simplify this rule.

## Human Gate

This proposal requires human review.

The rules must not be changed on main until the proposal is explicitly approved and merged.
