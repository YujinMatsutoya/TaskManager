# Story 1 Wrap-Up: CRUD + Testing Foundation

## Overview

Story 1 delivered a FastAPI CRUD backend for Task management. This document captures the work done on *testing* that backend — the architectural decisions, learning moments, and open questions for future refinement.

---

## What Was Built

### Application Layer (pre-existing)
- **main.py**: HTTP routing (POST/GET/PATCH/DELETE /tasks)
- **schemas.py**: Pydantic validation (TaskCreate, TaskUpdate, TaskRead)
- **crud.py**: Business logic & data access (5 CRUD functions)
- **models.py**: SQLAlchemy ORM (Task model)
- **database.py**: SQLite session management

### Testing Infrastructure (new, this iteration)
- **CLAUDE.md update**: Clarified that test-writer subagent is the *only* place tests may be written; main session delegates all test-writing to it
- **.claude/agents/test-writer.md**: Subagent definition scoped to read specs-only (not source code), write under `backend/tests/` only, never modify implementation
- **.claude/hooks/**: Two PreToolUse hooks enforcing bidirectional test-directory boundary:
  - `restrict_test_writer.py`: confines test-writer to `backend/tests/`
  - `reserve_test_dir_for_test_writer.py`: blocks main session from writing tests
- **backend/tests/test_schemas.py**: 2 unit tests (Pydantic schema behavior)
- **backend/tests/test_crud.py**: 19 integration tests (CRUD layer + DB)
- **backend/tests/conftest.py**: pytest fixture and sys.path config

### Test Results
**21 passed, 0 failed** (2 unit + 19 integration)

---

## Key Learning Moments

### 1. Testing Layers: Unit vs. Integration vs. End-to-End

**Question:** "Are we testing Pydantic, or are we testing our code?"

**Learning:** Tests should target *your* logic, not framework behavior.
- **Unit tests**: Pure schema/logic with no database. Example: `TaskUpdate()` → `model_fields_set == set()` proves Pydantic's built-in behavior. We write this not because Pydantic needs testing, but because our *code* (the empty-PATCH-body rejection in main.py) depends on this schema behavior existing.
- **Integration tests**: CRUD functions + real (in-memory) database. Pydantic is still validating upstream, but now we're testing how our CRUD code handles valid inputs across multiple cases.
- **End-to-end tests** (not written yet): HTTP endpoints + real database. Tests the full request→response flow including FastAPI's routing, dependency injection, and error handling.

**Implication:** Don't write tests for "does Pydantic work" (it's a proven library). Write tests for "does my code correctly use Pydantic" and "does my business logic survive different valid inputs."

### 2. Business Logic ≠ Framework Plumbing

**Question:** "What parts of the code *actually* need tests?"

**Learning:** Focus on custom branching and decision points, not on framework defaults.
- ✅ `crud.update_task`'s three-way `due_date` branch (explicit null vs. omitted) — this is *your* logic, handles an ambiguity Pydantic doesn't solve
- ✅ `create_task` forcing status to `"todo"` — custom rule layered on the framework
- ❌ HTTPException raising on 404 — that's FastAPI doing its job, already tested
- ❌ Pydantic validation rejecting invalid dates — that's Pydantic's job

**Priority order:** The most complex logic (due_date three-way branch, status forcing) gets the most test attention because it's where bugs hide and regressions sneak in.

### 3. Independence of Branches ≠ Combinatorial Test Explosion

**Question:** "Do we need to test all possible combinations of PATCH fields?"

**Learning:** Only test combinations when code actually branches on multiple fields together.
- `update_task`'s three `if` blocks (title, due_date, status) are independent — each one checks its own field, ignores the others.
- Testing title-only, due_date-only, status-only covers every code path.
- Testing title+due_date, title+status, all three, etc. exercises the *same code paths repeatedly* (each branch still runs solo) — no new bug-catching power.
- **Exception:** If you had a rule like "status can only be 'done' if due_date is non-null" — that's a *cross-field* dependency, now you need combination tests for the interaction.

**Lesson:** Don't enumerate permutations blindly. Test the *code branches*, not the *input shapes*.

### 4. Partial Updates (PATCH) Require Three-Way State Tracking

**Question:** "How do you distinguish 'client didn't mention this field' from 'client explicitly set it to null'?"

**Learning:** Standard HTTP/REST libraries don't distinguish this by default — it's a design problem you have to solve explicitly.
- **The Problem:** A PATCH with `{"title": "New"}` (due_date omitted) and a PATCH with `{"title": "New", "due_date": null}` (due_date explicitly cleared) both produce `TaskUpdate(title="New", due_date=None)` if you only look at final values.
- **The Solution (Pydantic):** `model_fields_set` tracks which fields were actually present in the input JSON, separate from their resolved value.
  ```python
  if due_date is not None:
      # Set to a new value
  elif due_date is None and "due_date" in model_fields_set:
      # Explicit clear
  else:
      # Omitted — leave untouched
  ```
- **Why it matters:** Forgetting this distinction silently breaks partial updates (omitted fields get accidentally cleared, or explicit clears get silently ignored).

This is probably the single most important edge case in the codebase for testing coverage.

### 5. Fixture-Based Test Isolation: Fresh DB Per Test

**Question:** "How do we keep tests from interfering with each other when they all write to a database?"

**Learning:** Use pytest fixtures with `yield`-based teardown — each test gets a fresh, empty database.
```python
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session          # test runs here
    session.close()        # teardown — automatic cleanup
```
- Each test that takes `db` as a parameter gets its own isolated in-memory SQLite
- Tests can't accidentally see data from previous tests
- `yield` ensures cleanup even if a test fails

**Implication:** Without this, `get_tasks_returns_empty_list_when_no_matches` would fail if an earlier test didn't clean up — now it passes consistently because every test starts from a blank slate.

### 6. Spec Ambiguities Surface in Tests

**Question:** "What happens if the spec doesn't explicitly define a behavior?"

**Learning:** Tests force you to make a decision. Two cases in this project:

**Case 1: Empty-string status filter**
- Spec didn't say: "GET /tasks?status=" should filter to zero results or be treated as no filter?"
- Code did: `if status:` (truthy-check) treats `""` same as None — no filter applied
- **Decision made (human review):** This is intentional. Test locks it in as expected behavior.
- **Lesson:** Don't skip edge cases because the spec is silent. Write a test, pick a reasonable behavior, document it.

**Case 2: Explicit null on non-nullable field**
- Spec didn't say: "PATCH with `{\"title\": null}` should clear, reject, or silently ignore?"
- Code did: Silently ignored (title can't be null in the DB anyway)
- **Decision made (human review):** This is intentional. Test locks it in as expected behavior.
- **Lesson:** Asymmetries (title ignores explicit-null, but due_date clears it) are OK if justified — but they need to be *intentional and tested*, not accidental.

### 7. Dedicated Subagent for Testing: Isolation of Concerns

**Question:** "Why use a separate `test-writer` subagent instead of having the main session write tests?"

**Learning:** Separating test-writing into its own subagent creates a forced context boundary that prevents common mistakes.
- **The Problem:** The context that wrote the *implementation* code (main session) is most likely to fall into the *same patterns* when writing tests — thinking in terms of "how I implemented it" rather than "what the contract should be." This creates tightly-coupled tests that validate implementation details instead of behavior.
- **The Solution:** A dedicated `test-writer` subagent with clear scope (reads specs only, not source code; writes tests only, not implementation) forces a different mindset: "test from the spec's perspective, not the implementation's."
- **Boundary enforcement:** CLAUDE.md explicitly forbids the main session from writing or even *suggesting* tests. This isn't punitive; it's structural — it prevents the drift that happens when you're switching contexts between "implementing" and "testing" within the same conversation.
- **Reusability:** The test-writer (defined in `.claude/agents/test-writer.md`) becomes a reusable tool for future stories. Story 2 can invoke the same agent with the same constraints, ensuring consistent testing discipline across the project.

**Implication:** This setup trades a small context-switching cost (invoking the subagent) for a large payoff in test independence and long-term maintainability. The tests end up testing behavior, not implementation.

### 8. PreToolUse Hooks: Technical Enforcement of Boundaries

**Question:** "How do we *enforce* the test-writing boundary, not just ask for it in instructions?"

**Learning:** PreToolUse hooks can block tool calls before they execute, creating a hard technical boundary that instructions alone can't provide.

**Setup:**
- `restrict_test_writer.py`: Blocks the test-writer subagent from using Write/Edit outside `backend/tests/`
- `reserve_test_dir_for_test_writer.py`: Blocks the main session from using Write/Edit inside `backend/tests/`
- Both are registered in `.claude/settings.json` to run on every Write/Edit attempt

**Why it matters:**
- **Instructions are soft.** You can tell an agent "never write implementation code," and it usually obeys — but if it makes a mistake, the mistake goes through.
- **Hooks are hard.** A hook can literally prevent the tool call from succeeding, with a clear error message. No way around it.
- **Two-way enforcement:** Together, the two hooks create a genuine boundary: test-writer confined to tests, main session confined to non-tests. Neither can accidentally cross over.
- **Hook failures are visible:** When I tested the main session trying to write to `backend/tests/`, the hook blocked it with a clear message — that's how you know the boundary is real.

**Implication:** Hooks add a small amount of infrastructure setup (two Python scripts), but buy permanent, auditable enforcement of architectural decisions. Worth the cost for any serious separation of concerns.

---

## Open Questions / Future Refinement

### 1. Package Import Path and conftest.py

**The Problem:** When `uv run pytest` runs from `backend/`, test files in `backend/tests/` try to `from app import crud`. Python doesn't know where `app` is (it's a sibling directory, not an installed package). Without explicit help, the import fails.

**Three Solutions:**

1. **Manual sys.path hack (initial approach):** conftest.py adds `backend/` to sys.path imperatively:
   ```python
   import sys
   from pathlib import Path
   BACKEND_DIR = Path(__file__).resolve().parent.parent
   sys.path.insert(0, str(BACKEND_DIR))
   ```
   ✅ Works immediately, requires zero setup.
   ❌ Custom code that has to be maintained; can break if misunderstood later.

2. **Declarative pytest config (chosen solution):** Add `pythonpath = ["."]` to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   pythonpath = ["."]
   ```
   ✅ Standard pytest feature (v7.0+); no custom code; clear intent; works across all pytest invocation styles.
   ✅ Simpler conftest.py (now just a docstring).
   ❌ Requires knowing this pytest feature exists.

3. **Proper package install (longer-term):** `uv pip install -e .` with a proper `[build-system]` table in pyproject.toml.
   ✅ True Python package semantics; `app` importable from anywhere.
   ❌ Requires extra setup; overkill for a practice app that isn't distributed.

**Decision:** Implemented solution 2 — added `pythonpath` config to pyproject.toml and removed the sys.path code from conftest.py. All 21 tests pass, confirming the simpler approach works. This is the best balance for this project: minimal, standard, and maintainable.

### 2. Test Coverage Gaps (Intentional)

The 21 tests cover CRUD layer + schemas, but skip:
- **HTTP endpoint tests** (main.py routing, 404/422 translation) — would be integration tests using FastAPI's TestClient + real DB
- **Database constraint tests** (e.g., title NOT NULL) — worth adding if DB constraints drift from the ORM model
- **Performance/stress tests** — not relevant at this scale

These aren't gaps; they're planned for later (E2E layer in the spec), or they're low-value at this scope.

### 3. Two Bugs Found (Not Fixed, Per Policy)

The test suite didn't catch any bugs in the current code, but it did document two behaviors worth revisiting later:
1. **Status filter truthy-check:** `if status:` means `GET /tasks?status=` silently becomes "no filter." Arguably should be `if status is not None:`. Currently intentional; revisit if REST semantics become stricter.
2. **Title null asymmetry:** `PATCH {"title": null}` silently ignored, but `{"due_date": null}` clears due_date. Currently intentional (title can't be null anyway); revisit if the code logic ever changes.

No test changes needed; these are locked-in as expected behavior per human review.

---

## Summary: What This Means For Future Stories

1. **Testing is not optional.** Story 1 code has subtle branching logic (three-way update, status forcing) that's easy to regress — tests catch that.
2. **Specs have gaps.** Test-writing forces clarification. Document these clarifications (as happened with the two "confirmed intended" behaviors) so future stories don't re-litigate them.
3. **Fixtures and isolation matter.** Database tests need fresh state per test, or they'll fail mysteriously.
4. **Hooks enforce boundaries.** The test-writer subagent with bidirectional hooks ensures main-session code focus is separate from test-writing focus — no accidental test-code-in-main-code pollution.
5. **Package imports need clarity.** Sort out the conftest.py vs. proper package install flow before the project grows, or you'll have path-import issues in CI.

For Story 2 (frontend), we'll likely use a similar pattern: a testing-focused subagent, clear test boundaries, and spec-driven test-case design.

---

## Files Created/Modified This Iteration

**New:**
- `.claude/agents/test-writer.md` — subagent definition
- `.claude/hooks/restrict_test_writer.py` — boundary enforcement
- `.claude/hooks/reserve_test_dir_for_test_writer.py` — boundary enforcement
- `.claude/settings.json` — hook registration
- `backend/tests/test_schemas.py` — 2 unit tests
- `backend/tests/test_crud.py` — 19 integration tests
- `backend/tests/conftest.py` — pytest fixtures + sys.path config

**Modified:**
- `CLAUDE.md` — updated test-writing rule to delegate to test-writer subagent
- `backend/pyproject.toml` — added pytest as dev dependency (via `uv add --dev pytest`)

**Not modified** (per policy):
- `backend/app/` — source code untouched; if bugs were found, they'd be reported via test failures, not fixed by the test-writer subagent
