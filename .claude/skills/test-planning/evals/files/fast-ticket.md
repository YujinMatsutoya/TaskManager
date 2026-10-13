# TASK-57: Task list with status filter must be fast

Context: Story 2a (task list + status filter) in Development_Backlog.md.

Requirements:
1. `GET /tasks` returns all tasks; `GET /tasks?status=<todo|in_progress|done>` returns only tasks with that status.
2. The task list page shows every task returned, and the status filter dropdown narrows it to the selected status.
3. The task list must be fast, even when a user has lots of tasks.
4. Changing the status filter must also be fast.
