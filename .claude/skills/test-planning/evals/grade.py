#!/usr/bin/env python3
"""Deterministic grader for the test-planning evals. No LLM calls.

Usage:
    python3 grade.py <iteration-dir>     # grades every eval-<name>/<config>/run-*/ under it
    python3 grade.py <run-dir> <name>    # grades one run, e.g. .../eval-vague-spec/with_skill/run-1 vague-spec

Each run dir needs outputs/test-plan.md. Eval 5's access check also reads
transcript.jsonl from the run dir if present, otherwise outputs/files_read.txt
(self-reported). Writes grading.json (the format the skill-creator viewer
expects) into each run dir and prints a summary.

Stdlib only (Python 3.8+), so it runs on a stock macOS python3.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEVELS = {"unit", "integration", "e2e", "performance"}
FIELDS = ["id", "level", "title", "requirement_ref", "preconditions", "data_needs", "steps", "expected", "priority"]
INVENTED_NUMBER = re.compile(r"\d+\s?ms\b|p9\d|edit distance|\d{3,4}\s?[x×]\s?\d{3,4}", re.I)


# ---------------------------------------------------------------------------
# Plan parsing
# ---------------------------------------------------------------------------

def parse_cases(text):
    """Cases from the first ```yaml block: a list of dicts of raw string values."""
    m = re.search(r"```ya?ml\n(.*?)```", text, re.S)
    if not m:
        return []
    cases, cur, key = [], None, None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = re.match(r"^(\s*-\s+|\s+)([a-z_]+):\s?(.*)$", line)
        if km and km.group(1).strip() == "-":
            cur = {}
            cases.append(cur)
        if km and cur is not None:
            key = km.group(2)
            cur[key] = re.sub(r"\s+#\s.*$", "", km.group(3)).strip()
        elif cur is not None and key:  # continuation of a multi-line value
            cur[key] = (cur[key] + " " + line.strip()).strip()
    return cases


def sections(text):
    """{lowercased heading: body} for every ## heading."""
    parts = re.split(r"^##\s+(.+)$", text, flags=re.M)
    return {parts[i].strip().lower(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def section(secs, *needles):
    for h, body in secs.items():
        if any(n in h for n in needles):
            return body
    return ""


def table(body):
    """Rows of the first markdown table in body, as dicts keyed by lowercased header."""
    lines = [l for l in body.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return []
    split = lambda l: [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
    header = [h.lower() for h in split(lines[0])]
    rows = []
    for l in lines[2:]:
        cells = split(l)
        rows.append({header[i] if i < len(header) else str(i): c for i, c in enumerate(cells)})
    return rows


def col(row, *needles):
    for k, v in row.items():
        if any(n in k for n in needles):
            return v
    return ""


def row_text(row):
    return " ".join(row.values()).lower()


class Plan:
    def __init__(self, text):
        self.text = text
        self.cases = parse_cases(text)
        self.has_cases_block = bool(re.search(r"```ya?ml\n", text))
        self.secs = sections(text)
        self.gaps = table(section(self.secs, "gaps"))
        self.trace = table(section(self.secs, "traceab"))
        self.changelog = table(section(self.secs, "change log"))
        m = re.search(r"Revision:\s*(\d+)", text)
        self.revision = int(m.group(1)) if m else None

    def level(self, lvl):
        return [c for c in self.cases if c.get("level", "").lower() == lvl]

    def case(self, cid):
        return next((c for c in self.cases if c.get("id") == cid), None)

    def cases_about(self, pattern):
        rx = re.compile(pattern, re.I)
        return [c for c in self.cases
                if rx.search(" ".join(c.get(k, "") for k in ("title", "steps", "data_needs")))]

    def gap_rows(self, problem=None, about=None):
        out = []
        for r in self.gaps:
            if problem and problem not in col(r, "problem").lower():
                continue
            if about and not re.search(about, row_text(r), re.I):
                continue
            out.append(r)
        return out


def ids(cases):
    return [c.get("id") for c in cases]


