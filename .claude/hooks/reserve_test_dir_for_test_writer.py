#!/usr/bin/env python3
"""PreToolUse hook: reserves backend/tests/ and frontend/tests/ for the
test-writer subagent.

Blocks Write/Edit calls from any agent OTHER than test-writer (including
the main Claude Code session) that target a path inside either directory.
Pair with restrict_test_writer.py for full two-way enforcement: that hook
confines test-writer TO these directories, this one reserves them FOR
test-writer only.
"""
import json
import os
import sys

RESTRICTED_SUBDIRS = [("backend", "tests"), ("frontend", "tests")]


def main() -> None:
    data = json.loads(sys.stdin.read())

    if data.get("agent_type") == "test-writer":
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    cwd = data.get("cwd", "")

    if not file_path:
        sys.exit(0)

    target = file_path if os.path.isabs(file_path) else os.path.join(cwd, file_path)
    target = os.path.realpath(target)

    restricted_dirs = [os.path.realpath(os.path.join(cwd, *parts)) for parts in RESTRICTED_SUBDIRS]

    if not any(target == d or target.startswith(d + os.sep) for d in restricted_dirs):
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Only the test-writer subagent may write files under "
                f"backend/tests/ or frontend/tests/ (blocked path: {file_path})"
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
