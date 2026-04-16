from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_menu import MainMenuKeyboard
from storage import storage
from helpers.message_templates import MessageTemplates


class StartHandler:
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db_user = storage.get_user(user.id)

        if db_user is None:
            storage.save_user(user.id, user.username)

        await update.message.reply_text(
            MessageTemplates.WELCOME, reply_markup=MainMenuKeyboard.build(), parse_mode="HTML"
        )