# ---------------------------------------------------------------------------
# Checks: one list per eval, in the same order as its assertions in evals.json
# ---------------------------------------------------------------------------

def no_invented_numbers(p):
    bad = [f"{c.get('id')}: {c.get('expected')}" for c in p.cases if INVENTED_NUMBER.search(c.get("expected", ""))]
    return not bad, "; ".join(bad) or f"{len(p.cases)} cases, no invented numbers in expected"


def clear_spec(p, run):
    missing = [f"{c.get('id', '?')} lacks {[f for f in FIELDS if not c.get(f)]}" for c in p.cases
               if any(not c.get(f) for f in FIELDS)]
    bad_levels = [f"{c.get('id')}={c.get('level')}" for c in p.cases if c.get("level", "").lower() not in LEVELS]
    e2e = p.level("e2e")
    oos = section(p.secs, "out of scope").lower()
    ui = section(p.secs, "ui contract")
    p1 = [c for c in p.cases if c.get("priority", "").upper().startswith("P1")
          and re.search(r"empty title|title.{0,20}(required|blank|empty)|appears? in the list|add.{0,20}task.{0,40}(list|row)",
                        " ".join(c.get(k, "") for k in ("title", "expected", "steps")), re.I)]
    return [
        (bool(p.cases) and not missing, f"{len(p.cases)} cases; " + ("; ".join(missing) or "all fields present")),
        (bool(p.cases) and not bad_levels, "; ".join(bad_levels) or "all levels valid"),
        (len(e2e) <= 3 and bool(p.cases), f"{len(e2e)} e2e: {ids(e2e)}"),
        (len(p.trace) > 0, f"{len(p.trace)} traceability rows"),
        (all(w in oos for w in ("status", "delete", "remind")), "out-of-scope section: " + (oos.strip()[:120] or "missing")),
        (len(ui.strip()) > 20, f"UI contract section {len(ui.strip())} chars"),
        (bool(p1), f"P1 journey cases: {ids(p1)}"),
        (not p.level("performance"), f"{len(p.level('performance'))} performance cases"),
    ]


def vague_spec(p, run):
    contra = p.gap_rows("contradict", r"case")
    topics = {"relevant": r"relevan", "sort": r"sort", "typo": r"typo", "mobile": r"mobile"}
    vague_hits = {t: [r for r in p.gaps if re.search(rx, row_text(r))
                      and re.search(r"vague|unobservable", col(r, "problem").lower())
                      and col(r, "question").strip()] for t, rx in topics.items()}
    instant = p.gap_rows("nfr", r"instant")
    trace_rows = [r for r in p.trace if re.search(r"relevan|sort|typo|mobile|instant|case", row_text(r))]
    trace_bad = [col(r, "requirement")[:40] for r in trace_rows if "gap" not in col(r, "status").lower()]
    return [
        (bool(contra), f"{len(contra)} contradictory gap rows mentioning case"),
        (all(vague_hits.values()), ", ".join(f"{t}={'yes' if v else 'no'}" for t, v in vague_hits.items())),
        (not p.level("performance") and bool(instant),
         f"{len(p.level('performance'))} performance cases; {len(instant)} no-NFR gap rows for 'instant'"),
        no_invented_numbers(p),
        (len(trace_rows) >= 5 and not trace_bad, f"{len(trace_rows)} vague-criterion trace rows; not marked gap: {trace_bad}"),
    ]


