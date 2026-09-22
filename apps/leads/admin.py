from django.contrib import admin

from apps.leads.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("code", "student_name", "phone", "status", "assessment_date", "assessor")
    list_filter = ("status", "assessment_date")
    search_fields = ("code", "student_name", "phone", "neighborhood")
    raw_id_fields = ("assessor", "course", "lesson", "enrolled_person")
