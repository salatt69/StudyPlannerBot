from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuKeyboard:
    @staticmethod
    def build():
        keyboard = [
            [InlineKeyboardButton("📚 Новий план", callback_data="cmd_new_plan")],
            [InlineKeyboardButton("➕ Додати завдання", callback_data="cmd_add_task")],
            [InlineKeyboardButton("📋 Мої плани", callback_data="cmd_my_plans")],
            [InlineKeyboardButton("🔔 Нагадування", callback_data="cmd_reminders")],
        ]
        return InlineKeyboardMarkup(keyboard)