from datetime import datetime, timedelta
from typing import List, Dict, Any
from telegram import Bot
import asyncio
from helpers.message_templates import MessageTemplates


class ReminderService:
    """Service for managing user reminders."""

    def __init__(self, bot: Bot, storage):
        """Initializes the reminder service.

        Args:
            bot: Telegram bot instance.
            storage: Storage object.
        """
        self.bot = bot
        self.storage = storage
        self.reminders = {}
        self.sent_reminders = set()
        asyncio.create_task(self._load_reminders())

    async def _load_reminders(self):
        """Loads reminders from database on startup."""
        db_reminders = await self.storage.get_all_reminders()
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
        """Sets a new reminder for a task.

        Args:
            task: Task object or dict with data.
            plan: Plan object or dict with data.
            delta: Time until deadline for reminder.
            reminder_type: Reminder type (today_tomorrow, week).
        """
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

        await self.storage.save_reminder(
            task_id,
            user_id,
            title,
            deadline,
            reminder_type,
            int(delta.total_seconds()),
        )

    async def cancel_reminder(self, task_id: int):
        """Cancels all reminders for a task.

        Args:
            task_id: Task ID.
        """
        keys_to_remove = [k for k in self.reminders if k.startswith(f"{task_id}_")]
        for key in keys_to_remove:
            del self.reminders[key]
            self.sent_reminders.discard(key)
        await self.storage.delete_reminders_for_task(task_id)

    async def send_notification(
        self, user_id: int, text: str, parse_mode: str = None
    ):
        """Sends a message to the user.

        Args:
            user_id: User ID.
            text: Message text.
            parse_mode: Formatting mode (HTML, Markdown).
        """
        try:
            await self.bot.send_message(
                chat_id=user_id, text=text, parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")

    async def list_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Gets the list of reminders for the user.

        Args:
            user_id: User ID.

        Returns:
            List of dicts with reminder data, sorted by time.
        """
        task_map = {}
        today = datetime.now().date()

        for rem in self.reminders.values():
            if rem["user_id"] != user_id:
                continue

            task_id = rem["task_id"]
            deadline_date = rem["deadline"].date() if hasattr(rem["deadline"], "date") else rem["deadline"]
            days_left = (deadline_date - today).days

            if (
                task_id not in task_map
                or days_left < task_map[task_id]["days_num"]
            ):
                days_text = self._get_days_text(days_left)
                task_map[task_id] = {
                    "task_id": task_id,
                    "title": rem["title"],
                    "days_left": days_text,
                    "deadline": deadline_date.strftime("%d.%m.%Y"),
                    "days_num": days_left,
                }

        result = sorted(task_map.values(), key=lambda x: x["days_num"])
        for item in result:
            del item["days_num"]
        return result

    def _get_days_text(self, days_left: int) -> str:
        """Formats the number of days into text format.

        Args:
            days_left: Number of days until deadline.

        Returns:
            Text representation (Today, Tomorrow, X days, etc).
        """
        if days_left < 0:
            return "Прострочено"
        elif days_left == 0:
            return "Сьогодні"
        elif days_left == 1:
            return "Завтра"
        elif days_left <= 7:
            return f"{days_left} днів"
        elif days_left <= 30:
            return f"{days_left // 7} тижнів"
        else:
            return f"{days_left // 30} місяців"

    async def schedule_task_reminders(self, task, plan):
        """Schedules reminders for a task.

        Args:
            task: Task object.
            plan: Plan object.
        """
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
        """Gets the list of reminders that need to be sent.

        Returns:
            List of reminders whose time has come.
        """
        due = []
        now = datetime.now()

        for key, rem in self.reminders.items():
            if key in self.sent_reminders:
                continue

            deadline_date = rem["deadline"].date() if hasattr(rem["deadline"], "date") else rem["deadline"]
            reminder_time = deadline_date - rem["delta"]

            if reminder_time <= now.date():
                due.append(rem)
                self._mark_sent(rem["task_id"], rem["reminder_type"])

        return due

    def _mark_sent(self, task_id: int, reminder_type: str):
        """Marks a reminder as sent.

        Args:
            task_id: Task ID.
            reminder_type: Reminder type.
        """
        key = f"{task_id}_{reminder_type}"
        self.sent_reminders.add(key)
        asyncio.create_task(
            self.storage.mark_reminder_sent(task_id, reminder_type)
        )

    async def check_and_send(self):
        """Checks and sends reminders whose time has come."""
        due_reminders = self.get_due_reminders()

        for rem in due_reminders:
            user_id = rem["user_id"]
            title = rem["title"]
            reminder_type = rem["reminder_type"]
            deadline_date = rem["deadline"].date() if hasattr(rem["deadline"], "date") else rem["deadline"]
            days_left = (deadline_date - datetime.now().date()).days

            time_text = self._get_time_text(days_left)
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

    def _get_time_text(self, days_left: int) -> str:
        """Formats time until deadline for message.

        Args:
            days_left: Number of days until deadline.

        Returns:
            Text representation (Today, Tomorrow, In X days).
        """
        if days_left == 0:
            return "Сьогодні"
        elif days_left == 1:
            return "Завтра"
        else:
            return f"Через {days_left} днів"

    async def start_scheduler(self):
        """Starts the reminder check and send loop."""
        while True:
            await asyncio.sleep(60)
            await self.check_and_send()