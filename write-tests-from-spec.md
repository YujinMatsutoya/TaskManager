**Skill: `write-tests-from-spec`**

- **Purpose:** Write tests from specs and reference docs only, without seeing application code, so tests check requirements rather than mirroring the implementation.
- **How you use it:** Start a fresh session, invoke the skill, and it works only from `docs/` and `refs/`.
- **Structure:** A `SKILL.md` with the instructions and a `scripts/restrict-reads.sh` hook script alongside it.
- **Enforcement:** A PreToolUse hook in the skill's frontmatter blocks Read, Grep and Glob outside the allowed folders. It defaults to deny, and `ALLOWED_DIRS` overrides the folders per project.
- **Fresh-context check (possible):** A soft check in `SKILL.md` tells it to stop and ask for a new session if the conversation already has prior history. It's instruction-based, so not guaranteed. A hard version would have the hook read `transcript_path` and block if earlier turns exist, but that depends on an unstable transcript format and only fires on the first tool call. Start with the soft check.
- **Invocation control (possible):** `disable-model-invocation` would keep it from auto-triggering mid-conversation. `context: fork` might give a fresh context automatically, but it reintroduces the brief as a leak point.
- **Ambiguity rule:** If a requirement is unclear, it lists questions instead of guessing from the code.
- **Known gap:** Bash can bypass the hook, so leave Bash out of that session or extend the hook to cover it.
- **Portability path:** Build it in one repo's `.claude/skills/`, then move the whole folder into a plugin unchanged. You may only need to swap the path variable.
- **To verify in the docs:** Skill-scoped `hooks` frontmatter, the `${CLAUDE_SKILL_DIR}` variable name, `disable-model-invocation`, `context: fork`, and what the hook input JSON contains.