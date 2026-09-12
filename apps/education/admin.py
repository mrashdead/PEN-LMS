from __future__ import annotations

from django.contrib import admin

from apps.education.models import (
    AttendanceRecord,
    ClassSession,
    Course,
    CourseLesson,
    CourseOffering,
    Department,
    GradeRecord,
    Lesson,
    Location,
)

admin.site.register(Department)
admin.site.register(Location)
admin.site.register(Lesson)
admin.site.register(Course)
admin.site.register(CourseLesson)
admin.site.register(CourseOffering)
admin.site.register(ClassSession)
admin.site.register(AttendanceRecord)
admin.site.register(GradeRecord)
