# Project rules
- This is a frozen-scope practice app. Do not add features beyond the
  spec in Task_Manager_Spec.md without being explicitly asked.
- Automated tests may only be written by the dedicated `test-writer`
  subagent (see .claude/agents/test-writer.md). The main session must
  NEVER write or suggest automated tests, test files, or CI test steps
  itself — delegate all test-writing tasks to the test-writer subagent
  instead.