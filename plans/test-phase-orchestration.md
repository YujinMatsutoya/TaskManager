# Plan (deferred): `test-phase` orchestrator skill

> Saved for later, 2026-10-09. Builds on the `write-tests` skill (`plans/write-tests-skill.md`).

## Context
The goal is an orchestrated test phase: requirements → write tests → review (optionally sending work back to the writer) → summary report. Code and tests are written in the same conversation, so the main session needs to keep its context. The writer and reviewer need isolation: tests written from the spec only, independent review, guardrails scoped to each agent. Subagents can't start other subagents, so the coordination has to run in the main session. A skill fits that.

## Design: hybrid
- **Keep `test-writer` and `test-reviewer` as subagents** (`.claude/agents/`). They keep their own context, model, tool limits, and agent-scoped hooks.
  - test-writer: confinement hook in its frontmatter (Write/Edit only under `backend/tests/`, `frontend/tests/`).
  - test-reviewer: already read-only (no Write/Edit tools).
- **New inline skill `.claude/skills/test-phase/SKILL.md`** that runs in the main session. It carries **no hooks**, because hooks declared in a skill stay on for the rest of the session.

## Skill workflow
1. **Requirements:** identify the story from the arguments or conversation. Pull the acceptance criteria from `Development_Backlog.md` and `Task_Manager_Spec.md`, and the changed files from `git diff main...HEAD --name-only`. Write a self-contained brief: story, criteria, changed-file names (names only, so test-writer stays spec-driven), test level.
2. **Write:** start `test-writer` with the brief and keep its agent ID.
3. **Review:** start `test-reviewer` on the files test-writer produced.
   - Verdict "needs revision" → send the findings back to the same test-writer (SendMessage) → review again.
   - Cap at 2 rounds. Assumption disputes go to the user instead of looping.
4. **Report:** one merged summary:
   - files added or changed
   - coverage (happy/edge/error)
   - failing tests, read as places where the implementation doesn't match the spec
   - reviewer findings by catch-log category (coverage gaps, wrong assertions, over-mocking, flaky/async, wrong layer, inherited assumptions)
   - final per-file verdict
   - combined **Assumptions to verify**
   - optionally, an entry ready to paste into the `Development_Backlog.md` catch log

## Evals
- Each run is `claude -p` in a throwaway git worktree. Baseline: the same prompt without the skill.
- Planted bug in the implementation → it is reported, not fixed. `git diff` touches only `*/tests/**` and manifests or lockfiles.
- A deliberately weak test is already present → the reviewer flags it and the writer revises it within the cap.
- The report has every section. The skill fires on "run the test phase for story X" and "let's do tests + review for this".

## Open questions for later
- Should the skill also update the backlog catch log automatically, or only propose an entry?
- Should test-reviewer run `--cov` every time, or only when asked?
