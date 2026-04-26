from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
from models import User, Plan, Task


class StorageInterface(ABC):
    """Abstract storage interface."""

    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        """Gets a user by ID."""
        pass

    @abstractmethod
    async def save_user(self, user_id: int, username: Optional[str]):
        """Saves or updates a user."""
        pass

    @abstractmethod
    async def create_plan(
        self, user_id: int, subject: str, deadline: Optional[date]
    ) -> Plan:
        """Creates a new plan."""
        pass

    @abstractmethod
    async def update_plan_deadline(
        self, plan_id: int, deadline: Optional[date]
    ) -> bool:
        """Updates the plan deadline."""
        pass

    @abstractmethod
    async def get_plan(self, plan_id: int) -> Optional[Plan]:
        """Gets a plan by ID."""
        pass

    @abstractmethod
    async def get_user_plans(self, user_id: int) -> List[Plan]:
        """Gets all plans for the user."""
        pass

    @abstractmethod
    async def delete_plan(self, plan_id: int) -> bool:
        """Deletes a plan."""
        pass

    @abstractmethod
    async def create_task(
        self, plan_id: int, title: str, deadline: date
    ) -> Task:
        """Creates a new task."""
        pass

    @abstractmethod
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Gets a task by ID."""
        pass

    @abstractmethod
    async def get_tasks_by_plan(self, plan_id: int) -> List[Task]:
        """Gets all tasks for the plan."""
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> bool:
        """Updates a task."""
        pass

    @abstractmethod
    async def update_task_status(self, task_id: int, is_done: bool) -> bool:
        """Updates the task completion status."""
        pass

    @abstractmethod
    async def delete_task(self, task_id: int) -> bool:
        """Deletes a task."""
        pass

    @abstractmethod
    async def get_all_user_tasks(self, user_id: int) -> List[Task]:
        """Gets all tasks for the user."""
        pass