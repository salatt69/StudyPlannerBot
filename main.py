import asyncio


async def main():
    from telegram_bot import TelegramBot

    bot = TelegramBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("Shutting down...")
        if bot.application:
            await bot.application.stop()


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy()
            )
        except Exception:
            pass

    asyncio.run(main())
