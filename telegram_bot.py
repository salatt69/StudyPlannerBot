from telegram.ext import Application
from telegram import Bot, BotCommand
from telegram import MenuButtonCommands
from services import StudyService, ReminderService
from handlers import CommandHandler
from config import config
from storage import storage
import asyncio


class TelegramBot:
    def __init__(self):
        self.study_service = StudyService()
        self.reminder_service = None
        self.command_handler = None
        self.application = None
        self.bot = None

    async def setup(self):
        self.bot = Bot(token=config.TOKEN)

        self.reminder_service = ReminderService(self.bot, storage)

        self.command_handler = CommandHandler(
            study_service=self.study_service,
            reminder_service=self.reminder_service,
        )

        self.application = Application.builder().token(config.TOKEN).build()

        handlers = self.command_handler.get_handlers()
        for handler in handlers:
            self.application.add_handler(handler)

        commands = [
            BotCommand("start", "Головне меню"),
            BotCommand("help", "Допомога"),
        ]
        await self.bot.set_my_commands(commands)
        await self.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    async def start(self):
        await self.setup()
        print("Bot started...")

        asyncio.create_task(self.reminder_service.start_scheduler())

        async with self.bot:
            await self.bot.initialize()

            await self.application.initialize()
            await self.application.start()

            await self.application.updater.start_polling()

            print("Bot is running.")
            await asyncio.Event().wait()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    async def main():
        bot = TelegramBot()
        try:
            await bot.start()
        except KeyboardInterrupt:
            print("Shutting down...")
            if bot.application:
                await bot.application.stop()

    asyncio.run(main())
