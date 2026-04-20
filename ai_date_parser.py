import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional


RUSSIAN_MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

WEEKDAY_ALIASES = {
    "понедельник": 0,
    "понедельника": 0,
    "пн": 0,
    "вторник": 1,
    "вторника": 1,
    "вт": 1,
    "среда": 2,
    "среду": 2,
    "среды": 2,
    "ср": 2,
    "четверг": 3,
    "четверга": 3,
    "чт": 3,
    "пятница": 4,
    "пятницу": 4,
    "пятницы": 4,
    "пт": 4,
    "суббота": 5,
    "субботу": 5,
    "субботы": 5,
    "сб": 5,
    "воскресенье": 6,
    "воскресенья": 6,
    "вс": 6,
}


@dataclass(frozen=True)
class ParsedDateContext:
    due_at: Optional[datetime] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    has_explicit_time: bool = False


def _start_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _end_of_week(value: date) -> date:
    return _start_of_week(value) + timedelta(days=6)


def _next_weekday(base: date, weekday: int) -> date:
    delta = (weekday - base.weekday()) % 7
    delta = 7 if delta == 0 else delta
    return base + timedelta(days=delta)


def extract_time(text: str) -> Optional[time]:
    match = re.search(r"\b([01]?\d|2[0-3])[:\-\.]([0-5]\d)\b", text)
    if match:
        return time(hour=int(match.group(1)), minute=int(match.group(2)))

    hour_only_match = re.search(r"\b([01]?\d|2[0-3])\s*(?:час(?:а|ов)?|ч)\b", text)
    if hour_only_match:
        return time(hour=int(hour_only_match.group(1)), minute=0)
    return None


def extract_absolute_date(text: str, now: datetime) -> Optional[date]:
    normalized = text.lower()

    numeric_match = re.search(r"\b(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?\b", normalized)
    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year = int(numeric_match.group(3)) if numeric_match.group(3) else now.year
        try:
            parsed = date(year, month, day)
            if not numeric_match.group(3) and parsed < now.date():
                parsed = date(year + 1, month, day)
            return parsed
        except ValueError:
            return None

    month_match = re.search(
        r"\b(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)(?:\s+(\d{4}))?\b",
        normalized,
    )
    if month_match:
        day = int(month_match.group(1))
        month = RUSSIAN_MONTHS[month_match.group(2)]
        year = int(month_match.group(3)) if month_match.group(3) else now.year
        try:
            parsed = date(year, month, day)
            if not month_match.group(3) and parsed < now.date():
                parsed = date(year + 1, month, day)
            return parsed
        except ValueError:
            return None

    return None


def parse_relative_datetime(text: str, now: datetime) -> ParsedDateContext:
    normalized = text.lower()
    parsed_time = extract_time(normalized)
    base_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    absolute_date = extract_absolute_date(normalized, now)
    if absolute_date is not None:
        base_date = absolute_date
        start_date = end_date = absolute_date

    if "сегодня" in normalized:
        base_date = now.date()
        start_date = end_date = base_date
    elif "послезавтра" in normalized:
        base_date = now.date() + timedelta(days=2)
        start_date = end_date = base_date
    elif "завтра" in normalized:
        base_date = now.date() + timedelta(days=1)
        start_date = end_date = base_date
    elif absolute_date is None:
        day_match = re.search(r"через\s+(\d+)\s+(дн(?:я|ей)?|сут(?:ок|ки)?)", normalized)
        if day_match:
            base_date = now.date() + timedelta(days=int(day_match.group(1)))
            start_date = end_date = base_date

        week_match = re.search(r"через\s+(\d+)\s+недел(?:ю|и|ь)", normalized)
        if week_match:
            base_date = now.date() + timedelta(days=int(week_match.group(1)) * 7)
            start_date = end_date = base_date
        elif "через неделю" in normalized:
            base_date = now.date() + timedelta(days=7)
            start_date = end_date = base_date

        month_match = re.search(r"через\s+(\d+)\s+месяц(?:а|ев)?", normalized)
        if month_match:
            base_date = now.date() + timedelta(days=int(month_match.group(1)) * 30)
            start_date = end_date = base_date
        elif "через месяц" in normalized:
            base_date = now.date() + timedelta(days=30)
            start_date = end_date = base_date

    if "на этой неделе" in normalized or "на неделе" in normalized:
        start_date = _start_of_week(now.date())
        end_date = _end_of_week(now.date())
        base_date = start_date
    elif "на следующей неделе" in normalized:
        next_week = now.date() + timedelta(days=7)
        start_date = _start_of_week(next_week)
        end_date = _end_of_week(next_week)
        base_date = start_date

    weekday_match = re.search(
        r"\b(?:в|на)\s+(понедельник(?:а)?|вторник(?:а)?|сред(?:а|у|ы)|четверг(?:а)?|пятниц(?:а|у|ы)|суббот(?:а|у|ы)|воскресень(?:е|я)|пн|вт|ср|чт|пт|сб|вс)\b",
        normalized,
    )
    if weekday_match:
        weekday_text = weekday_match.group(1)
        weekday = WEEKDAY_ALIASES.get(weekday_text)
        if weekday is not None:
            base_date = _next_weekday(now.date(), weekday)
            start_date = end_date = base_date

    due_at = None
    if base_date is not None:
        due_at = datetime.combine(base_date, parsed_time or time(hour=23, minute=59))

    return ParsedDateContext(
        due_at=due_at,
        start_date=start_date,
        end_date=end_date,
        has_explicit_time=parsed_time is not None,
    )


def build_relative_date_hints(text: str, now: datetime) -> str:
    parsed = parse_relative_datetime(text, now)
    hints = [
        f"Текущая локальная дата и время: {now.strftime('%Y-%m-%d %H:%M')}",
        f"Сегодня: {now.strftime('%Y-%m-%d')}",
        f"Завтра: {(now.date() + timedelta(days=1)).isoformat()}",
        f"Послезавтра: {(now.date() + timedelta(days=2)).isoformat()}",
        f"Эта неделя: {_start_of_week(now.date()).isoformat()} .. {_end_of_week(now.date()).isoformat()}",
        f"Следующая неделя: {_start_of_week(now.date() + timedelta(days=7)).isoformat()} .. {_end_of_week(now.date() + timedelta(days=7)).isoformat()}",
    ]
    if parsed.due_at is not None:
        hints.append(f"Для этой фразы локально распознана дата/время-подсказка: {parsed.due_at.strftime('%Y-%m-%d %H:%M')}")
    elif parsed.start_date is not None and parsed.end_date is not None:
        hints.append(f"Для этой фразы локально распознан период-подсказка: {parsed.start_date.isoformat()} .. {parsed.end_date.isoformat()}")
    return "\n".join(hints)
