from datetime import date
from storage import storage


class StudyService:
    async def create_plan(
        self, user_id: int, subject: str, deadline: date = None
    ):
        return await storage.create_plan(user_id, subject, deadline)

    async def add_task(self, plan_id: int, title: str, deadline: date):
        task = await storage.create_task(plan_id, title, deadline)
        await self.update_plan_deadline(plan_id, deadline)
        return task

    async def update_plan_deadline(self, plan_id: int, new_deadline: date):
        plan = await storage.get_plan(plan_id)
        if plan:
            current_deadline = plan.deadline
            if current_deadline is None or new_deadline > current_deadline:
                await storage.update_plan_deadline(plan_id, new_deadline)

    async def get_plan(self, user_id: int):
        return await storage.get_user_plans(user_id)

    async def get_tasks(self, plan_id: int):
        return await storage.get_tasks_by_plan(plan_id)

    async def get_plan_by_id(self, plan_id: int):
        return await storage.get_plan(plan_id)

    def format_deadline(self, deadline: date) -> str:
        if deadline is None:
            return "Немає"
        return deadline.strftime("%d.%m.%Y")
