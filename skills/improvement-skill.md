# Improvement Skill: Evidence-Driven Dreaming

## Overview

This skill guides the autonomous background improvement loop ("dreaming loop") that inspects historical system runs, detects recurring operational failures, extracts concrete evidence, formulates minimal corrective rule updates, proposes deletion of obsolete rules, and submits a pull request proposal subject to strict human review.

## Core Rules & Principles

1. **Evidence-First Reasoning**: Never propose an improvement without verifiable evidence from dated runs. Plausible improvements without historical evidence are strictly forbidden.
2. **Repeated-Pattern Detection**: A failure or corrective need must occur at least two times in independent runs before it qualifies as a systematic pattern warranting a rule change.
3. **Traceability**: Every claim, problem description, and corrective action must explicitly link to specific run IDs and execution dates in `progress.md`.
4. **Minimal Changes**: Propose the smallest possible modification that directly addresses the repeated failure. Avoid broad rewrites, whole-system architectural changes, or speculative optimizations.
5. **Single Deletion Proposal**: For every cycle with rule proposals, identify and propose exactly one rule whose utility has expired based on recent operational evidence.
6. **Strict Maker-Checker Separation**: The loop operates exclusively as the **Maker**. The human engineer operates as the **Checker**.
7. **No Direct Main Modification**: Under no circumstances may the loop modify `rules/rules.md` directly on `main`. All proposals must be committed to dedicated `claude/*` branches.
8. **No Unsupported Guesses**: If evidence is missing, untraceable, or occurrences < 2, produce NO proposal. "No evidence = No proposal".
