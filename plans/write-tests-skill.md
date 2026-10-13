# Plan: `write-tests` skill (next session)

*Written 2026-10-09. Start in a fresh conversation.*

## Focus
Build a project skill at `.claude/skills/write-tests/SKILL.md` that writes tests and test scaffolding from specs, stories and other references.
- It runs in a **fresh context via `context: fork`**, so no implementation details from the calling conversation leak in.
- Example triggers: "for story X, write unit tests", "given these specs, write backend tests", "write e2e tests".
- Output: test files and scaffolding, plus a summary of what was added or changed and the assumptions to verify.
- Run it through skill-creator: test prompts, comparing runs with and without the skill.

## Open points to decide
- **Guardrail approach.** Requirement: the skill can touch only test code and never changes app code to make tests pass. A guard script was proposed (block Write/Edit outside test paths and block reads of app source) and declined. Options:
  - instructions only + evals that check `git diff`
  - a hook in the skill's frontmatter. Caution: these stay active for the rest of the session once the skill is invoked.
  - something else
