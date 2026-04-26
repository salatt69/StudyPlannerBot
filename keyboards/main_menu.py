from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class MainMenuKeyboard:
    """Main menu keyboard builder."""

    @staticmethod
    def build() -> InlineKeyboardMarkup:
        """Builds the main menu keyboard.

        Returns:
            Keyboard with buttons: New plan, Add task, My plans, Reminders.
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 Новий план", callback_data="cmd_new_plan"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Додати завдання", callback_data="cmd_add_task"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Мої плани", callback_data="cmd_my_plans"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔔 Нагадування", callback_data="cmd_reminders"
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)