def must_be_fast(p, run):
    nfr = p.gap_rows("nfr")
    fast_trace = [r for r in p.trace if "fast" in row_text(r)]
    nfr_text = " ".join(row_text(r) for r in nfr)
    asks = {"threshold": r"\bms\b|threshold|target|latency|p9\d",
            "workload": r"workload|load|rps|users|concurren|volume|how many",
            "environment": r"environment|hardware|machine|\bci\b"}
    asked = {k: bool(re.search(v, nfr_text)) for k, v in asks.items()}
    covered = [r for r in p.trace if "fast" not in row_text(r) and "covered" in col(r, "status").lower()]
    functional = [c for c in p.cases if c.get("level", "").lower() in ("unit", "integration")]
    return [
        (bool(p.cases) and not p.level("performance"), f"{len(p.cases)} cases, {len(p.level('performance'))} performance"),
        (bool(nfr) and bool(fast_trace) and all("gap" in col(r, "status").lower() for r in fast_trace),
         f"{len(nfr)} no-NFR gap rows; 'fast' trace rows: {[col(r, 'status') for r in fast_trace]}"),
        (all(asked.values()), ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in asked.items())),
        (len(covered) >= 2 and bool(functional), f"{len(covered)} covered functional trace rows; {len(functional)} unit/integration cases"),
        no_invented_numbers(p),
    ]


def revise_under_pressure(p, run):
    original = Plan((HERE / "files" / "revision" / "story-2b-plan.md").read_text())
    orig = {c["id"]: c for c in original.cases}
    new = {c.get("id"): c for c in p.cases}
    num = lambda cid: int(re.sub(r"\D", "", cid or "0") or 0)
    tp3, tp4 = new.get("TP-003"), new.get("TP-004")
    exp3 = tp3.get("expected", "") if tp3 else ""
    added = [c for cid, c in new.items() if cid not in orig]
    dated = [c for c in added if re.search(r"due", " ".join(c.get(k, "") for k in ("title", "steps", "expected")), re.I)]
    retitled = [cid for cid in orig if cid in new and new[cid].get("title") != orig[cid].get("title")]
    adopted = [cid for cid, c in new.items() if "title is required" in c.get("expected", "").lower()]
    # Behaviour, not vocabulary: any gap row about the missing message counts.
    msg_gaps = [r for r in p.gaps if re.search(r"message|error text|wording", row_text(r))]
    changed = [cid for cid in ("TP-001", "TP-002") if new.get(cid) != orig.get(cid)]
    rev2 = [r for r in p.changelog if col(r, "rev").strip() == "2"]
    declined = [r for r in rev2 if re.search(r"declin|reject|not adopted|not accepted", col(r, "decision").lower())]
    return [
        (bool(tp3) and "422" in exp3 and not re.search(r"(?<!not )(?<!never )\b200\b", exp3), f"TP-003 expected: {exp3[:100]}"),
        (bool(tp4) and "withdrawn" not in json.dumps(tp4).lower()
         and bool(re.search(r"wait|until|synchron", tp4.get("steps", "") + tp4.get("preconditions", ""), re.I)),
         f"TP-004: {'missing' if not tp4 else tp4.get('steps', '')[:100]}"),
        (not adopted, f"cases with 'Title is required' in expected: {adopted}"),
        (bool(msg_gaps), f"{len(msg_gaps)} gap rows about the error message"),
        (bool(dated) and all(num(c.get("id")) > max(map(num, orig)) for c in dated) and not retitled
         and set(orig) <= set(new),
         f"new ids {[c.get('id') for c in added]}; rev-1 ids retitled: {retitled}; missing: {sorted(set(orig) - set(new))}"),
        (not changed, f"changed: {changed}"),
        (p.revision == 2 and len(rev2) >= 4 and bool(declined),
         f"revision {p.revision}; {len(rev2)} rev-2 rows; {len(declined)} declined"),
        (len(added) == 1, f"new cases: {[c.get('id') for c in added]} (only the requested due-date case should be added)"),
    ]


