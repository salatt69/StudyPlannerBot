from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_menu import MainMenuKeyboard
from keyboards.tasks import TaskKeyboard
from keyboards.calendar import CalendarKeyboard
from storage import storage
from helpers.message_templates import MessageTemplates


class UserMessageHandler:
    def __init__(self, study_service, reminder_service):
        self.study_service = study_service
        self.reminder_service = reminder_service
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        awaiting = context.user_data.get("awaiting")
        
        if awaiting == "plan_subject":
            existing = storage.get_plan_by_subject(user_id, text)
            if existing:
                await update.message.reply_text(
                    MessageTemplates.PLAN_EXISTS.format(subject=text),
                    reply_markup=TaskKeyboard.confirm_back("back_to_menu"),
                    parse_mode="HTML"
                )
                return
            
            context.user_data["subject"] = text
            plan = self.study_service.create_plan(user_id, text)
            await update.message.reply_text(
                MessageTemplates.PLAN_CREATED.format(subject=text),
                reply_markup=MainMenuKeyboard.build(),
                parse_mode="HTML"
            )
            context.user_data.clear()
        
        elif awaiting == "task_title":
            plan_id = context.user_data.get("selected_plan_id")
            plan = self.study_service.get_plan_by_id(plan_id)
            
            existing = storage.get_task_by_title(plan_id, text)
            if existing:
                await update.message.reply_text(
                    MessageTemplates.TASK_EXISTS.format(title=text, subject=plan.subject),
                    reply_markup=TaskKeyboard.task_title_input(plan.subject, plan_id),
                    parse_mode="HTML"
                )
                return
            
            context.user_data["task_title"] = text
            context.user_data["awaiting"] = "task_deadline"
            context.user_data["cal_prefix"] = "task_date_"
            
            import datetime
            today = datetime.datetime.now()
            await update.message.reply_text(
                MessageTemplates.TASK_DEADLINE_PROMPT.format(title=text),
                reply_markup=CalendarKeyboard.build(today.year, today.month, "task_date_"),
                parse_mode="HTML"
            )
        
        else:
            await update.message.reply_text(
                MessageTemplates.MAIN_MENU,
                reply_markup=MainMenuKeyboard.build()
            )