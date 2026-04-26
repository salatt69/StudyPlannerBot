from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Union


class TaskKeyboard:
    """Keyboards for working with tasks."""

    @staticmethod
    def task_detail(task: Union[dict, object], plan_subject: str) -> InlineKeyboardMarkup:
        """Builds the task detail keyboard.

        Args:
            task: Task object.
            plan_subject: Plan name.

        Returns:
            Task detail keyboard.
        """
        keyboard = []
        is_done = task.is_done if hasattr(task, "is_done") else task["is_done"]
        task_id = task.task_id if hasattr(task, "task_id") else task["task_id"]
        plan_id = task.plan_id if hasattr(task, "plan_id") else task["plan_id"]

        if is_done:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "↩️ Позначити як невиконане",
                        callback_data=f"undone_{task_id}",
                    )
                ]
            )
        else:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Позначити як виконане",
                        callback_data=f"done_{task_id}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🗑️ Видалити завдання",
                    callback_data=f"delete_task_{task_id}",
                )
            ]
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 До плану", callback_data=f"view_plan_{plan_id}"
                )
            ]
        )

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def task_title_input(plan_subject: str, plan_id: int) -> InlineKeyboardMarkup:
        """Builds the task title input keyboard.

        Args:
            plan_subject: Plan name.
            plan_id: Plan ID.

        Returns:
            Title input keyboard.
        """
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="cmd_add_task")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirm_back(callback: str = "back_to_menu") -> InlineKeyboardMarkup:
        """Builds a confirmation keyboard with Back button.

        Args:
            callback: Callback for Back button.

        Returns:
            Confirmation keyboard.
        """
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Назад", callback_data=callback)]]
        )