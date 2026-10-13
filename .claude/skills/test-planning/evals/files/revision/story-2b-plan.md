# Test plan: Story 2b — add task form
Sources: Task_Manager_Spec.md, Development_Backlog.md (Story 2b) · Revision: 1

## Cases
```yaml
- id: TP-001
  level: unit
  title: Title plus due date is submitted with both values
  requirement_ref: Spec §Frontend screens, "Add task form — title + optional due date, submits to POST /tasks"
  preconditions: [add-task form rendered with the create-task API function stubbed]
  data_needs: [title "Buy milk", due date 2026-03-01]
  steps: [type the title, pick the due date, submit]
  expected: create-task function called once with title "Buy milk" and due_date "2026-03-01"
  priority: P2
- id: TP-002
  level: unit
  title: The form never sends a status
  requirement_ref: Spec §POST /tasks, "status — not accepted in the request body at all"
  preconditions: [add-task form rendered with the create-task API function stubbed]
  data_needs: [title "Buy milk"]
  steps: [type the title, submit]
  expected: the payload passed to the create-task function has no status key
  priority: P2
- id: TP-003
  level: integration
  title: POST /tasks with an empty title is rejected
  requirement_ref: Spec §POST /tasks, "title — required. No task can exist without one."
  preconditions: [backend running against an empty test database]
  data_needs: [body {"title": ""}]
  steps: [send POST /tasks with {"title": ""}, then GET /tasks]
  expected: 422; GET /tasks still returns an empty list
  priority: P1
- id: TP-004
  level: e2e
  title: User adds a task and sees it in the list
  requirement_ref: Backlog Story 2b, "E2E test — add a task, see it appear in the list"
  preconditions: [frontend and backend running, empty test database]
  data_needs: [title "E2E add task"]
  steps: [open the page, type the title, click submit, check the list]
  expected: a row titled "E2E add task" is visible
  priority: P1
- id: TP-005
  level: unit
  title: Submitting with an empty title is blocked client-side
  requirement_ref: Backlog Story 2b, "Client-side validation (title required)"
  preconditions: [add-task form rendered with the create-task API function stubbed]
  data_needs: [title left empty]
  steps: [submit without typing a title]
  expected: the create-task function is not called
  priority: P1
```

## Traceability
| Requirement | Cases | Status |
|---|---|---|
| Add task form submits title + optional due date | TP-001 | covered |
| Status not accepted on create | TP-002 | covered |
| Title required | TP-003, TP-005 | covered |
| E2E: add a task, see it in the list | TP-004 | covered |

## Gaps
| ID | Requirement (quoted) | Problem | Question for owner |
|---|---|---|---|

## Out of scope
- Status change, delete, reminder: excluded from Story 2b by the backlog

## UI contract (e2e)
- Page `/`; title input, submit button and task list located by role/label (labels not yet confirmed)

## Change log
| Rev | Cases | Change | Decision | Source |
|---|---|---|---|---|
| 1 | all | Initial plan | n/a | — |
