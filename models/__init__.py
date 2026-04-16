from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str] = None
    timezone: str = "UTC"


@dataclass
class Plan:
    plan_id: int
    user_id: int
    subject: str
    deadline: Optional[date] = None
    tasks: list = field(default_factory=list)


@dataclass
class Task:
    task_id: int
    plan_id: int
    title: str
    deadline: date
    is_done: bool = False
