from telegram.ext import (
    CommandHandler as TgCommandHandler,
    MessageHandler as TgMessageHandler,
    filters,
    CallbackQueryHandler,
)

from .start_handler import StartHandler
from .help_handler import HelpHandler
from .callback_handler import CallbackHandler
from .message_handler import UserMessageHandler


class CommandHandler:
    def __init__(self, study_service, reminder_service):
        self.start_handler = StartHandler()
        self.help_handler = HelpHandler()
        self.callback_handler = CallbackHandler(study_service, reminder_service)
        self.message_handler = UserMessageHandler(study_service, reminder_service)
    
    def get_handlers(self):
        return [
            TgCommandHandler("start", self.start_handler.handle),
            TgCommandHandler("help", self.help_handler.handle),
            CallbackQueryHandler(self.callback_handler.handle),
            TgMessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler.handle),
        ]