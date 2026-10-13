# Agent Skills Practical Cheatsheet: rubric

This is a transcription of "Agent Skills — Appendix A: The Practical Cheatsheet" (May 2026, pp. 46–52). Each item has an ID; the report cites these IDs. The **Check** column says who checks it: `script` means `scripts/check_skill.py` reports it, `judge` means you read the skill and decide, and `external` means the files alone can't show it.

## Contents
- T: Template sections (minimal SKILL.md)
- F: Folder structure
- N: Naming
- D: The description field
- R: The five rules
- Q: Quality principles
- DD: Do's and Don'ts
- S: Skill smells
- E: Eval coverage checklist
- P: Deployment checklist
- Known conflicts with the Agent Skills spec / Claude Code

---

## T: Template (the minimal SKILL.md)

| ID | Criterion | Check |
|---|---|---|
| T1 | YAML frontmatter has `name` and `description` | script |
| T2 | Optional fields are well formed if present: `version` (semver), `license`, `allowed-tools`, `metadata.author` | script |
| T3 | The body has a "When to use" section with concrete scenarios | script (heading) + judge (concreteness) |
| T4 | The body has a "When NOT to use" section | script |
| T5 | The body has a "Workflow" with numbered steps that point to `references/` for edge cases | script (heading) + judge |
| T6 | The body has "Examples" in input → output form | script (heading) + judge |
| T7 | The body has an "Output format" that points to a template in `assets/` where that makes sense | script (heading) + judge |
| T8 | The body has an "Anti-patterns to avoid" section | script |

The template is a starting point, not a hard requirement. A missing section is a **warn**, not a fail, unless leaving it out causes a real problem. For example, a skill that produces documents but has no output format is a real problem.

## F: Folder structure

| ID | Criterion | Check |
|---|---|---|
| F1 | `SKILL.md` exists at the skill root | script |
| F2 | The optional dirs `scripts/` (executable helpers), `references/` (context loaded as needed) and `assets/` (files used in output) are used for their intended purpose | script (presence) + judge (purpose) |

## N: Naming

| ID | Criterion | Check |
|---|---|---|
| N1 | Directory name is snake_case (*conflicts with the spec, see below*) | script |
| N2 | Skill name is kebab-case | script |
| N3 | Prefer the gerund form: `processing-pdfs`, not `pdf-processor` | script (heuristic) + judge |
| N4 | No generic names: `helper`, `utils`, `tools`, `data` | script |
| N5 | No vendor prefixes: `claude-*`, `gemini-*`, `anthropic-*` | script |
| N6 | No internal jargon that outsiders won't recognize | judge |

## D: The description field ("the routing algorithm")

| ID | Criterion | Check |
|---|---|---|
| D1 | States **what it does** AND **when to use it** | judge |
| D2 | Front-loads trigger keywords and is verb-led ("Generate a commit message…", not "This skill helps with…") | script (first words) + judge |
| D3 | Includes **when NOT to use**, to prevent over-triggering | script (phrase search) + judge |
| D4 | Is pushy when the model under-triggers | judge |
| D5 | ≤1024 chars in YAML (hard limit); ≤200 chars for the API; aim for ~50 words | script |

## R: The five rules

| ID | Rule | Check |
|---|---|---|
| R1 | **One skill, one job.** If you can't describe it in one sentence, it is two skills | judge |
| R2 | **Descriptions are an interface.** A vague description means an unused skill | judge (overlaps D) |
| R3 | **Skills are dependencies.** Version them, pin them, review them in PRs. "A skill without a test is a hope, not a capability" | script (version, evals present) + external (PR review) |
| R4 | **The right team owns the right skill.** Domain experts own domain skills | external (ownership; `metadata.author` is a weak signal) |
| R5 | **The agent runtime is interchangeable.** Don't tie a skill to one runtime | judge (runtime-specific tools, paths, frontmatter) |

## Q: Quality principles

| ID | Principle | Check |
|---|---|---|
| Q1 | Run the task yourself first: the skill should reflect real failures, not speculation | external / judge (does it name concrete gotchas?) |
| Q2 | Give the reason, not just the rule. Caps-lock ALWAYS/NEVER is a yellow flag | script (count) + judge (are rules explained?) |
| Q3 | Every line earns its place. Keep gotchas, exact commands, business logic and anti-patterns. Cut boilerplate the model already knows | judge |
| Q4 | One skill, one job. If the description needs "and" between unrelated capabilities, split it | judge |
| Q5 | Instructions are verifiable. If the agent can't tell whether it followed a rule, the rule is too vague | judge |
| Q6 | Bundle what repeats. Helper code the agent keeps re-deriving belongs in `scripts/` | judge |

## DD: Do's and Don'ts

