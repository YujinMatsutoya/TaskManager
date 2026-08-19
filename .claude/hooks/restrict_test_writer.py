#!/usr/bin/env python3
"""PreToolUse hook: confines the test-writer subagent to backend/tests/.

Blocks Write/Edit calls from the test-writer subagent that target any
path outside backend/tests/. Other agents (including the main session)
are left untouched by this hook.
"""
import json
import os
import sys


def main() -> None:
    data = json.loads(sys.stdin.read())

    if data.get("agent_type") != "test-writer":
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    cwd = data.get("cwd", "")

    if not file_path:
        sys.exit(0)

    allowed_dir = os.path.realpath(os.path.join(cwd, "backend", "tests"))
    target = file_path if os.path.isabs(file_path) else os.path.join(cwd, file_path)
    target = os.path.realpath(target)

    if target == allowed_dir or target.startswith(allowed_dir + os.sep):
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"test-writer may only write files under backend/tests/ "
                f"(blocked path: {file_path})"
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
