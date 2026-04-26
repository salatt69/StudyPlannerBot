from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class User:
    """
    Attributes:
        user_id: Unique user ID.
        username: Username (optional).
        timezone: User timezone.
    """
    user_id: int
    username: Optional[str] = None
    timezone: str = "UTC"


@dataclass
class Plan:
    """
    Attributes:
        plan_id: Unique plan ID.
        user_id: Owner user ID.
        subject: Subject name.
        deadline: Plan deadline (optional).
        tasks: List of task IDs for the plan.
    """
    plan_id: int
    user_id: int
    subject: str
    deadline: Optional[date] = None
    tasks: list = field(default_factory=list)


@dataclass
class Task:
    """
    Attributes:
        task_id: Unique task ID.
        plan_id: Plan ID the task belongs to.
        title: Task title.
        deadline: Task deadline.
        is_done: Completion status.
    """
    task_id: int
    plan_id: int
    title: str
    deadline: date
    is_done: bool = False