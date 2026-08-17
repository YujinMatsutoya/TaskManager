# Task Manager — Development Backlog

*Build strategy: one layer-style pass for backend CRUD (clean, isolated
backend testing rep), then vertical slices for everything after (realistic,
fully end-to-end testable increments). Same frozen scope from
Task_Manager_Spec.md applies to every story — no adding anything not
listed there, in any story.*

*Testing approach: write tests with AI assistance as you go, not as a
separate timed comparison — existing research (METR, McKinsey, controlled
task-level studies) already covers AI-assisted coding speed better than a
single-person, single-app benchmark could. The actual skill worth
demonstrating is catching and correcting what the AI gets wrong. Keep a
running catch log across all stories — see the bottom of this file.*

*AI-assistance method by story: Story 1 uses plain main-conversation
prompting (baseline). From Story 2 onward, define and use a `test-writer`
subagent (fixed system prompt, isolated context — see Module 1 in the
curriculum) instead of ad-hoc prompting, then have a `test-reviewer`
subagent critique its output before you do your own review. This keeps
test quality consistent across stories and gives a genuine before/after
comparison point.*

---

## Story 1 — Backend: Task model + CRUD endpoints
*Layer-style pass. No frontend yet.*

**Build:**
- `Task` model (id, title, due_date, status, created_at)
- `POST /tasks`, `GET /tasks` (with `?status=` filter), `GET /tasks/{id}`,
  `PATCH /tasks/{id}`, `DELETE /tasks/{id}`
- SQLite persistence

**Explicitly not in this story:** the `/remind` endpoint, any frontend code

**Test after this story (baseline — plain main-conversation prompting, log catches as you go):**
- [ ] Unit tests — status validation, model defaults
- [ ] Integration tests — each endpoint against a real test database
      (happy path + 404s + validation errors)

---

## Story 2 — Frontend

### Story 2a — Task list (read-only)
*Simplest possible slice — no mutations at all.*

**Build:**
- Task list view, rendering from `GET /tasks`
- Status filter dropdown/tabs

**Explicitly not in this story:** add form, status change, delete, reminder

**Test after this story (via test-writer + test-reviewer subagents, log catches as you go):**
- [ ] Unit tests — isolated rendering/filtering logic
- [ ] Integration tests — frontend against the real backend (not mocked)
- [ ] E2E test — load the page, filter by status

---

### Story 2b — Add task form

**Build:**
- Add task form (title + optional due date), submits to `POST /tasks`
- Client-side validation (title required)
- List re-renders to show the new task

**Explicitly not in this story:** status change, delete, reminder

**Test after this story (via test-writer + test-reviewer subagents, log catches as you go):**
- [ ] Unit tests — form validation logic
- [ ] Integration tests — submit against the real backend
- [ ] E2E test — add a task, see it appear in the list; try submitting
      with an empty title, confirm it's rejected

---

### Story 2c — Row actions: status change + delete

**Build:**
- Status change control on each row (`PATCH /tasks/{id}`)
- Delete button on each row (`DELETE /tasks/{id}`)

**Explicitly not in this story:** reminder button, reminder state display

**Test after this story (via test-writer + test-reviewer subagents, log catches as you go):**
- [ ] Unit tests — isolated row-action logic
- [ ] Integration tests — status change and delete against the real backend
- [ ] E2E test — change a task's status, confirm it updates; delete a task,
      confirm it disappears

---

## Story 3 — Backend: Reminder endpoint + async behaviour
*Layer-style pass, the trickiest piece in isolation before it's wired to UI.*

**Build:**
- Add `reminder_sent` field to the `Task` model (boolean, default `false`)
- `POST /tasks/{id}/remind`
- Delayed action (suggest 10–15s), sets `reminder_sent = true` after delay

**Explicitly not in this story:** any frontend changes

**Test after this story (via test-writer + test-reviewer subagents, log catches as you go):**
- [ ] Unit tests — reminder scheduling logic
- [ ] Integration tests — call the endpoint, assert `reminder_sent` flips
      to true after the delay (this is the one genuinely async test in the
      whole app — good place to watch for AI mishandling timing/flakiness)

---

## Story 4 — Frontend: Reminder button + visible state change
*Final vertical slice — completes the full pyramid on the async feature.*

**Build:**
- "Remind me" button on each task row
- Visible state change once `reminder_sent` flips true (badge/icon/text)
- Polling or re-fetch to pick up the state change

**Test after this story (via test-writer + test-reviewer subagents, log catches as you go):**
- [ ] Unit tests — any new isolated frontend logic (e.g. polling logic)
- [ ] E2E test — click "remind me", wait for the state change to appear in
      the UI, assert on it. This is the flagship E2E test for the whole
      app — a real async UI state change, not just an instant response.

---

## Running catch log (fill in throughout, not just at the end)

For every AI-generated test you accept, tweak, or reject, note it here.
This log — not a timing comparison — is the actual Module 1 portfolio
output.

| Story | Test | What AI got wrong / right | Fix applied | Caught by (you / reviewer subagent / both) |
|---|---|---|---|---|
| | | | | |

Categories worth watching for specifically (ties back to the mocking and
stubbing task in Module 3):
- Wrong assertion (passes but doesn't test the right thing)
- Over-mocked integration test (mocks something that should be real)
- Flaky async assertion (race condition in the reminder tests especially)
- Hallucinated coverage (test looks thorough but misses an actual edge case)
- Wrong test layer (E2E-style assertion inside what should be a fast unit
  test, or vice versa)

---

## After all stories: portfolio write-up

- [ ] Summarize the catch log into a short case study — what categories of
      AI mistakes showed up most, with 1-2 concrete examples
- [ ] Reference the existing productivity research (METR, McKinsey) rather
      than re-deriving your own timing numbers, to frame why this skill
      matters
- [ ] Use this as a CV bullet and interview talking point