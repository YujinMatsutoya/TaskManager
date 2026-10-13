---
name: assessing-skills
description: |
  Grade an Agent Skill against the Agent Skills Cheatsheet and report concrete fixes. Use to review, audit, lint or ship-check a SKILL.md. Do NOT use to create skills, run evals, or review code.
license: MIT
metadata:
  version: 1.0.0
---

# Assessing skills

Grade one skill folder against the cheatsheet rubric in `references/cheatsheet.md` and hand back a report the author can act on. The rubric mixes mechanical checks (lengths, names, missing files) with judgment calls (does it do one job? are rules explained?). A script handles the first kind, so your attention goes to the second. That's where an assessment actually earns its keep.

## When to use
- "Review my skill at `~/.claude/skills/foo`" / "is this SKILL.md ready to ship?"
- "Grade this skill against the cheatsheet / best practices"
- "Why isn't my skill triggering?" (when the cause is likely to be its description)
- The user pastes a SKILL.md and asks for feedback

## When NOT to use
- Creating or iterating on a skill. That's skill-creator. You can run this assessment at the end of that work.
- Measuring trigger accuracy or running eval suites. This skill only checks that they *exist*; it doesn't execute them.
- Reviewing app code, prompts, CLAUDE.md or AGENTS.md.

## Workflow

1. **Locate the skill.** Resolve the path to the folder that contains `SKILL.md`. If the user pasted only the text, write it to a temporary folder as `SKILL.md` and say that folder checks (scripts, references, evals) can't be assessed.

2. **Run the mechanical checks.**
   ```bash
   python3 <this-skill-dir>/scripts/check_skill.py <skill-dir> --format json
   ```
   It reports each check with a rubric ID and a status: `pass`, `warn`, `fail` or `info`. Use the results as they come. Don't recount words or re-measure lengths by hand. If it can't parse the frontmatter, report that as a P1 failure and carry on with what you can read.

3. **Read the whole skill**: SKILL.md, plus every file in `references/`, `scripts/` and `assets/`. Judgment items depend on content, and a skill that is clean in SKILL.md can still hide a 4,000-word reference file or a script that installs packages.

4. **Make the judgment calls.** Open `references/cheatsheet.md` and work through every item marked `judge`. For each one, decide pass / warn / fail and quote the line that decided it. Pay most attention to these, because they're where skills most often go wrong:
   - **D1/D3/D4. The description as a router.** Read it as Claude would when choosing between skills. Does it name concrete triggers? Would it fire on a near-miss it shouldn't take? Would it stay silent on a real request?
   - **R1/Q4. One job.** Try to state what the skill does in one sentence without "and" joining unrelated capabilities.
   - **Q2. Reason, not rule.** For each caps-lock rule the script counted, check whether a "because" comes with it.
   - **Q5. Verifiable.** Pick the two vaguest instructions and ask whether an agent could tell that it followed them.
   - **S3. Three test cases.** Write three: two that should trigger the skill and one near-miss that shouldn't. If you can't, that's the finding. If you can, put them in the report, because the author can reuse them as evals.

5. **Mark what the files can't show.** E3/E4 (regression, token budget), P4/P6/P7/P8 (CI, reviewer, install paths, provisioning), R4 (ownership) and Q1 (was it built from real failures?) can't be decided from files. Mark them `not verifiable`, not failed. Failing a skill for things you couldn't observe makes the report less trustworthy.

6. **Handle the spec conflicts.** `references/cheatsheet.md` ends with places where the cheatsheet disagrees with the Agent Skills spec or Claude Code. Examples: snake_case directories, a top-level `version`, and the 200-character description limit. Report these as conflicts, with the trade-off, not as failures.

7. **Decide the tier.** Under the cheatsheet's rule, the skill is **draft** if any of E1–E4 isn't satisfied. In practice that's almost always true, since E3/E4 need measurement. So give two things: the tier, and a separate **readiness** verdict on what you *could* check: `ready`, `needs work` or `not ready`. Base readiness on the fail-level findings.

8. **Write the report** using `assets/report-template.md`. Save it if the user asked for a file. Otherwise reply with it.

## Examples

**Input:** "assess ~/.claude/skills/pdf-processor"
**Output (excerpt):**
> **Readiness: needs work** · Tier: draft (no trigger evals)
> 1. **D3 fail.** The description has no when-not clause, so it competes with the docx skill on "convert this file". Add: "Do NOT use for Word or Excel files."
> 2. **N3 warn.** Rename to `processing-pdfs`.
> 3. **Q2 warn.** There are 5 caps-lock MUSTs with no reasons. For example, line 34 says "ALWAYS use pdfplumber" without saying why it's preferred over pypdf.

**Input:** the user pastes a 12-line SKILL.md with no folder.
**Output:** a report that marks the F, DD7 and P3 checks "not assessable (text only)" and grades the rest.

## Output format
Fill in `assets/report-template.md`:
- Lead with the verdict and the top three fixes, ordered by impact on whether the skill triggers and works.
- Then give the full per-section table and the drafted test cases.
- Every non-pass finding cites its rubric ID, quotes the evidence (with `file:line` where possible) and proposes a concrete fix: the replacement description text, the new name, the sentence to add.

## Anti-patterns to avoid
- **Box-ticking the template sections.** A missing "Examples" heading is a warn at most. A vague description is the real problem. Spend the report's attention where it changes whether the skill works.
- **Grading from the script alone.** The script can't tell whether a description is good, only whether it's long or missing a "do not use" phrase.
- **Rewriting the skill.** Propose specific fixes, but don't edit the user's skill files unless they ask.
- **Over-trusting heuristics.** The gerund check, the "when not" phrase search and the section-heading detection are heuristics. If the script says `warn` but the content clearly satisfies the rule (e.g. a "Scope" section that lists exclusions), override it and say so.
