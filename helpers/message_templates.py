from typing import Any


class MessageTemplates:
    WELCOME = """👋 Вітаю! Я <b>Study Planner Bot</b> - ваш помічник для організації навчального процесу.

🍀 Допоможу вам створити план, додати завдання та відстежити прогрес!

/help — для отримання інформації про бота

Оберіть дію з меню нижче:"""

    HELP = """📖 <b>Допомога</b>

Використовуйте кнопки меню для навігації.

Кнопки меню:
• 📚 <b>Новий план</b> — створити новий навчальний план
• ➕ <b>Додати завдання</b> — додати завдання до плану
• 📋 <b>Мої плани</b> — переглянути ваші плани
• 🔔 <b>Нагадування</b> — переглянути активні нагадування

/start — Головне меню"""

    MAIN_MENU = "📋 Головне меню:"

    PLAN_CREATED = "✅ План '<b>{subject}</b>' створено!"
    PLAN_EXISTS = "❌ План з назвою '<b>{subject}</b>' вже існує!\n\nВведіть іншу назву:"
    PLAN_NOT_FOUND = "❌ План не знайдено."
    PLAN_DELETED = "✅ План '<b>{subject}</b>' видалено."
    NO_PLANS = "📭 У вас немає навчальних планів."
    SELECT_PLAN = "📋 Оберіть план:"
    PLAN_DETAIL = "📚 <b>{subject}</b>\n📅 Дедлайн: {deadline}\n\n📝 Оберіть завдання:"
    PLAN_DETAIL_NO_TASKS = "📚 <b>{subject}</b>\n📅 Дедлайн: {deadline}\n\n📝 Завдання: немає"

    TASK_ADDED = (
        "✅ Завдання '<b>{title}</b>' додано до плану '<b>{subject}</b>'!\n\n📅 Дедлайн: {deadline}"
    )
    TASK_DONE = "✅ Завдання '<b>{title}</b>' позначено як виконане!"
    TASK_UNDONE = "↩️ Завдання '<b>{title}</b>' позначено як невиконане."
    TASK_ALREADY_DONE = "ℹ️ Завдання '<b>{title}</b>' вже виконано."
    TASK_NOT_FOUND = "❌ Завдання не знайдено."
    TASK_DELETED = "✅ Завдання '<b>{title}</b>' видалено."
    TASK_EXISTS = "❌ Завдання з назвою '<b>{title}</b>' вже існує в плані '<b>{subject}</b>'!\n\nВведіть іншу назву:"
    NO_TASKS = "📝 У цьому плані немає завдань."

    SELECT_TASK = "📝 Оберіть завдання:"
    TASK_DETAIL_FORMAT = "{status} <b>{title}</b>\n\n📅 Дедлайн: {deadline}\n📚 План: {subject}"

    ENTER_PLAN_SUBJECT = "📚 Введіть назву предмета:"
    SELECT_TASK_DEADLINE = "📅 Оберіть дедлайн:"
    TASK_TITLE_PROMPT = "📚 План: <b>{subject}</b>\n\n📝 Введіть назву завдання:"
    TASK_DEADLINE_PROMPT = "📝 Завдання: <b>{title}</b>\n\n📅 Оберіть дедлайн:"

    NO_PLANS_FOR_TASK = "📭 У вас немає планів.\n\nСпочатку створіть план!"
    NO_REMINDERS = "🔔 У вас немає активних нагадувань."
    REMINDERS_LIST = "🔔 <b>Ваші нагадування:</b>\n\n{reminders}"

    REMINDER_TOMORROW = (
        "⏰ <b>Нагадування:</b>\n{time_text} ({deadline}) очікується виконання завдання «{title}»"
    )
    REMINDER_WEEK = (
        "⏰ <b>Нагадування:</b>\nчерез тиждень ({deadline}) очікується виконання завдання «{title}»"
    )
    REMINDER_24HOURS = "⏰ <b>Нагадування:</b>\nчерез 24 години ({deadline}) очікується виконання завдання «{title}»"
    REMINDER_DEFAULT = "⏰ <b>Нагадування:</b>\nзавдання «{title}» ({deadline})"

    SELECT_DATE = "📅 Оберіть дату:"

    @staticmethod
    def format(key: str, **kwargs: Any) -> str:
        template = getattr(MessageTemplates, key, None)
        if template is None:
            return key
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
