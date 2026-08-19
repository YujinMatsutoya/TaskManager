"""Unit tests for app.schemas — pure schema behavior, no database required."""

from app.schemas import TaskCreate, TaskUpdate


def test_schema_task_update_empty_body_has_no_fields_set():
    """An empty TaskUpdate() should report no fields as explicitly set.

    This is the mechanism the empty-PATCH-body check in main.py relies on
    to detect a request with no updatable fields.
    """
    update = TaskUpdate()

    assert update.model_fields_set == set()


def test_schema_task_create_ignores_unknown_status_field():
    """TaskCreate has no 'status' field declared, so passing status=... on
    creation is silently dropped rather than raising or being stored.

    This is the mechanism the "can't set status on create" rule depends on.
    """
    task_create = TaskCreate(title="Buy milk", status="done")

    assert not hasattr(task_create, "status")
    assert task_create.title == "Buy milk"
