from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import calendar


class CalendarKeyboard:
    MONTH_NAMES = [
        "Січень",
        "Лютий",
        "Березень",
        "Квітень",
        "Травень",
        "Червень",
        "Липень",
        "Серпень",
        "Вересень",
        "Жовтень",
        "Листопад",
        "Грудень",
    ]
    DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

    @staticmethod
    def build(year: int, month: int, callback_prefix: str):
        keyboard = []

        header = f"{CalendarKeyboard.MONTH_NAMES[month-1]} {year}"
        keyboard.append([InlineKeyboardButton(header, callback_data="noop")])

        days_row = [
            InlineKeyboardButton(d, callback_data="noop") for d in CalendarKeyboard.DAY_NAMES
        ]
        keyboard.append(days_row)

        cal = calendar.monthcalendar(year, month)
        for week in cal:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="noop"))
                else:
                    row.append(
                        InlineKeyboardButton(
                            str(day), callback_data=f"{callback_prefix}{year}_{month}_{day}"
                        )
                    )
            keyboard.append(row)

        nav_row = [
            InlineKeyboardButton("◀", callback_data=f"cal_prev_{year}_{month}"),
            InlineKeyboardButton("Сьогодні", callback_data="cal_today"),
            InlineKeyboardButton("▶", callback_data=f"cal_next_{year}_{month}"),
        ]
        keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 Скасувати", callback_data="cmd_cancel_date")])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def build_current_month(prefix: str = "date_"):
        today = datetime.now()
        return CalendarKeyboard.build(today.year, today.month, prefix)
