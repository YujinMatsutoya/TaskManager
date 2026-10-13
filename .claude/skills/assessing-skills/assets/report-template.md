# Skill assessment: `<skill-name>`

**Readiness:** ready | needs work | not ready  ·  **Tier:** draft | evaluated
<one sentence on why>

Assessed against the Agent Skills Practical Cheatsheet (May 2026) · path: `<skill-dir>`
<!-- Mention it here if only pasted text was available. -->

## Top fixes
1. **<ID> <status>.** <problem, with a quoted evidence line> → <concrete fix: replacement text, new name, or sentence to add>
2. ...
3. ...

## Description (the router)
> <current description>

- Chars / words: <n> / <n> (warn over 200, fail over 1024)
- What / when / when-not: <yes/no each>
- Likely false triggers: <near-miss requests that would wrongly fire it>
- Likely misses: <real requests it would fail to catch>
- **Suggested rewrite:** <full replacement description, if any>

## Findings by section
| Section | ID | Status | Evidence | Fix |
|---|---|---|---|---|
| Naming | N2 | pass | `name: foo-bar` | — |
| ... | | | | |

Status values: pass, warn, fail, conflict (the cheatsheet disagrees with the spec), not verifiable.

## Three test cases (S3)
| # | Prompt | Should trigger? | Why |
|---|---|---|---|
| 1 | | yes | |
| 2 | | yes | |
| 3 | | no (near-miss) | |

## Not verifiable from files
<E3, E4, P4, P6, P7, P8, R4, Q1: one line each on how the author could check it>

## Spec conflicts
<only if any apply: N1 snake_case dir, top-level version, 200-char limit, Claude Code-only keys>
