from datetime import date
from storage import storage


class StudyService:
    def create_plan(self, user_id: int, subject: str, deadline: date = None):
        user = storage.get_user(user_id)
        if user is None:
            storage.save_user(user_id, None)
        
        return storage.create_plan(user_id, subject, deadline)
    
    def add_task(self, plan_id: int, title: str, deadline: date):
        task = storage.create_task(plan_id, title, deadline)
        self.update_plan_deadline(plan_id, deadline)
        return task
    
    def update_plan_deadline(self, plan_id: int, new_deadline: date):
        plan = storage.get_plan(plan_id)
        if plan:
            current_deadline = plan.deadline
            if current_deadline is None or new_deadline > current_deadline:
                storage.update_plan_deadline(plan_id, new_deadline)
    
    def get_plan(self, user_id: int):
        return storage.get_user_plans(user_id)
    
    def get_tasks(self, plan_id: int):
        return storage.get_tasks_by_plan(plan_id)
    
    def get_plan_by_id(self, plan_id: int):
        return storage.get_plan(plan_id)
    
    def format_deadline(self, deadline: date) -> str:
        if deadline is None:
            return "Немає"
        return deadline.strftime("%d.%m.%Y")