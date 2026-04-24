from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Union


class PlanKeyboard:
    @staticmethod
    def plans_list(
        plans: List[Union[dict, object]], back_callback: str = "back_to_menu"
    ):
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
    ):
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
    def plan_detail_no_tasks(plan_id: int):
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
    def for_adding_task(plans: List[Union[dict, object]]):
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
    def back(back_callback: str = "back_to_menu"):
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Назад", callback_data=back_callback)]]
        )
