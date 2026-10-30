Here's the draft to-do list. I haven't written the context file yet, so you can change the list first.

**Shared setup (on main, before branching)**
- [ ] Pick one small feature as the test target for every branch, so results are comparable.
- [ ] Write the seed test by hand in your project's style.
- [ ] Write the evaluation rubric in `EVAL.md`: locator quality, no hard-coded waits, assertion strength, plan traceability, token cost, and what each role can read and write.

**Branch 1: `explore/playwright-test-agents`** (official planner, generator, healer)
- [ ] Run `npx playwright init-agents --loop=claude` and read the three generated agent files and `.mcp.json`.
- [ ] Record each agent's tools line, especially planner and healer, which I haven't seen.
- [ ] Run planner, then generator, then healer on the target feature.
- [ ] Note how the generator's write-only-through-`generator_write_test` restriction behaves in practice.
- [ ] Record token usage per agent.

**Branch 2: `explore/playwright-cli-skills`** (agent CLI plus skills)
- [ ] Install with `npm install -g @playwright/cli@latest` and `playwright-cli install --skills`.
- [ ] Read the generated SKILL.md and its reference files.
- [ ] Write a minimal planner and writer prompt on top of it, with no agent definitions.
- [ ] Compare token cost against branch 1 (the CLI is meant to be lighter than MCP).

**Branch 3: `explore/community-yusuf-plugin`**
- [ ] Install the plugin (`/plugin marketplace add yusuftayman/playwright-cli-agents`).
- [ ] Study how the shared `e2e` skill is preloaded through `skills:` frontmatter.
- [ ] Adapt the paths and conventions to your project.
- [ ] Run its three agents on the target feature.

**Branch 4: `explore/custom-skills-design`** (your own design)
- [ ] Create a shared conventions skill (layout, naming, locators, waits, seed conventions).
- [ ] Create role skills: `test-planner`, `test-writer` (with unit, integration, API and E2E references) and `test-reviewer`.
- [ ] Create subagents for planner, writer and reviewer, each preloading the shared skill plus its own.
- [ ] Add permissions: reviewer read-only, planner writes to `specs/`, writer writes to `tests/` plus the Tier 2 config paths you approve.
- [ ] Add a PreToolUse hook for path allowlists and test it by asking the writer to edit `package.json`.
- [ ] Add the blocker-report behaviour for work the writer can't do itself.
- [ ] Decide whether a test-scaffolder is needed or a README checklist is enough.

**Wrap-up**
- [ ] Fill in a comparison table across branches from `EVAL.md`.
- [ ] Decide which parts to merge (likely official patterns plus your custom reviewer and permissions).

Two things to confirm before I write the context file: do you want the file named something like `CLAUDE.md` or a separate `docs/test-skills-context.md`, and should it include the permissions table and the tiered scaffolding rules from earlier, or only the summary and the list?