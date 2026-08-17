from pydantic import BaseModel
from datetime import date, datetime
from typing import Literal


class TaskCreate(BaseModel):
    title: str
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    status: Literal["todo", "in_progress", "done"] | None = None


class TaskRead(BaseModel):
    id: int
    title: str
    due_date: date | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
