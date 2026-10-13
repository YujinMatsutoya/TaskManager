# Test plan: Story 2a — task list (read-only) + status filter
Sources: Task_Manager_Spec.md, Development_Backlog.md (Story 2a) · Revision: 1

## Cases
```yaml
- id: TP-001
  level: integration
  title: GET /tasks returns all tasks
  requirement_ref: Spec §Backend endpoints, "GET /tasks — List all tasks"
  preconditions: [three tasks exist with statuses todo, in_progress, done]
  data_needs: [3 tasks, one per status]
  steps: [send GET /tasks]
  expected: 200; response contains all three tasks
  priority: P1
- id: TP-002
  level: unit
  title: TaskList renders one row per task
  requirement_ref: Spec §Frontend screens, "Task list — shows all tasks"
  preconditions: []
  data_needs: [array of 3 task objects]
  steps: [render TaskList with the 3 tasks]
  expected: 3 rows, each showing its task's title
  priority: P2
- id: TP-003
  level: e2e
  title: Selecting "done" in the filter requests GET /tasks?status=done
  requirement_ref: Spec §Backend endpoints, "Optional query param ?status=todo|in_progress|done"
  preconditions: [app running against real backend]
  data_needs: [none]
  steps: [open the page, select "done" in the status filter, capture the network request]
  expected: request URL is /tasks?status=done
  priority: P2
- id: TP-004
  level: e2e
  title: User filters the list by status
  requirement_ref: Backlog Story 2a, "E2E test — load the page, filter by status"
  preconditions: [app running against real backend]
  data_needs: [one task per status, seeded via API]
  steps: [open the page, select "in_progress"]
  expected: only the in_progress task is visible
  priority: P1
```

## Traceability
| Requirement | Cases | Status |
|---|---|---|
| GET /tasks lists all | TP-001 | covered |
| ?status= filter | TP-003, TP-004 | covered |
| Task list screen shows all tasks | TP-002 | covered |

## Gaps
| ID | Requirement | Problem | Question for owner |
|---|---|---|---|

## Out of scope
- Add form, status change, delete, reminder: excluded from Story 2a by the backlog

## Change log
| Rev | Change | Reason / feedback source |
|---|---|---|
| 1 | Initial plan | — |
