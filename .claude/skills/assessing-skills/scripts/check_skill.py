#!/usr/bin/env python3
"""Mechanical checks of a skill folder against the Agent Skills cheatsheet.

Usage:
    python3 check_skill.py <path-to-skill-dir-or-SKILL.md> [--format json|md]

Covers only what can be decided from the files. Judgment items (one job,
reason-not-rule, verifiable instructions, ...) are left to the assessor.
Each result carries the rubric ID from references/cheatsheet.md.

Stdlib only, Python 3.8+ (no PyYAML), so it runs on a stock macOS python3.
"""

import json
import re
import sys
from pathlib import Path

GENERIC_NAMES = {"helper", "helpers", "utils", "util", "tools", "tool", "data", "misc", "common"}
VENDOR_PREFIXES = ("claude-", "gemini-", "anthropic-", "openai-", "gpt-")
CLAUDE_CODE_ONLY_KEYS = {
    "context", "agent", "hooks", "disable-model-invocation", "user-invocable",
    "argument-hint", "model", "when_to_use", "paths", "shell",
}
KNOWN_KEYS = {"name", "description", "version", "license", "allowed-tools", "metadata", "compatibility"}
WHEN_NOT_PATTERNS = [
    r"\bdo not use\b", r"\bdon'?t use\b", r"\bnot for\b", r"\bnot use (this|it) (for|when)\b",
    r"\bavoid using\b", r"\bnot intended for\b", r"\bskip (this|it) (for|when)\b",
    r"\buse (this skill )?only (when|if|for)\b", r"\bis not (by itself )?a request\b", r"\bnot (a|an) .{0,40}\b(task|request)\b",
]
VAGUE_DESC_PATTERNS = [r"^\s*(a|an)\s+helpful\s+skill", r"^\s*this\s+skill\s+helps", r"^\s*helps\s+with\b"]
SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9_-]{20,}", "API key-like token (sk-...)"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"ghp_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", "hard-coded credential assignment"),
]
ABS_PATH_PATTERN = r"(?<![\w$}])(/(?:Users|home)/[\w.-]+(?:/[\w.-]+)*|[A-Z]:\\\\[\w.-]+(?:\\\\[\w.-]+)*)"
TEXT_SUFFIXES = {".md", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml", ".txt", ".toml"}


# ---------------------------------------------------------------------------
# Minimal frontmatter parser (enough for SKILL.md; not a general YAML parser)
# ---------------------------------------------------------------------------

def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return v


def parse_frontmatter(text):
    """Return (frontmatter dict, body str, errors list)."""
    errors = []
    if not text.startswith("---"):
        return {}, text, ["SKILL.md does not start with a '---' frontmatter block"]
    lines = text.splitlines()
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text, ["frontmatter block is never closed with '---'"]
    fm_lines, body = lines[1:end], "\n".join(lines[end + 1:])

    data, i = {}, 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0] in " \t":
            errors.append(f"unexpected indented line in frontmatter: {line.strip()!r}")
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            errors.append(f"unparseable frontmatter line: {line!r}")
            i += 1
            continue
        key, rest = m.group(1), m.group(2).strip()
        if key in data:
            errors.append(f"duplicate key: {key}")
        i += 1
        # collect indented continuation lines
        block = []
        while i < len(fm_lines) and (not fm_lines[i].strip() or fm_lines[i][0] in " \t"):
            block.append(fm_lines[i])
            i += 1
        while block and not block[-1].strip():
            block.pop()
        if rest in ("|", "|-", "|+", ">", ">-", ">+"):
            stripped = [b.strip() for b in block]
            data[key] = ("\n" if rest.startswith("|") else " ").join(stripped).strip()
        elif rest.startswith("[") and rest.endswith("]"):
            data[key] = [_unquote(x) for x in rest[1:-1].split(",") if x.strip()]
        elif rest == "" and block:
            items = [b.strip() for b in block if b.strip()]
            if all(x.startswith("- ") for x in items):
                data[key] = [_unquote(x[2:]) for x in items]
            else:
                sub = {}
                for x in items:
                    sm = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", x)
                    if sm:
                        sub[sm.group(1)] = _unquote(sm.group(2))
                    else:
                        errors.append(f"unparseable nested line under {key}: {x!r}")
                data[key] = sub
        else:
            # plain scalar, possibly folded over continuation lines
            parts = [rest] + [b.strip() for b in block]
            data[key] = _unquote(" ".join(p for p in parts if p))
    return data, body, errors


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check(skill_dir):
    results = []

    def add(rid, status, message, evidence=""):
        results.append({"id": rid, "status": status, "message": message, "evidence": evidence})

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        add("F1", "fail", "SKILL.md not found", str(skill_md))
        return results, {}
    add("F1", "pass", "SKILL.md exists")

    text = skill_md.read_text(encoding="utf-8")
    fm, body, fm_errors = parse_frontmatter(text)

    # P1 / T1 / T2: frontmatter validity
    add("P1", "fail" if fm_errors else "pass",
        "frontmatter has problems" if fm_errors else "frontmatter parses",
        "; ".join(fm_errors))
    name, desc = fm.get("name"), fm.get("description")
    missing = [k for k in ("name", "description") if not fm.get(k)]
    add("T1", "fail" if missing else "pass",
        f"missing required field(s): {', '.join(missing)}" if missing else "name and description present")
    meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    version = fm.get("version") or meta.get("version")
    if version and not re.match(r"^\d+\.\d+\.\d+", str(version)):
        add("T2", "warn", "version is not semver", str(version))
    cc_keys = sorted(set(fm) & CLAUDE_CODE_ONLY_KEYS)
    unknown = sorted(set(fm) - KNOWN_KEYS - CLAUDE_CODE_ONLY_KEYS)
    add("T2", "info", "optional fields present",
        f"version={version!r}, license={fm.get('license')!r}, allowed-tools={fm.get('allowed-tools')!r}, "
        f"author={meta.get('author')!r}" + (f"; unknown keys: {unknown}" if unknown else ""))
    if "version" in fm:
        add("T2", "info", "top-level `version` is a cheatsheet field; the Agent Skills spec puts it under metadata.version (conflict, not a failure)")
    add("R5", "warn" if cc_keys else "pass",
        "Claude Code-only frontmatter ties the skill to one runtime" if cc_keys else "no runtime-specific frontmatter keys",
        ", ".join(cc_keys))

    # N: naming
    dir_name = skill_dir.name
    if name:
        add("N2", "pass" if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) else "fail",
            "name is kebab-case" if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) else "name is not kebab-case", name)
        add("N3", "pass" if re.search(r"(^|-)[a-z]+ing(-|$)", name) else "warn",
            "name uses a gerund" if re.search(r"(^|-)[a-z]+ing(-|$)", name) else "name has no gerund (e.g. processing-pdfs)", name)
        generic = [p for p in name.split("-") if p in GENERIC_NAMES]
        add("N4", "warn" if generic else "pass",
            f"generic word(s) in name: {generic}" if generic else "no generic words in name", name)
        vendor = name.startswith(VENDOR_PREFIXES)
        add("N5", "fail" if vendor else "pass", "vendor prefix in name" if vendor else "no vendor prefix", name)
        if dir_name != name:
            add("N1", "warn" if dir_name.replace("_", "-") == name else "fail",
                "directory name differs from skill name", f"dir={dir_name!r} name={name!r}")
    snake = bool(re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", dir_name)) and "_" in dir_name
    add("N1", "info",
        "directory is snake_case (cheatsheet style; Agent Skills spec expects dir == kebab-case name)" if snake
        else "directory is not snake_case (cheatsheet N1); acceptable if it matches the kebab-case name per the Agent Skills spec",
        dir_name)

    # D: description
    if desc:
        chars, words = len(desc), len(desc.split())
        add("D5", "fail" if chars > 1024 else ("warn" if chars > 200 else "pass"),
            f"{chars} chars, {words} words (limits: <=1024 YAML hard, <=200 API, ~50 words target)",
            desc[:120] + ("..." if chars > 120 else ""))
        first = re.findall(r"[A-Za-z']+", desc)[:3]
        add("D2", "info", "first words of description (should be a verb / trigger keyword)", " ".join(first))
        vague = any(re.search(p, desc, re.I) for p in VAGUE_DESC_PATTERNS)
        add("S6", "fail" if vague else "pass",
            "description opens with 'a helpful skill' / 'this skill helps'" if vague else "description doesn't open with filler")
        when_not = [p for p in WHEN_NOT_PATTERNS if re.search(p, desc, re.I)]
        add("D3", "pass" if when_not else "fail",
            "description has a when-NOT-to-use clause" if when_not else "no when-NOT-to-use clause found in description")

    # Body structure (T3–T8). Strip fenced code first so `# comment` lines aren't read as headings.
    prose = re.sub(r"^(```|~~~).*?^\1[^\n]*$", "", body, flags=re.M | re.S)
    headings = [h.strip().lower() for h in re.findall(r"^#{1,6}\s+(.+)$", prose, re.M)]

    def has(*needles):
        return any(any(n in h for n in needles) for h in headings)

    for rid, label, needles in [
        ("T3", "When to use", ("when to use",)),
        ("T4", "When NOT to use", ("when not to use", "when not", "out of scope", "not for")),
        ("T5", "Workflow", ("workflow", "steps", "process", "procedure")),
        ("T6", "Examples", ("example",)),
        ("T7", "Output format", ("output", "report", "format")),
        ("T8", "Anti-patterns", ("anti-pattern", "antipattern", "avoid", "don't", "do not", "pitfall", "gotcha")),
    ]:
        add(rid, "pass" if has(*needles) else "warn",
            f"'{label}' section {'found' if has(*needles) else 'not found'}")

    # Size, tone
    body_words = len(re.findall(r"\S+", body))
    add("S1", "fail" if body_words > 5000 else ("warn" if body_words > 3000 else "pass"),
        f"SKILL.md body is {body_words} words (smell above 5,000)")
    caps = re.findall(r"\b(ALWAYS|NEVER|MUST|MUST NOT|CRITICAL|IMPORTANT)\b", prose)
    add("Q2", "warn" if len(caps) >= 3 else "pass",
        f"{len(caps)} caps-lock imperatives (ALWAYS/NEVER/MUST/...) — check each has a reason",
        ", ".join(sorted(set(caps))))
    edge = [h for h in headings if "edge case" in h]
    add("S5", "warn" if len(edge) >= 2 else "pass", f"{len(edge)} 'edge case' headings", "; ".join(edge))

    # Folder use, references, progressive disclosure
    subdirs = {d: (skill_dir / d).is_dir() for d in ("scripts", "references", "assets")}
    add("F2", "info", "optional dirs present", ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in subdirs.items()))
    refs = sorted(set(re.findall(r"(?<![\w.-])((?:scripts|references|assets|evals)/[\w./-]+)", body)))
    refs = [r.rstrip(".,:;)") for r in refs]
    # evals/ paths are often outputs the skill tells the agent to create, so only bundled dirs count as broken
    broken = [r for r in refs if not r.startswith("evals/") and not (skill_dir / r).exists()]
    if broken:
        add("P1", "fail", "body references files that don't exist", ", ".join(broken))

    other_files = [p for p in skill_dir.rglob("*") if p.is_file() and p.name != "SKILL.md"
                   and "__pycache__" not in p.parts and not p.name.startswith(".")]
    bundled = [p for p in other_files
               if not re.match(r"(test_|__init__|LICENSE)", p.name) and "evals" not in p.relative_to(skill_dir).parts]

    def mentioned(p, text):
        rel = str(p.relative_to(skill_dir))
        module = rel.rsplit(".", 1)[0].replace("/", ".")  # `python -m scripts.foo`
        stem_path = rel.rsplit(".", 1)[0]  # `python scripts/foo <args>` without the extension
        if p.suffix in (".py", ".sh", ".js") and (module in text or re.search(re.escape(stem_path) + r"(?![\w-])", text)):
            return True
        return rel in text or re.search(r"(?<![\w.-])" + re.escape(p.name) + r"(?![\w-])", text) is not None

    in_body = [p for p in bundled if mentioned(p, body)]
    add("S4", "pass" if in_body else "warn",
        f"SKILL.md references {len(in_body)} bundled file(s)" if in_body else "SKILL.md references no bundled resources",
        ", ".join(sorted(str(p.relative_to(skill_dir)) for p in in_body)))
    all_md = body + "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in other_files if p.suffix == ".md")
    orphans = [str(p.relative_to(skill_dir)) for p in bundled if not mentioned(p, all_md)]
    if orphans:
        add("DD3", "warn", "bundled files not mentioned in SKILL.md or any bundled .md (the agent won't know they exist)",
            ", ".join(sorted(orphans)))

    # Tests and evals (R3 / DD7 / E1 / E2 / P3)
    eval_files = [p for p in skill_dir.rglob("*") if p.is_file() and (
        "evals" in p.relative_to(skill_dir).parts[:-1]
        or re.fullmatch(r".*evals?(_set|-set)?\.(json|ya?ml|jsonl)", p.name.lower()))]
    trigger = []
    for p in eval_files:
        if p.suffix == ".json":
            try:
                txt = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if "should_trigger" in txt:
                trigger.append(p)
    add("DD7", "pass" if eval_files else "fail",
        f"{len(eval_files)} eval file(s) found" if eval_files else "no eval files (a skill without a test is a hope)",
        ", ".join(str(p.relative_to(skill_dir)) for p in eval_files[:5]))
    if trigger:
        has_pos = has_neg = False
        for p in trigger:
            try:
                items = json.loads(p.read_text(encoding="utf-8"))
                items = items if isinstance(items, list) else items.get("queries", [])
                has_pos |= any(i.get("should_trigger") is True for i in items)
                has_neg |= any(i.get("should_trigger") is False for i in items)
            except Exception:
                pass
        add("E1", "pass" if has_pos and has_neg else "warn",
            f"trigger evals: positive={'yes' if has_pos else 'no'}, negative={'yes' if has_neg else 'no'} (accuracy must be measured separately)")
    else:
        add("E1", "fail", "no trigger evals (positive + negative should_trigger cases) found")
    scripts = [p for p in (skill_dir / "scripts").rglob("*") if p.is_file()] if subdirs["scripts"] else []
    code_scripts = [p for p in scripts if p.suffix in (".py", ".sh", ".js", ".ts") and not p.name.startswith("test")]
    script_tests = [p for p in skill_dir.rglob("*") if p.is_file() and re.match(r"(test_.*|.*_test|.*\.test)\.(py|js|ts|sh)$", p.name)]
    if code_scripts:
        add("P3", "pass" if script_tests else "fail",
            f"{len(code_scripts)} script(s), {len(script_tests)} test file(s)",
            ", ".join(str(p.relative_to(skill_dir)) for p in script_tests))

    # Security: hard-coded paths and secrets (DD10 / P5)
    path_hits, secret_hits = [], []
    for p in [skill_md] + other_files:
        if p.suffix not in TEXT_SUFFIXES:
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        rel = str(p.relative_to(skill_dir))
        for n, line in enumerate(lines, 1):
            for m in re.finditer(ABS_PATH_PATTERN, line):
                path_hits.append(f"{rel}:{n}: {m.group(0)}")
            for pat, label in SECRET_PATTERNS:
                if re.search(pat, line):
                    secret_hits.append(f"{rel}:{n}: {label}")
    add("DD10", "fail" if path_hits else "pass",
        f"{len(path_hits)} hard-coded absolute path(s)" if path_hits else "no hard-coded absolute paths",
        "; ".join(path_hits[:8]))
    add("P5", "fail" if secret_hits else "pass",
        f"{len(secret_hits)} possible secret(s)" if secret_hits else "no secret-like strings",
        "; ".join(secret_hits[:8]))
    installs = re.findall(r"(pip install [^\n`]+|npm (?:i|install) [^\n`]+|curl [^\n`]*\|\s*(?:ba)?sh)", body)
    if installs:
        add("DD12", "warn", "body installs third-party packages — check they're trusted/pinned", "; ".join(installs[:5]))

    summary = {
        "skill_dir": str(skill_dir),
        "name": name,
        "description_chars": len(desc) if desc else 0,
        "body_words": body_words,
        "counts": {s: sum(r["status"] == s for r in results) for s in ("pass", "warn", "fail", "info")},
    }
    return results, summary


def to_markdown(results, summary):
    icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "info": "INFO"}
    title = summary.get("name") or summary.get("skill_dir") or "(no SKILL.md)"
    counts = {s: sum(r["status"] == s for r in results) for s in ("pass", "warn", "fail", "info")}
    out = [f"# Mechanical checks: {title}", "", f"Counts: {counts}", "", "| ID | Status | Check | Evidence |", "|---|---|---|---|"]
    for r in results:
        ev = r["evidence"].replace("|", "\\|").replace("\n", " ")
        out.append(f"| {r['id']} | {icon[r['status']]} | {r['message']} | {ev} |")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    target = Path(argv[1]).expanduser().resolve()
    skill_dir = target.parent if target.name == "SKILL.md" else target
    fmt = "json"
    if "--format" in argv:
        fmt = argv[argv.index("--format") + 1]
    results, summary = check(skill_dir)
    if fmt == "md":
        print(to_markdown(results, summary))
    else:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
