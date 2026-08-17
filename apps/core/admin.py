from __future__ import annotations

from django.contrib import admin

from apps.core.utils import persian_date, persian_numbers


class JalaliAdminMixin:
    """
    Mixin for Django admin to show Jalali (Shamsi) dates.
    Add this mixin to any ModelAdmin to get Jalali date display.
    """

    @admin.display(description="تاریخ ایجاد (شمسی)")
    def created_at_jalali_display(self, obj):
        if hasattr(obj, "created_at"):
            return persian_date(obj.created_at)
        return ""

    @admin.display(description="تاریخ بروزرسانی (شمسی)")
    def updated_at_jalali_display(self, obj):
        if hasattr(obj, "updated_at"):
            return persian_date(obj.updated_at)
        return ""

    @staticmethod
    def persian(val):
        """تبدیل اعداد به فارسی برای نمایش در ادمین."""
        if val is None:
            return ""
        return persian_numbers(str(val))
