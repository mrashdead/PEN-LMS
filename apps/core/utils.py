from __future__ import annotations

import datetime
from typing import Optional, Union

import jdatetime


def to_jalali_date(value: Optional[Union[datetime.date, jdatetime.date]]) -> Optional[jdatetime.date]:
    """تبدیل تاریخ میلادی به شمسی."""
    if value is None:
        return None
    if isinstance(value, jdatetime.date):
        return value
    try:
        return jdatetime.date.fromgregorian(date=value)
    except (ValueError, TypeError):
        return None


def to_jalali_datetime(value: Optional[Union[datetime.datetime, jdatetime.datetime]]) -> Optional[jdatetime.datetime]:
    """تبدیل تاریخ و زمان میلادی به شمسی."""
    if value is None:
        return None
    if isinstance(value, jdatetime.datetime):
        return value
    try:
        if isinstance(value, datetime.datetime):
            from django.utils import timezone
            if timezone.is_aware(value):
                value = timezone.localtime(value)
            return jdatetime.datetime.fromgregorian(datetime=value)
        return None
    except (ValueError, TypeError):
        return None


def gregorian_to_jalali(value: Optional[Union[datetime.date, datetime.datetime]]) -> Optional[Union[jdatetime.date, jdatetime.datetime]]:
    """تبدیل خودکار تاریخ یا تاریخ-زمان به شمسی."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return to_jalali_datetime(value)
    if isinstance(value, datetime.date):
        return to_jalali_date(value)
    return value


def jalali_date_str(value: Optional[Union[datetime.date, jdatetime.date]], fmt: str = "%Y/%m/%d") -> str:
    """قالب‌بندی تاریخ شمسی به صورت رشته."""
    j = to_jalali_date(value)
    if j is None:
        return ""
    return j.strftime(fmt)


def jalali_datetime_str(value: Optional[Union[datetime.datetime, jdatetime.datetime]], fmt: str = "%Y/%m/%d %H:%M") -> str:
    """قالب‌بندی تاریخ و زمان شمسی به صورت رشته."""
    j = to_jalali_datetime(value)
    if j is None:
        return ""
    return j.strftime(fmt)


def persian_numbers(value: Union[str, int, float, None]) -> str:
    """تبدیل اعداد انگلیسی به فارسی (۱۲۳ → ۱۲۳)."""
    if value is None:
        return ""
    text = str(value)
    persian_digits = {
        "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
        "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
    }
    for en, fa in persian_digits.items():
        text = text.replace(en, fa)
    return text


def english_numbers(value: Optional[str]) -> str:
    """تبدیل اعداد فارسی به انگلیسی (۱۲۳ → 123)."""
    if value is None:
        return ""
    text = str(value)
    persian_digits = {
        "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
        "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
        "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
        "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    }
    for fa, en in persian_digits.items():
        text = text.replace(fa, en)
    return text


def persian_date(value: Optional[Union[datetime.date, datetime.datetime]]) -> str:
    """
    نمایش تاریخ شمسی به صورت فارسی کامل.
    مثال: ۱۴۰۳/۰۶/۲۷ — ۱۷ شهریور ۱۴۰۳
    """
    j = gregorian_to_jalali(value)
    if j is None:
        return ""
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
    ]
    if isinstance(j, jdatetime.datetime):
        return persian_numbers(f"{j.year}/{j.month:02d}/{j.day:02d} — {j.day} {month_names[j.month - 1]} {j.year}")
    return persian_numbers(f"{j.year}/{j.month:02d}/{j.day:02d} — {j.day} {month_names[j.month - 1]} {j.year}")


def persian_time(value: Optional[datetime.datetime]) -> str:
    """نمایش ساعت به صورت فارسی."""
    j = to_jalali_datetime(value)
    if j is None:
        return ""
    return persian_numbers(j.strftime("%H:%M:%S"))
