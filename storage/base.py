from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
from models import User, Plan, Task


class StorageInterface(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def save_user(self, user_id: int, username: Optional[str]):
        pass

    @abstractmethod
    async def create_plan(
        self, user_id: int, subject: str, deadline: Optional[date]
    ) -> Plan:
        pass

    @abstractmethod
    async def update_plan_deadline(
        self, plan_id: int, deadline: Optional[date]
    ) -> bool:
        pass

    @abstractmethod
    async def get_plan(self, plan_id: int) -> Optional[Plan]:
        pass

    @abstractmethod
    async def get_user_plans(self, user_id: int) -> List[Plan]:
        pass

    @abstractmethod
    async def delete_plan(self, plan_id: int) -> bool:
        pass

    @abstractmethod
    async def create_task(
        self, plan_id: int, title: str, deadline: date
    ) -> Task:
        pass

    @abstractmethod
    async def get_task(self, task_id: int) -> Optional[Task]:
        pass

    @abstractmethod
    async def get_tasks_by_plan(self, plan_id: int) -> List[Task]:
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> bool:
        pass

    @abstractmethod
    async def delete_task(self, task_id: int) -> bool:
        pass

    @abstractmethod
    async def get_all_user_tasks(self, user_id: int) -> List[Task]:
        pass
