from telegram import Update
from telegram.ext import ContextTypes
from datetime import date, datetime

from services.study_service import StudyService
from services.reminder_service import ReminderService
from storage import storage
from keyboards.main_menu import MainMenuKeyboard
from keyboards.calendar import CalendarKeyboard
from keyboards.plans import PlanKeyboard
from keyboards.tasks import TaskKeyboard
from helpers.message_templates import MessageTemplates


class CallbackHandler:
    def __init__(
        self, study_service: StudyService, reminder_service: ReminderService
    ):
        self.study_service = study_service
        self.reminder_service = reminder_service

    @staticmethod
    def _parse_id(data: str, prefix: str, index: int) -> int | None:
        if data.startswith(prefix):
            try:
                return int(data.split("_")[index])
            except (ValueError, IndexError):
                return None
        return None

    @staticmethod
    def _parse_calendar_date(data: str) -> tuple[int, int, int] | None:
        if "_" not in data:
            return None
        parts = data.split("_")
        if len(parts) >= 4:
            try:
                year = int(parts[-3])
                month = int(parts[-2])
                day = int(parts[-1])
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return year, month, day
            except (ValueError, IndexError):
                pass
        return None

    async def _get_task_or_reply(
        self,
        update: Update,
        task_id: int,
    ) -> tuple[Update, int] | None:
        query = update.callback_query
        task = await storage.get_task(task_id)
        if task is None:
            await query.edit_message_text(MessageTemplates.TASK_NOT_FOUND)
            return None
        return task

    @staticmethod
    def _task_to_dict(task) -> dict:
        return {
            "task_id": task.task_id,
            "plan_id": task.plan_id,
            "title": task.title,
            "deadline": task.deadline,
            "is_done": task.is_done,
        }

    @staticmethod
    def _plan_to_dict(plan) -> dict:
        return {
            "plan_id": plan.plan_id,
            "user_id": plan.user_id,
            "subject": plan.subject,
            "deadline": plan.deadline,
        }

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "noop":
            return

        handlers = {
            "cmd_new_plan": self._show_subject_input,
            "cmd_add_task": self._show_plans_for_task,
            "cmd_my_plans": self._show_plans_list,
            "cmd_reminders": self._show_reminders,
            "back_to_menu": self._back_to_menu,
            "back_to_plans": self._show_plans_list,
            "cal_today": self._handle_cal_today,
            "cmd_cancel_date": self._cancel_date,
        }

        if data in handlers:
            await handlers[data](update, context)
            return

        if data.startswith("cal_prev_") or data.startswith("cal_next_"):
            await self._handle_calendar_nav(update, context, data)
            return

        if date_result := self._parse_calendar_date(data):
            await self._select_date(update, context, *date_result)
            return

        if plan_id := self._parse_id(data, "view_plan_", 2):
            await self._show_plan_detail(update, context, plan_id)
            return

        if task_id := self._parse_id(data, "task_detail_", 2):
            await self._show_task_detail(update, context, task_id)
            return

        if task_id := self._parse_id(data, "done_", 1):
            await self._mark_task_done(update, context, task_id)
            return

        if task_id := self._parse_id(data, "undone_", 1):
            await self._mark_task_undone(update, context, task_id)
            return

        if plan_id := self._parse_id(data, "delete_plan_", 2):
            await self._delete_plan(update, context, plan_id)
            return

        if task_id := self._parse_id(data, "delete_task_", 2):
            await self._delete_task(update, context, task_id)
            return

        if plan_id := self._parse_id(data, "plan_", 1):
            await self._show_task_title_input(update, context, plan_id)
            return

        if plan_id := self._parse_id(data, "task_title_", 2):
            await self._show_task_deadline_input(update, context, plan_id)
            return

    async def _back_to_menu(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        await self._return_to_main_menu(update, context, clear_data=False)

    async def _cancel_date(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        await self._return_to_main_menu(update, context, clear_data=True)

    async def _return_to_main_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        clear_data: bool = False,
    ):
        query = update.callback_query
        if clear_data:
            context.user_data.clear()
        await query.edit_message_text(
            MessageTemplates.MAIN_MENU, reply_markup=MainMenuKeyboard.build()
        )

    async def _handle_cal_today(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        today = datetime.now()
        await self._select_date(
            update, context, today.year, today.month, today.day
        )

    async def _handle_calendar_nav(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
    ):
        query = update.callback_query
        parts = data.split("_")
        year = int(parts[-2])
        month = int(parts[-1])

        if data.startswith("cal_prev"):
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        else:
            month += 1
            if month > 12:
                month = 1
                year += 1

        await query.edit_message_text(
            MessageTemplates.SELECT_DATE,
            reply_markup=CalendarKeyboard.build(
                year, month, context.user_data.get("cal_prefix", "date_")
            ),
        )

    async def _show_subject_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.edit_message_text(
            MessageTemplates.ENTER_PLAN_SUBJECT,
            reply_markup=TaskKeyboard.confirm_back("back_to_menu"),
        )
        context.user_data["awaiting"] = "plan_subject"

    async def _show_plans_list(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        user_id = update.effective_user.id
        plans = await self.study_service.get_plan(user_id)

        if not plans:
            await query.edit_message_text(
                MessageTemplates.NO_PLANS,
                reply_markup=PlanKeyboard.back("back_to_menu"),
            )
            return

        plans_data = [
            {
                "plan_id": p.plan_id,
                "subject": p.subject,
                "deadline": p.deadline,
            }
            for p in plans
        ]
        await query.edit_message_text(
            MessageTemplates.SELECT_PLAN,
            reply_markup=PlanKeyboard.plans_list(plans_data),
        )

    async def _show_plan_detail(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int
    ):
        query = update.callback_query
        user_id = update.effective_user.id
        plan = await self.study_service.get_plan_by_id(plan_id)

        if not plan:
            await query.edit_message_text(
                MessageTemplates.PLAN_NOT_FOUND,
                reply_markup=PlanKeyboard.back("back_to_plans"),
            )
            return

        if plan.user_id != user_id:
            await query.edit_message_text(
                MessageTemplates.PLAN_NOT_FOUND,
                reply_markup=PlanKeyboard.back("back_to_menu"),
            )
            return

        tasks = await self.study_service.get_tasks(plan_id)
        deadline_text = self.study_service.format_deadline(plan.deadline)

        if not tasks:
            await query.edit_message_text(
                MessageTemplates.PLAN_DETAIL_NO_TASKS.format(
                    subject=plan.subject, deadline=deadline_text
                ),
                reply_markup=PlanKeyboard.plan_detail_no_tasks(plan_id),
                parse_mode="HTML",
            )
            return

        tasks_data = [
            {
                "task_id": t.task_id,
                "title": t.title,
                "is_done": t.is_done,
                "plan_id": t.plan_id,
            }
            for t in tasks
        ]
        await query.edit_message_text(
            MessageTemplates.PLAN_DETAIL.format(
                subject=plan.subject, deadline=deadline_text
            ),
            reply_markup=PlanKeyboard.plan_detail(plan_id, tasks_data),
            parse_mode="HTML",
        )

    async def _show_task_detail(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int
    ):
        query = update.callback_query
        user_id = update.effective_user.id
        task = await storage.get_task(task_id)

        if not task:
            await query.edit_message_text(MessageTemplates.TASK_NOT_FOUND)
            return

        plan = await self.study_service.get_plan_by_id(task.plan_id)

        if not plan or plan.user_id != user_id:
            await query.edit_message_text(MessageTemplates.TASK_NOT_FOUND)
            return

        deadline_text = (
            task.deadline.strftime("%d.%m.%Y") if task.deadline else "Немає"
        )

        status_icon = "✅" if task.is_done else "⬜"

        task_dict = self._task_to_dict(task)

        await query.edit_message_text(
            MessageTemplates.TASK_DETAIL_FORMAT.format(
                status=status_icon,
                title=task.title,
                deadline=deadline_text,
                subject=plan.subject if plan else "Невідомо",
            ),
            reply_markup=TaskKeyboard.task_detail(
                task_dict, plan.subject if plan else ""
            ),
            parse_mode="HTML",
        )

    async def _mark_task_done(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int
    ):
        task = await storage.get_task(task_id)
        if task is None:
            await update.callback_query.edit_message_text(
                MessageTemplates.TASK_NOT_FOUND
            )
            return

        if task.is_done:
            await self._show_task_detail(update, context, task_id)
            return

        await self._set_task_status(update, context, task_id, True)

    async def _mark_task_undone(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int
    ):
        await self._set_task_status(update, context, task_id, False)

    async def _delete_task(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: int
    ):
        query = update.callback_query

        task = await storage.get_task(task_id)
        if task is None:
            await query.edit_message_text(MessageTemplates.TASK_NOT_FOUND)
            return

        plan_id = task.plan_id
        await storage.delete_task(task_id)
        await self.reminder_service.cancel_reminder(task_id)

        tasks = await self.study_service.get_tasks(plan_id)
        if tasks:
            latest_deadline = max(t.deadline for t in tasks if t.deadline)
            await storage.update_plan_deadline(plan_id, latest_deadline)
        else:
            await storage.update_plan_deadline(plan_id, None)

        await self._show_plan_detail(update, context, plan_id)

    async def _delete_plan(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int
    ):
        query = update.callback_query
        user_id = update.effective_user.id

        plan = await self.study_service.get_plan_by_id(plan_id)
        if not plan:
            await query.edit_message_text(MessageTemplates.PLAN_NOT_FOUND)
            return

        if plan.user_id != user_id:
            await query.edit_message_text(MessageTemplates.PLAN_NOT_FOUND)
            return

        tasks = await self.study_service.get_tasks(plan_id)
        for task in tasks:
            await self.reminder_service.cancel_reminder(task.task_id)

        await storage.delete_plan(plan_id)

        await self._show_plans_list(update, context)

    async def _show_plans_for_task(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        user_id = update.effective_user.id
        plans = await self.study_service.get_plan(user_id)

        if not plans:
            await query.edit_message_text(
                MessageTemplates.NO_PLANS_FOR_TASK,
                reply_markup=PlanKeyboard.back("back_to_menu"),
            )
            return

        plans_data = [
            {"plan_id": p.plan_id, "subject": p.subject} for p in plans
        ]
        await query.edit_message_text(
            MessageTemplates.SELECT_PLAN,
            reply_markup=PlanKeyboard.for_adding_task(plans_data),
        )

    async def _show_task_title_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int
    ):
        query = update.callback_query
        context.user_data["selected_plan_id"] = plan_id
        plan = await self.study_service.get_plan_by_id(plan_id)

        await query.edit_message_text(
            MessageTemplates.TASK_TITLE_PROMPT.format(subject=plan.subject),
            reply_markup=TaskKeyboard.task_title_input(plan.subject, plan_id),
            parse_mode="HTML",
        )
        context.user_data["awaiting"] = "task_title"

    async def _show_task_deadline_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int
    ):
        query = update.callback_query
        task_title = context.user_data.get("task_title", "")
        context.user_data["selected_plan_id"] = plan_id
        context.user_data["awaiting"] = "task_deadline"
        context.user_data["cal_prefix"] = "task_date_"

        today = datetime.now()
        await query.edit_message_text(
            MessageTemplates.SELECT_TASK_DEADLINE.format(title=task_title),
            reply_markup=CalendarKeyboard.build(
                today.year, today.month, "task_date_"
            ),
            parse_mode="HTML",
        )

    async def _show_reminders(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        user_id = update.effective_user.id
        reminders = await self.reminder_service.list_reminders(user_id)

        if not reminders:
            await query.edit_message_text(
                MessageTemplates.NO_REMINDERS,
                reply_markup=PlanKeyboard.back("back_to_menu"),
            )
            return

        reminders_text = "\n".join(
            f"• <b>{rem['title']}</b> — {rem['days_left']}"
            for rem in reminders
        )

        await query.edit_message_text(
            MessageTemplates.REMINDERS_LIST.format(reminders=reminders_text),
            reply_markup=PlanKeyboard.back("back_to_menu"),
            parse_mode="HTML",
        )

    async def _show_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query
        await query.edit_message_text(
            MessageTemplates.HELP,
            reply_markup=MainMenuKeyboard.build(),
            parse_mode="HTML",
        )

    async def _select_date(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        year: int,
        month: int,
        day: int,
    ):
        query = update.callback_query
        selected_date = date(year, month, day)
        awaiting = context.user_data.get("awaiting")

        if awaiting == "task_deadline":
            plan_id = context.user_data.get("selected_plan_id")
            title = context.user_data.get("task_title")

            task = await self.study_service.add_task(
                plan_id, title, selected_date
            )
            plan = await self.study_service.get_plan_by_id(plan_id)

            if plan:
                await self.study_service.update_plan_deadline(
                    plan_id, selected_date
                )
                plan = await self.study_service.get_plan_by_id(plan_id)

                task_dict = self._task_to_dict(task)
                plan_dict = self._plan_to_dict(plan)
                await self.reminder_service.schedule_task_reminders(
                    task_dict, plan_dict
                )

            await query.edit_message_text(
                MessageTemplates.TASK_ADDED.format(
                    title=title,
                    subject=plan.subject if plan else "",
                    deadline=selected_date.strftime("%d.%m.%Y"),
                ),
                reply_markup=MainMenuKeyboard.build(),
                parse_mode="HTML",
            )
            context.user_data.clear()
