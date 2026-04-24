from datetime import datetime, timedelta
from typing import List, Dict, Any
from telegram import Bot
import asyncio
from helpers.message_templates import MessageTemplates


class ReminderService:
    def __init__(self, bot: Bot, storage):
        self.bot = bot
        self.storage = storage
        self.reminders = {}
        self.sent_reminders = set()
        self._load_reminders()

    def _load_reminders(self):
        db_reminders = self.storage.get_all_reminders()
        for rem in db_reminders:
            key = rem["key"]
            self.reminders[key] = {
                "task_id": rem["task_id"],
                "user_id": rem["user_id"],
                "title": rem["title"],
                "deadline": rem["deadline"],
                "reminder_type": rem["reminder_type"],
                "delta": timedelta(seconds=rem["delta_seconds"]),
            }

    async def set_reminder(
        self, task, plan, delta: timedelta, reminder_type: str
    ):
        task_id = (
            task.task_id if hasattr(task, "task_id") else task.get("task_id")
        )
        reminder_key = f"{task_id}_{reminder_type}"

        if reminder_key in self.reminders:
            return

        user_id = (
            plan.user_id if hasattr(plan, "user_id") else plan.get("user_id")
        )
        title = task.title if hasattr(task, "title") else task.get("title")
        deadline = (
            task.deadline
            if hasattr(task, "deadline")
            else task.get("deadline")
        )

        self.reminders[reminder_key] = {
            "task_id": task_id,
            "user_id": user_id,
            "title": title,
            "deadline": deadline,
            "reminder_type": reminder_type,
            "delta": delta,
        }

        self.storage.save_reminder(
            task_id,
            user_id,
            title,
            deadline,
            reminder_type,
            int(delta.total_seconds()),
        )

    async def cancel_reminder(self, task_id: int):
        for key in list(self.reminders.keys()):
            if key.startswith(f"{task_id}_"):
                del self.reminders[key]
                self.sent_reminders.discard(key)
        self.storage.delete_reminders_for_task(task_id)

    async def send_notification(
        self, user_id: int, text: str, parse_mode: str = None
    ):
        try:
            await self.bot.send_message(
                chat_id=user_id, text=text, parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")

    async def list_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        task_map = {}
        today = datetime.now().date()

        for rem in self.reminders.values():
            if rem["user_id"] != user_id:
                continue

            task_id = rem["task_id"]
            deadline = rem["deadline"]
            if hasattr(deadline, "date"):
                deadline_date = deadline.date()
            else:
                deadline_date = deadline

            days_left = (deadline_date - today).days

            if (
                task_id not in task_map
                or days_left < task_map[task_id]["days_num"]
            ):
                if days_left < 0:
                    days_text = "Прострочено"
                elif days_left == 0:
                    days_text = "Сьогодні"
                elif days_left == 1:
                    days_text = "Завтра"
                elif days_left <= 7:
                    days_text = f"{days_left} днів"
                elif days_left <= 30:
                    weeks = days_left // 7
                    days_text = f"{weeks} тижнів"
                else:
                    months = days_left // 30
                    days_text = f"{months} місяців"

                task_map[task_id] = {
                    "task_id": task_id,
                    "title": rem["title"],
                    "days_left": days_text,
                    "deadline": deadline_date.strftime("%d.%m.%Y")
                    if hasattr(deadline_date, "strftime")
                    else str(deadline_date),
                    "days_num": days_left,
                }

        result = list(task_map.values())
        result.sort(key=lambda x: x["days_num"])
        for item in result:
            del item["days_num"]
        return result

    async def schedule_task_reminders(self, task, plan):
        deadline = (
            task.deadline
            if hasattr(task, "deadline")
            else task.get("deadline")
        )

        await self.set_reminder(
            task, plan, timedelta(days=1), "сьогодні_завтра"
        )

        if deadline:
            if hasattr(deadline, "date"):
                days_until_deadline = (
                    deadline.date() - datetime.now().date()
                ).days
            else:
                days_until_deadline = (deadline - datetime.now().date()).days

            if days_until_deadline >= 7:
                await self.set_reminder(
                    task, plan, timedelta(days=7), "тиждень"
                )

    def get_due_reminders(self) -> List[Dict[str, Any]]:
        due = []
        now = datetime.now()

        for key, rem in self.reminders.items():
            if key in self.sent_reminders:
                continue

            deadline = rem["deadline"]
            if hasattr(deadline, "date"):
                deadline_date = deadline.date()
            else:
                deadline_date = deadline

            reminder_time = deadline_date - rem["delta"]

            if reminder_time <= now.date():
                due.append(rem)
                self._mark_sent(rem["task_id"], rem["reminder_type"])

        return due

    def _mark_sent(self, task_id: int, reminder_type: str):
        key = f"{task_id}_{reminder_type}"
        self.sent_reminders.add(key)
        self.storage.mark_reminder_sent(task_id, reminder_type)

    async def check_and_send(self):
        due_reminders = self.get_due_reminders()

        for rem in due_reminders:
            user_id = rem["user_id"]
            title = rem["title"]
            reminder_type = rem["reminder_type"]
            deadline = rem["deadline"]

            deadline_date = (
                deadline.date() if hasattr(deadline, "date") else deadline
            )
            days_left = (deadline_date - datetime.now().date()).days

            if days_left == 0:
                time_text = "Сьогодні"
            elif days_left == 1:
                time_text = "Завтра"
            else:
                time_text = f"Через {days_left} днів"

            deadline_str = deadline_date.strftime("%d.%m.%Y")

            type_messages = {
                "сьогодні_завтра": MessageTemplates.REMINDER_TODAY_TOMORROW.format(
                    time_text=time_text, deadline=deadline_str, title=title
                ),
                "тиждень": MessageTemplates.REMINDER_WEEK.format(
                    deadline=deadline_str, title=title
                ),
            }

            text = type_messages.get(
                reminder_type,
                MessageTemplates.REMINDER_DEFAULT.format(
                    title=title, deadline=deadline_str
                ),
            )

            await self.send_notification(user_id, text, parse_mode="HTML")

    async def start_scheduler(self):
        while True:
            await asyncio.sleep(60)
            await self.check_and_send()
