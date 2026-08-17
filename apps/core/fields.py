from __future__ import annotations

from typing import Any, Optional

import jdatetime
from rest_framework import serializers

from apps.core.utils import english_numbers, persian_numbers, to_jalali_date, to_jalali_datetime


class JalaliDateField(serializers.DateField):
    """
    فیلد تاریخ شمسی برای DRF.
    ورودی: رشته تاریخ شمسی (۱۴۰۳/۰۶/۲۷ یا 1403/06/27)
    خروجی: رشته تاریخ شمسی
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("input_formats", ["%Y/%m/%d", "%Y-%m-%d"])
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        """تبدیل ورودی (شمسی) به شیء date میلادی برای ذخیره."""
        if data is None or data == "":
            if self.required:
                self.fail("required")
            return None

        data = str(data).strip()
        data = english_numbers(data)

        if not data:
            if self.required:
                self.fail("required")
            return None

        for fmt in self.input_formats:
            try:
                jalali_date = jdatetime.datetime.strptime(data, fmt).date()
                return jalali_date.togregorian()
            except (ValueError, TypeError):
                continue

        self.fail("invalid", format=", ".join(self.input_formats))

    def to_representation(self, value):
        """تبدیل تاریخ میلادی به رشته شمسی برای خروجی."""
        if value is None:
            return None
        j = to_jalali_date(value)
        if j is None:
            return None
        return persian_numbers(j.strftime("%Y/%m/%d"))


class JalaliDateTimeField(serializers.DateTimeField):
    """
    فیلد تاریخ و زمان شمسی برای DRF.
    ورودی: رشته تاریخ شمسی (۱۴۰۳/۰۶/۲۷ ۱۴:۳۰)
    خروجی: رشته تاریخ و زمان شمسی
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("input_formats", ["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"])
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        """تبدیل ورودی (شمسی) به datetime میلادی."""
        if data is None or data == "":
            if self.required:
                self.fail("required")
            return None

        data = str(data).strip()
        data = english_numbers(data)

        if not data:
            if self.required:
                self.fail("required")
            return None

        for fmt in self.input_formats:
            try:
                jalali_dt = jdatetime.datetime.strptime(data, fmt)
                greg_dt = jalali_dt.togregorian()
                if self.timezone:
                    greg_dt = greg_dt.replace(tzinfo=self.timezone)
                return greg_dt
            except (ValueError, TypeError):
                continue

        self.fail("invalid", format=", ".join(self.input_formats))

    def to_representation(self, value):
        """تبدیل datetime میلادی به رشته شمسی برای خروجی."""
        if value is None:
            return None
        j = to_jalali_datetime(value)
        if j is None:
            return None
        return persian_numbers(j.strftime("%Y/%m/%d %H:%M"))


class PersianCharField(serializers.CharField):
    """فیلد متنی با نمایش اعداد فارسی."""

    def to_representation(self, value):
        if value is None:
            return None
        return persian_numbers(str(value))
