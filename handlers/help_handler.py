from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main_menu import MainMenuKeyboard
from helpers.message_templates import MessageTemplates


class HelpHandler:
    """Handler for /help command."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /help command.

        Args:
            update: Update object from Telegram.
            context: Bot context.
        """
        await update.message.reply_text(
            MessageTemplates.HELP,
            reply_markup=MainMenuKeyboard.build(),
            parse_mode="HTML",
        )