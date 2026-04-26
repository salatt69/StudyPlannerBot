from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Union


class PlanKeyboard:
    """Keyboards for working with plans."""

    @staticmethod
    def plans_list(
        plans: List[Union[dict, object]], back_callback: str = "back_to_menu"
    ) -> InlineKeyboardMarkup:
        """Builds the plan list keyboard.

        Args:
            plans: List of plans.
            back_callback: Callback for Back button.

        Returns:
            Plan list keyboard.
        """
        keyboard = []
        for plan in plans:
            subject = (
                plan.subject if hasattr(plan, "subject") else plan["subject"]
            )
            plan_id = (
                plan.plan_id if hasattr(plan, "plan_id") else plan["plan_id"]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📚 {subject}", callback_data=f"view_plan_{plan_id}"
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def plan_detail(
        plan_id: int,
        tasks: List[Union[dict, object]],
        back_callback: str = "back_to_plans",
    ) -> InlineKeyboardMarkup:
        """Builds the plan detail keyboard.

        Args:
            plan_id: Plan ID.
            tasks: List of tasks.
            back_callback: Callback for Back button.

        Returns:
            Plan detail keyboard.
        """
        keyboard = []
        for task in tasks:
            is_done = (
                task.is_done if hasattr(task, "is_done") else task["is_done"]
            )
            title = task.title if hasattr(task, "title") else task["title"]
            task_id = (
                task.task_id if hasattr(task, "task_id") else task["task_id"]
            )
            status = "✅ " if is_done else "⬜ "
            keyboard.insert(
                0,
                [
                    InlineKeyboardButton(
                        f"{status}{title}",
                        callback_data=f"task_detail_{task_id}",
                    )
                ],
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️ Видалити план", callback_data=f"delete_plan_{plan_id}"
                )
            ]
        )
        keyboard.append(
            [InlineKeyboardButton("🔙 До списку", callback_data=back_callback)]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def plan_detail_no_tasks(plan_id: int) -> InlineKeyboardMarkup:
        """Builds the plan detail keyboard without tasks.

        Args:
            plan_id: Plan ID.

        Returns:
            Plan detail keyboard.
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "🗑️ Видалити план", callback_data=f"delete_plan_{plan_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 До списку", callback_data="back_to_plans"
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def for_adding_task(plans: List[Union[dict, object]]) -> InlineKeyboardMarkup:
        """Builds the plan selection keyboard for adding a task.

        Args:
            plans: List of plans.

        Returns:
            Plan selection keyboard.
        """
        keyboard = []
        for plan in plans:
            subject = (
                plan.subject if hasattr(plan, "subject") else plan["subject"]
            )
            plan_id = (
                plan.plan_id if hasattr(plan, "plan_id") else plan["plan_id"]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"📚 {subject}", callback_data=f"plan_{plan_id}"
                    )
                ]
            )
        keyboard.append(
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
        )
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back(back_callback: str = "back_to_menu") -> InlineKeyboardMarkup:
        """Builds a keyboard with a single Back button.

        Args:
            back_callback: Callback for Back button.

        Returns:
            Keyboard with Back button.
        """
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]]
        )