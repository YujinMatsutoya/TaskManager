from sqlalchemy.orm import Session
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate


def create_task(db: Session, task: TaskCreate) -> Task:
    db_task = Task(title=task.title, due_date=task.due_date, status="todo")
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, status: str | None = None) -> list[Task]:
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.all()


def get_task(db: Session, task_id: int) -> Task | None:
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Task | None:
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        return None

    if task_update.title is not None:
        db_task.title = task_update.title
    if task_update.due_date is not None:
        db_task.due_date = task_update.due_date
    elif task_update.due_date is None and "due_date" in task_update.model_fields_set:
        db_task.due_date = None
    if task_update.status is not None:
        db_task.status = task_update.status

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True
