"""Integration tests for app.crud — exercised against a real (in-memory)
SQLite database, since every crud function takes a db: Session and calls
db.add/db.commit/db.query() directly.

Each test gets a fresh, isolated in-memory database via the `db` fixture
below, so no state leaks between tests.
"""

from datetime import date

import pytest
from sqlalchemy import create_engine

from app import crud
from app.database import Base, SessionLocal
from app.schemas import TaskCreate, TaskUpdate


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session
    session.close()


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


def test_create_task_persists_title_only(db):
    task = crud.create_task(db, TaskCreate(title="Buy milk"))

    assert task.id is not None
    assert task.title == "Buy milk"
    assert task.due_date is None


def test_create_task_persists_title_and_due_date(db):
    task = crud.create_task(
        db, TaskCreate(title="Buy milk", due_date=date(2026, 8, 20))
    )

    assert task.id is not None
    assert task.title == "Buy milk"
    assert task.due_date == date(2026, 8, 20)


def test_create_task_forces_status_todo(db):
    """Business rule: newly created tasks always start as 'todo', regardless
    of what the caller passes (TaskCreate has no status field at all — see
    test_schema_task_create_ignores_unknown_status_field)."""
    task = crud.create_task(db, TaskCreate(title="status todo check"))

    assert task.status == "todo"


# ---------------------------------------------------------------------------
# get_tasks
# ---------------------------------------------------------------------------


def _seed_mixed_status_tasks(db):
    """Seed one task each of status todo, in_progress, done.

    Returns the three created Task objects.
    """
    todo_task = crud.create_task(db, TaskCreate(title="todo task"))
    in_progress_task = crud.create_task(db, TaskCreate(title="in progress task"))
    done_task = crud.create_task(db, TaskCreate(title="done task"))

    crud.update_task(db, in_progress_task.id, TaskUpdate(status="in_progress"))
    crud.update_task(db, done_task.id, TaskUpdate(status="done"))

    return todo_task, in_progress_task, done_task


def test_get_tasks_returns_all_when_no_filter(db):
    _seed_mixed_status_tasks(db)

    tasks = crud.get_tasks(db, status=None)

    assert len(tasks) == 3


def test_get_tasks_filters_by_status(db):
    _seed_mixed_status_tasks(db)

    tasks = crud.get_tasks(db, status="in_progress")

    assert len(tasks) == 1
    assert tasks[0].status == "in_progress"


def test_get_tasks_empty_status_string_returns_all(db):
    # Confirmed intended (human review 2026-08-18): empty filter value = no
    # filter. `if status:` in crud.py stays as-is; this test locks the
    # behavior in, not a bug report.
    _seed_mixed_status_tasks(db)

    tasks = crud.get_tasks(db, status="")

    assert len(tasks) == 3


def test_get_tasks_returns_empty_list_when_no_matches(db):
    crud.create_task(db, TaskCreate(title="todo task"))

    tasks = crud.get_tasks(db, status="done")

    assert tasks == []


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------


def test_get_task_returns_task_when_exists(db):
    created = crud.create_task(db, TaskCreate(title="Buy milk"))

    fetched = crud.get_task(db, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Buy milk"


def test_get_task_returns_none_when_not_exists(db):
    result = crud.get_task(db, 9999)

    assert result is None


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------


def test_update_task_title_only(db):
    created = crud.create_task(
        db, TaskCreate(title="Old title", due_date=date(2026, 8, 20))
    )

    updated = crud.update_task(db, created.id, TaskUpdate(title="New title"))

    assert updated.title == "New title"
    assert updated.due_date == date(2026, 8, 20)
    assert updated.status == "todo"


def test_update_task_due_date_only(db):
    created = crud.create_task(db, TaskCreate(title="Buy milk"))

    updated = crud.update_task(
        db, created.id, TaskUpdate(due_date=date(2026, 9, 1))
    )

    assert updated.due_date == date(2026, 9, 1)
    assert updated.title == "Buy milk"
    assert updated.status == "todo"


def test_update_task_status_only(db):
    created = crud.create_task(db, TaskCreate(title="Buy milk"))

    updated = crud.update_task(db, created.id, TaskUpdate(status="done"))

    assert updated.status == "done"
    assert updated.title == "Buy milk"


def test_update_task_multiple_fields(db):
    """Sanity check, not combinatorial coverage — proves one commit
    correctly picks up every changed field at once (fields are independent
    per-branch; this is the maximal case, not one of several needed
    permutations)."""
    created = crud.create_task(db, TaskCreate(title="Old title"))

    updated = crud.update_task(
        db,
        created.id,
        TaskUpdate(
            title="New", due_date=date(2026, 9, 1), status="in_progress"
        ),
    )

    assert updated.title == "New"
    assert updated.due_date == date(2026, 9, 1)
    assert updated.status == "in_progress"


def test_update_task_clear_due_date_with_explicit_null(db):
    """Critical: three-way branch — explicit null clears the field."""
    created = crud.create_task(
        db, TaskCreate(title="Buy milk", due_date=date(2026, 8, 20))
    )

    updated = crud.update_task(db, created.id, TaskUpdate(due_date=None))

    assert updated.due_date is None


def test_update_task_omit_due_date_leaves_untouched(db):
    """Critical: omitted field must NOT be treated as null."""
    created = crud.create_task(
        db, TaskCreate(title="Buy milk", due_date=date(2026, 8, 20))
    )

    updated = crud.update_task(db, created.id, TaskUpdate(title="New"))

    assert updated.due_date == date(2026, 8, 20)


def test_update_task_returns_none_when_not_exists(db):
    result = crud.update_task(db, 9999, TaskUpdate(title="New"))

    assert result is None


def test_update_task_title_explicit_null_is_ignored(db):
    # Confirmed intended (human review 2026-08-18): title is NOT NULL in
    # the DB, so there's nothing meaningful to clear — silent no-op is fine
    # despite the due_date asymmetry. This test locks the behavior in, not
    # a bug report.
    created = crud.create_task(db, TaskCreate(title="Buy milk"))

    updated = crud.update_task(db, created.id, TaskUpdate(title=None))

    assert updated.title == "Buy milk"


# ---------------------------------------------------------------------------
# delete_task
# ---------------------------------------------------------------------------


def test_delete_task_removes_when_exists(db):
    created = crud.create_task(db, TaskCreate(title="Buy milk"))

    result = crud.delete_task(db, created.id)

    assert result is True
    assert crud.get_task(db, created.id) is None


def test_delete_task_returns_false_when_not_exists(db):
    result = crud.delete_task(db, 9999)

    assert result is False
