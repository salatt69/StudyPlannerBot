from datetime import date
from models import Plan, Task
from storage import storage


class StudyService:
    """Service for working with user plans and tasks."""

    async def create_plan(
        self, user_id: int, subject: str, deadline: date = None
    ) -> Plan:
        """Creates a new study plan for the user.

        Args:
            user_id: User ID.
            subject: Subject/plan name.
            deadline: Plan deadline (optional).

        Returns:
            The created plan.
        """
        return await storage.create_plan(user_id, subject, deadline)

    async def add_task(self, plan_id: int, title: str, deadline: date) -> Task:
        """Adds a task to the plan and updates the plan deadline.

        Args:
            plan_id: Plan ID.
            title: Task title.
            deadline: Task deadline.

        Returns:
            The created task.
        """
        task = await storage.create_task(plan_id, title, deadline)
        await self.update_plan_deadline(plan_id, deadline)
        return task

    async def update_plan_deadline(self, plan_id: int, new_deadline: date) -> bool:
        """Updates the plan deadline if new deadline is later than current.

        Args:
            plan_id: Plan ID.
            new_deadline: New deadline.

        Returns:
            True if updated, False otherwise.
        """
        plan = await storage.get_plan(plan_id)
        if plan:
            current_deadline = plan.deadline
            if current_deadline is None or new_deadline > current_deadline:
                await storage.update_plan_deadline(plan_id, new_deadline)
                return True
        return False

    async def get_plan(self, user_id: int) -> list[Plan]:
        """Gets all plans for the user.

        Args:
            user_id: User ID.

        Returns:
            List of user's plans.
        """
        return await storage.get_user_plans(user_id)

    async def get_tasks(self, plan_id: int) -> list[Task]:
        """Gets all tasks for the plan.

        Args:
            plan_id: Plan ID.

        Returns:
            List of plan tasks.
        """
        return await storage.get_tasks_by_plan(plan_id)

    async def get_plan_by_id(self, plan_id: int) -> Plan | None:
        """Gets a plan by its ID.

        Args:
            plan_id: Plan ID.

        Returns:
            Plan or None if not found.
        """
        return await storage.get_plan(plan_id)

    def format_deadline(self, deadline: date | None) -> str:
        """Formats the deadline date for display.

        Args:
            deadline: Deadline date.

        Returns:
            Formatted date as string.
        """
        if deadline is None:
            return "Немає"
        return deadline.strftime("%d.%m.%Y")