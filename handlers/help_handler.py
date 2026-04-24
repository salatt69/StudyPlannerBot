from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_menu import MainMenuKeyboard
from helpers.message_templates import MessageTemplates


class HelpHandler:
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            MessageTemplates.HELP,
            reply_markup=MainMenuKeyboard.build(),
            parse_mode="HTML",
        )