Do:
| ID | Item | Check |
|---|---|---|
| DD1 | Start small and concrete | judge |
| DD2 | Description includes what, when, and when not | (same as D1/D3) |
| DD3 | Trust progressive disclosure: the body points to `references/` instead of inlining everything | script (references used) + judge |
| DD4 | Bundle deterministic work in `scripts/`, not as instructions | judge |
| DD5 | Treat skills as code | (same as R3) |
| DD6 | Skills + MCPs, not Skills vs. MCPs | judge |
| DD7 | Has test cases and controlled, programmatic evaluation | script (evals present) |

Don't:
| ID | Item | Check |
|---|---|---|
| DD8 | Vague descriptions like "helps with documents" | script (phrase) + judge |
| DD9 | SKILL.md body over 5,000 words | script |
| DD10 | Hard-coded paths or secrets | script |
| DD11 | "Always do X" rules that belong in AGENTS.md (project-wide rules, not workflow steps) | judge |
| DD12 | Untrusted third-party libraries or skills installed without scanning | judge (install commands in the body/scripts) |
| DD13 | Reinventing MCP as scripts (scripts that wrap an API an MCP server already provides) | judge |

## S: Skill smells (revise if you see these)

| ID | Smell | Check |
|---|---|---|
| S1 | Over 5,000 words: probably two skills, or reference material that belongs in `references/` | script |
| S2 | Two domain teams could plausibly own it, so it isn't decomposed yet | judge |
| S3 | You can't write three test cases for it: too vague, or does too much | judge (try to write three; include them in the report) |
| S4 | It doesn't reference any other resource, so it may just be a long instruction that belongs in a system prompt | script |
| S5 | It keeps adding "edge cases" sections; each one probably wants its own skill | script (count) |
| S6 | The description starts with "a helpful skill for…". It should name the trigger, the inputs and the output | script |

## E: Eval coverage checklist

The skill counts as "evaluated" only when all four items are satisfied. **Any failure holds the skill at the draft tier, however well it does on the happy path.**

| ID | Item | Check |
|---|---|---|
| E1 | Trigger: positive AND negative test cases, targeting 90% trigger accuracy | script (looks for trigger evals) + external (accuracy) |
| E2 | Execution: correct outputs across a representative range of inputs | script (execution evals present) + external |
| E3 | Regression: adding this skill causes zero drops in the existing library suite | external |
| E4 | Token budget: co-loaded with 5–15 frequently active skills, it doesn't degrade unrelated turns | external |

## P: Deployment checklist

| ID | Item | Check |
|---|---|---|
| P1 | Frontmatter validates (lint passes) | script |
| P2 | Description includes what + when + when-not | (same as D1/D3) |
| P3 | Scripts have unit tests passing in CI | script (tests present) + external (CI) |
| P4 | Eval suite passes in CI with a min-pass threshold | external |
| P5 | Security scan clean (no secrets, no untrusted deps) | script (secrets) + judge |
| P6 | Description reviewed by someone other than the author | external |
| P7 | Cross-tool install paths tested if shipping publicly | external |
| P8 | Org-level admin provisioning updated (if applicable) | external |

## Workflow the cheatsheet recommends (for context on Q1/E)

1. Have an experienced practitioner narrate three workflows.
2. Run the most repeated one without any skill; note where the agent fails.
3. Draft SKILL.md from the transcript, and write three eval cases (two positive, one negative) **before** the body.
4. Ship to a read-only tier and iterate on the description until trigger accuracy clears 90%.

---

## Known conflicts with the Agent Skills spec / Claude Code

Report these as **conflicts**, not failures. Say which way the skill went and why that's acceptable or not.

- **N1 vs. directory = name.** The Agent Skills spec and Claude Code expect the directory name to match `name`, which must be kebab-case. A snake_case directory with a kebab-case name breaks that. Prefer kebab-case for both, and note that the cheatsheet disagrees.
- **T2 `version` at the top level.** The Agent Skills spec has no top-level `version` field. It goes under `metadata.version`. Claude Code ignores unknown keys, so either works there. Accept either, and mention the portable form.
- **D5 ≤200 chars.** This limit only matters for surfaces that truncate descriptions. A longer description is fine for Claude Code as long as it stays under 1024 chars, and length is often deliberate: telling the skill apart from a sibling skill (for example, by naming its tool prefixes) takes words. Warn, don't fail. In the report, say whether the extra length is doing routing work or is just padding.
- **Claude Code-only frontmatter** (`context`, `agent`, `hooks`, `disable-model-invocation`, `user-invocable`, `argument-hint`, `model`, …). These are legitimate, but they tie the skill to one runtime (R5). Note it, and fail it only if the skill claims to be portable.