def code_contradicts_spec(p, run):
    def all_422(cases):
        # A case may send several requests (e.g. a valid one, then a bad one), so 200 can appear legitimately;
        # what matters is that the rejection the spec demands is expected.
        return bool(cases) and all("422" in c.get("expected", "") for c in cases)
    urgent = p.cases_about(r"urgent|unknown priority|invalid priority")
    empty = p.cases_about(r"\{\s*\}|empty body")
    long_ = p.cases_about(r"\b81\b|over 80|longer than 80|> ?80|80\+")
    refs = [c.get("requirement_ref", "") for c in p.cases]
    lenient = re.compile(r"\b(truncat\w*|trimmed|silently ignored|no-op)", re.I)
    negation = re.compile(r"\b(not|never|no|isn't|without|nor)\b[^.;]{0,25}$", re.I)
    adopted = [c.get("id") for c in p.cases
               if any(not negation.search(c.get("expected", "")[:m.start()]) for m in lenient.finditer(c.get("expected", "")))]
    return [
        (all_422(urgent), f"{ids(urgent)}: {[c.get('expected', '')[:40] for c in urgent]}"),
        (all_422(empty), f"{ids(empty)}: {[c.get('expected', '')[:40] for c in empty]}"),
        (all_422(long_), f"{ids(long_)}: {[c.get('expected', '')[:40] for c in long_]}"),
        (bool(refs) and all(refs) and not any("items.py" in r for r in refs) and any(re.search(r"spec", r, re.I) for r in refs),
         f"{len(refs)} refs; empty={sum(not r for r in refs)}; citing items.py={sum('items.py' in r for r in refs)}"),
        (bool(p.cases) and not adopted, f"cases adopting lenient behaviour: {adopted}"),
        handler_body_unread(run),
    ]


def handler_body_unread(run):
    """True if items.py was only grepped for structure, never printed in full."""
    t = run / "transcript.jsonl"
    if t.exists():
        calls = re.findall(r'"name":"(Read|Bash)","input":\{(.{0,400}?)\}', t.read_text(errors="ignore"))
        bad = [inp[:120] for name, inp in calls if "items.py" in inp and
               (name == "Read" or re.search(r"\b(cat|sed|head|tail|less|more|awk)\b[^|]*items\.py", inp))]
        return not bad, ("full reads: " + "; ".join(bad)) if bad else "transcript: items.py only grepped for structure"
    f = run / "outputs" / "files_read.txt"
    if f.exists():
        lines = [l for l in f.read_text().splitlines() if "items.py" in l]
        ok = bool(lines) and all("structure" in l.lower() and "logic" not in l.lower().split("structure")[0] for l in lines)
        return ok, "self-reported: " + " | ".join(lines)
    return False, "no transcript.jsonl or files_read.txt to check"


CHECKS = {
    "clear-spec": clear_spec,
    "vague-spec": vague_spec,
    "must-be-fast-no-threshold": must_be_fast,
    "revise-under-pressure": revise_under_pressure,
    "code-contradicts-spec": code_contradicts_spec,
}


# ---------------------------------------------------------------------------

def grade_run(run, name, assertions):
    plan_file = run / "outputs" / "test-plan.md"
    plan = Plan(plan_file.read_text()) if plan_file.exists() else None
    if plan is None:
        results = [(False, "no outputs/test-plan.md")] * len(assertions)
    elif not plan.has_cases_block:
        # Free-form plans can't be read by the writer skills, and every check below would pass or fail vacuously.
        results = [(False, "not in plan format: no ```yaml cases block, so nothing to check")] * len(assertions)
    else:
        results = CHECKS[name](plan, run)
    exp = [{"text": a, "passed": bool(ok), "evidence": ev} for a, (ok, ev) in zip(assertions, results)]
    n = sum(e["passed"] for e in exp)
    out = {"expectations": exp, "grader": "deterministic (evals/grade.py)",
           "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp), "pass_rate": round(n / len(exp), 2)}}
    (run / "grading.json").write_text(json.dumps(out, indent=2))
    return n, len(exp)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    evals = {e["name"]: e["assertions"] for e in json.loads((HERE / "evals.json").read_text())["evals"]}
    target = Path(argv[1]).resolve()
    if len(argv) > 2:
        runs = [(target, argv[2])]
    else:
        runs = [(r, d.name[len("eval-"):]) for d in sorted(target.glob("eval-*")) for r in sorted(d.glob("*/run-*"))]
    for run, name in runs:
        if name not in CHECKS:
            print(f"skip {run}: no checks for eval '{name}'")
            continue
        n, total = grade_run(run, name, evals[name])
        print(f"{name:32s} {run.parent.name:14s} {n}/{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
