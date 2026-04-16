from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, List
from models import User, Plan, Task


class StorageInterface(ABC):
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[User]: pass
    
    @abstractmethod
    def save_user(self, user_id: int, username: Optional[str]): pass
    
    @abstractmethod
    def create_plan(self, user_id: int, subject: str, deadline: Optional[date]) -> Plan: pass
    
    @abstractmethod
    def update_plan_deadline(self, plan_id: int, deadline: Optional[date]) -> bool: pass
    
    @abstractmethod
    def get_plan(self, plan_id: int) -> Optional[Plan]: pass
    
    @abstractmethod
    def get_user_plans(self, user_id: int) -> List[Plan]: pass
    
    @abstractmethod
    def delete_plan(self, plan_id: int) -> bool: pass
    
    @abstractmethod
    def create_task(self, plan_id: int, title: str, deadline: date) -> Task: pass
    
    @abstractmethod
    def get_task(self, task_id: int) -> Optional[Task]: pass
    
    @abstractmethod
    def get_tasks_by_plan(self, plan_id: int) -> List[Task]: pass
    
    @abstractmethod
    def update_task(self, task: Task) -> bool: pass
    
    @abstractmethod
    def delete_task(self, task_id: int) -> bool: pass
    
    @abstractmethod
    def get_all_user_tasks(self, user_id: int) -> List[Task]: pass