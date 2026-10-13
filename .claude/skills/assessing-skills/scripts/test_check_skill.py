"""Unit tests for check_skill.py. Run: python3 -m unittest discover -s scripts"""

import tempfile
import textwrap
import unittest
from pathlib import Path

import check_skill


def make_skill(root, dirname, skill_md, files=None):
    d = Path(root) / dirname
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(textwrap.dedent(skill_md).lstrip())
    for rel, content in (files or {}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return d


def by_id(results, rid):
    return [r for r in results if r["id"] == rid]


GOOD = """
---
name: processing-pdfs
description: |
  Extract text and tables from PDF files. Use when the user asks to read,
  parse or pull data out of a .pdf. Do NOT use for Word or Excel files.
metadata:
  version: 1.2.0
  author: someone
---
# Processing PDFs
## When to use
- reading a pdf
## When NOT to use
- docx
## Workflow
1. Run `scripts/extract.py`.
## Examples
- Input: x -> Output: y
## Output format
- plain text
## Anti-patterns to avoid
- Don't OCR text PDFs.
"""


class FrontmatterTests(unittest.TestCase):
    def test_block_scalar_nested_mapping_and_list(self):
        fm, body, errors = check_skill.parse_frontmatter(textwrap.dedent("""\
            ---
            name: a-b
            description: |
              line one
              line two
            allowed-tools: [Read, Bash]
            metadata:
              author: me
            ---
            body
            """))
        self.assertEqual(errors, [])
        self.assertEqual(fm["description"], "line one\nline two")
        self.assertEqual(fm["allowed-tools"], ["Read", "Bash"])
        self.assertEqual(fm["metadata"], {"author": "me"})
        self.assertEqual(body.strip(), "body")

    def test_quoted_scalar_is_unquoted(self):
        fm, _, _ = check_skill.parse_frontmatter('---\nname: x\ndescription: "Do it: now"\n---\n')
        self.assertEqual(fm["description"], "Do it: now")

    def test_missing_frontmatter_is_an_error(self):
        _, _, errors = check_skill.parse_frontmatter("# no frontmatter\n")
        self.assertTrue(errors)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def statuses(self, d, rid):
        results, _ = check_skill.check(d)
        return [r["status"] for r in by_id(results, rid)]

    def test_good_skill_passes_core_checks(self):
        d = make_skill(self.root, "processing-pdfs", GOOD, {"scripts/extract.py": "print(1)\n"})
        for rid in ("T1", "N2", "N3", "N5", "D3", "S6", "T3", "T4", "T8", "DD10", "P5"):
            self.assertIn("pass", self.statuses(d, rid), rid)

    def test_missing_skill_md(self):
        d = Path(self.root) / "empty"
        d.mkdir()
        self.assertEqual(self.statuses(d, "F1"), ["fail"])

    def test_vendor_prefix_and_generic_name(self):
        d = make_skill(self.root, "claude-utils", GOOD.replace("processing-pdfs", "claude-utils"))
        self.assertEqual(self.statuses(d, "N5"), ["fail"])
        self.assertEqual(self.statuses(d, "N4"), ["warn"])

    def test_filler_description_and_no_when_not(self):
        md = GOOD.replace(
            "Extract text and tables from PDF files. Use when the user asks to read,\n"
            "  parse or pull data out of a .pdf. Do NOT use for Word or Excel files.",
            "A helpful skill for PDFs.")
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "S6"), ["fail"])
        self.assertEqual(self.statuses(d, "D3"), ["fail"])

    def test_use_only_when_counts_as_when_not(self):
        md = GOOD.replace("Do NOT use for Word or Excel files.", "Use only when a .pdf is named.")
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "D3"), ["pass"])

    def test_description_over_200_chars_warns(self):
        desc = "Extract text from PDFs. Do NOT use for Word. " + "x" * (201 - 45)
        self.assertEqual(len(desc), 201)
        md = GOOD.replace(GOOD[GOOD.index("description:"):GOOD.index("metadata:")], f"description: {desc}\n")
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "D5"), ["warn"])

    def test_description_over_1024_chars_fails(self):
        md = GOOD.replace("Do NOT use for Word or Excel files.", "Do NOT use for Word. " + "x" * 1100)
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "D5"), ["fail"])

    def test_description_of_exactly_200_chars_passes(self):
        desc = "Extract text from PDFs. Do NOT use for Word. " + "x" * (200 - 45)
        self.assertEqual(len(desc), 200)
        md = GOOD.replace(GOOD[GOOD.index("description:"):GOOD.index("metadata:")], f"description: {desc}\n")
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "D5"), ["pass"])

    def test_broken_bundled_reference(self):
        d = make_skill(self.root, "processing-pdfs", GOOD)  # scripts/extract.py not created
        results, _ = check_skill.check(d)
        self.assertTrue(any(r["status"] == "fail" and "extract.py" in r["evidence"] for r in by_id(results, "P1")))

    def test_evals_path_reference_is_not_broken(self):
        d = make_skill(self.root, "processing-pdfs", GOOD + "\nSave cases to `evals/evals.json`.\n",
                       {"scripts/extract.py": ""})
        results, _ = check_skill.check(d)
        self.assertFalse(any(r["status"] == "fail" for r in by_id(results, "P1")))

    def test_hard_coded_path_and_secret(self):
        # built by concatenation so this test file doesn't trip the checker when it scans itself
        home_path = "/" + "Users" + "/alice/bin/x"
        fake_key = "API" + '_KEY = "' + "abcdefghijklmnop" + '"\n'
        d = make_skill(self.root, "processing-pdfs", GOOD + "\nRun " + home_path + "\n",
                       {"scripts/extract.py": fake_key})
        self.assertEqual(self.statuses(d, "DD10"), ["fail"])
        self.assertEqual(self.statuses(d, "P5"), ["fail"])

    def test_regex_source_is_not_a_hard_coded_path(self):
        d = make_skill(self.root, "processing-pdfs", GOOD,
                       {"scripts/extract.py": 'PAT = r"/Users/[^\\s]+"\n'})
        self.assertEqual(self.statuses(d, "DD10"), ["pass"])

    def test_trigger_evals_positive_and_negative(self):
        d = make_skill(self.root, "processing-pdfs", GOOD, {
            "scripts/extract.py": "",
            "evals/trigger_evals.json": '[{"query": "a", "should_trigger": true},'
                                        ' {"query": "b", "should_trigger": false}]',
        })
        self.assertEqual(self.statuses(d, "DD7"), ["pass"])
        self.assertEqual(self.statuses(d, "E1"), ["pass"])

    def test_eval_named_tooling_is_not_an_eval_suite(self):
        d = make_skill(self.root, "processing-pdfs", GOOD,
                       {"scripts/extract.py": "", "eval-viewer/generate_review.py": ""})
        self.assertEqual(self.statuses(d, "DD7"), ["fail"])

    def test_claude_code_only_keys_flag_runtime_coupling(self):
        md = GOOD.replace("metadata:", "context: fork\nmetadata:")
        d = make_skill(self.root, "processing-pdfs", md)
        self.assertEqual(self.statuses(d, "R5"), ["warn"])


if __name__ == "__main__":
    unittest.main()
