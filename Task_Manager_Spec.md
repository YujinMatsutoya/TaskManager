# Task Manager — Build Spec

*Practice target for Module 1 (AI-assisted testing) — frozen scope, see
"Explicitly out of scope" before touching anything not listed here.*

## Stack

- **Backend:** Python + FastAPI, SQLite (via SQLAlchemy or raw `sqlite3`)
- **Frontend:** React, plain CSS only — no component library, no styling
  framework. Deliberately unpolished; the point is real DOM interactions to
  drive with Playwright, not a portfolio-worthy UI.

## Data model

**Task**
| Field | Type | Notes |
|---|---|---|
| `id` | integer, PK | auto-increment |
| `title` | string | required |
| `due_date` | date | optional |
| `status` | enum: `todo`, `in_progress`, `done` | default `todo` |
| `created_at` | timestamp | auto-set on creation |

*`reminder_sent` (boolean, default `false`) is added later, alongside the
reminder feature — see backlog Story 3. Not part of the initial model.*

## Backend endpoints

| Method | Path | Behaviour |
|---|---|---|
| `POST` | `/tasks` | Create a task. Body: `title` (required), `due_date` (optional) |
| `GET` | `/tasks` | List all tasks. Optional query param `?status=todo\|in_progress\|done` |
| `GET` | `/tasks/{id}` | Get a single task; 404 if not found |
| `PATCH` | `/tasks/{id}` | Update status (and/or title/due_date) |
| `DELETE` | `/tasks/{id}` | Delete a task; 404 if not found |
| `POST` | `/tasks/{id}/remind` | Queue a reminder — see below |

### Field requirements per endpoint

**`POST /tasks` (creating) — fixed required/optional fields:**
- `title` — **required**. No task can exist without one.
- `due_date` — **optional**.
- `status` — **not accepted in the request body at all.** The server
  always forces new tasks to `todo`, regardless of what's sent. Reject or
  ignore any `status` field passed in on creation — don't let the client
  set it.

**`PATCH /tasks/{id}` (updating) — partial update, nothing individually
required, but the body as a whole can't be empty:**
- `title`, `due_date`, `status` — each **optional individually**, since
  only the fields present in the body get updated; everything else on the
  task stays untouched.
- An **empty body `{}`** should be rejected (422), not silently accepted
  as a no-op — this is a deliberate edge case to test.
- `status`, if sent, must be one of `todo` / `in_progress` / `done` —
  invalid values return 422, not silently accepted.

**`GET` and `DELETE`** — no body, so no field-requirement question; only
the `{id}` in the URL, which 404s if it doesn't exist.

**FastAPI implementation note** (via Pydantic models):
```python
class TaskCreate(BaseModel):
    title: str                          # required
    due_date: date | None = None        # optional
    # no status field — server always sets "todo"

class TaskUpdate(BaseModel):
    title: str | None = None            # all optional — partial update
    due_date: date | None = None
    status: Literal["todo", "in_progress", "done"] | None = None
```
FastAPI auto-generates 422 validation errors for missing/invalid fields —
each required field and each enum constraint gives an obvious test case
("what happens if I omit this", "what happens if I send garbage").

**Reminder behaviour (the one deliberate async feature):**
- On call, schedule a delayed action (e.g. `asyncio.sleep` in a background
  task, or a simple in-memory scheduler — no external queue/service)
- After the delay (suggest 10–15 seconds for practice purposes, not real
  minutes/hours), set `reminder_sent = true` on the task
- Frontend polls or re-fetches to reflect the state change — this is the
  "real UI state that changes after a delay" behaviour Module 1's E2E
  layer is meant to exercise

## Frontend screens

Single page is enough — no routing needed:
- **Task list** — shows all tasks, with a status filter dropdown/tabs
- **Add task form** — title + optional due date, submits to `POST /tasks`
- **Task row actions** — change status (dropdown or buttons), delete
  button, "remind me" button
- **Visual reminder state** — some visible change on the row once
  `reminder_sent` flips to true (badge, icon, text change — doesn't need
  to be pretty, just testable)

## Explicitly out of scope

Do not add, suggest, or scaffold any of the following unless asked:
- Authentication / user accounts
- Any database beyond SQLite
- Deployment configuration (Docker, cloud hosting, CI/CD)
- A styling framework or component library
- Additional entities beyond `Task` (no projects, tags, categories, users)
- Real notification delivery (email/push) — the in-app state flip is enough
- Tests, test files, or test configuration of any kind — see below

## Build instructions for Claude Code

**In the first prompt**, state explicitly:
Build exactly the app described in this spec. Do not add, suggest, or
scaffold anything beyond what's listed, including authentication, a
database beyond SQLite, deployment configuration, or a styling framework.
Do not write any automated tests, test files, or testing configuration —
I will add all testing separately as a learning exercise. If you'd
normally scaffold a test suite, skip that step entirely.


## Testing layers to practice afterward (Module 1)

| Layer | What it targets | Tooling |
|---|---|---|
| Unit | Status validation, reminder scheduling logic, isolated frontend functions | pytest, Vitest |
| Integration | API endpoints against the real (test) database | pytest + FastAPI TestClient |
| E2E | Full flow through the UI — create a task, mark it done, trigger a reminder, see the state change | Playwright |