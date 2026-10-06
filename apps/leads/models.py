from __future__ import annotations

import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models

from apps.core.models import DomainModel
from apps.education.models import Course, Lesson
from apps.persons.models import Person


class Lead(DomainModel):
    """A prospective learner moving through intake and placement assessment."""

    class Status(models.TextChoices):
        NEW = "new", "لید جدید"
        SENT = "sent", "ارسال‌شده برای استاد"
        ASSESSED = "assessed", "تعیین سطح‌شده"
        RECOMMENDED = "recommended", "دوره معرفی شد"
        ENROLLED = "enrolled", "ثبت‌نام‌شده"
        LOST = "lost", "بایگانی‌شده"

    code = models.CharField(max_length=24, unique=True, editable=False, db_index=True)
    student_name = models.CharField(max_length=200)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    neighborhood = models.CharField(max_length=160, blank=True, default="")
    father_job = models.CharField(max_length=160, blank=True, default="")
    mother_job = models.CharField(max_length=160, blank=True, default="")
    allergy_notes = models.TextField(blank=True, default="")

    assessment_date = models.DateField(null=True, blank=True, db_index=True)
    assessment_time = models.TimeField(null=True, blank=True)
    assessor = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_assessments",
    )
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    assessment_score = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    assessment_result = models.TextField(blank=True, default="")
    recommendation = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_leads")
    enrolled_person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_leads",
        limit_choices_to={"person_type": Person.Type.STUDENT},
    )

    class Meta:
        app_label = "leads"
        db_table = "leads_lead"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "assessment_date")),
            models.Index(fields=("phone", "status")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(assessment_score__isnull=True) | models.Q(assessment_score__lte=100),
                name="leads_score_lte_100",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"LD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.student_name}"

    @property
    def status_label(self):
        if self.status == "scheduled":
            return self.Status.SENT.label
        return self.get_status_display()
