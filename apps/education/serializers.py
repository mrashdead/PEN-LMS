from __future__ import annotations

import re

from django.db import transaction
from rest_framework import serializers

from apps.core.fields import JalaliDateField, PersianCharField
from apps.core.serializers import CRUDActionsMixin
from apps.core.utils import jalali_date_str, persian_date
from apps.persons.models import Person
from apps.education.models import (
    AcademicHoliday,
    AttendanceRecord,
    ClassSession,
    Course,
    CourseLesson,
    CourseOffering,
    Department,
    GradeRecord,
    Lesson,
    Location,
    OfferingEnrollment,
    EnrollmentWaitlist,
    EnrollmentRefund,
    SessionMaterial,
)
from apps.leads.models import Lead

#: Recurrence-rule validation mirrors apps.education.services._DAY_KEYS.
_VALID_DAYS = frozenset({"sat", "sun", "mon", "tue", "wed", "thu", "fri"})
_HHMM_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
#: Business keys (of-XXXX / CLS-PY-01) — same grammar as models._BUSINESS_CODE_RE.
_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class AcademicHolidaySerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    date_from = JalaliDateField()
    date_to = JalaliDateField()

    class Meta:
        model = AcademicHoliday
        fields = ("id", "name", "scope", "date_from", "date_to", "weekday",
                  "all_day", "location", "note", "is_active", "legacy_id",
                  "created_at", "updated_at", "actions")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        if attrs.get("scope") == AcademicHoliday.Scope.WEEKLY and attrs.get("weekday") is None:
            raise serializers.ValidationError(
                {"weekday": "برای تعطیل هفتگی، روز هفته را مشخص کنید."}
            )
        start = attrs.get("date_from")
        end = attrs.get("date_to")
        if start and end and end < start:
            raise serializers.ValidationError(
                {"date_to": "پایان بازه نمی‌تواند پیش از شروع باشد."}
            )
        return attrs


class DepartmentSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = ("id", "code", "name", "description", "parent", "is_active", "legacy_id",
                  "created_at", "updated_at", "actions")
        read_only_fields = ("created_at", "updated_at")


class LocationSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    class Meta:
        model = Location
        fields = ("id", "code", "name", "building", "capacity", "equipment",
                  "is_active", "legacy_id")
        fields = fields + ("created_at", "updated_at", "actions")
        read_only_fields = ("created_at", "updated_at")


class LessonSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Lesson.objects.all(), required=False
    )

    class Meta:
        model = Lesson
        fields = ("id", "code", "title", "title_en", "description", "syllabus",
                  "duration_hours", "audience_age",
                  "space_type", "department", "prerequisites",
                  "required_equipment", "learning_resources", "tuition",
                  "is_active", "version", "legacy_id", "created_at", "updated_at")
        fields = fields + ("actions",)
        # code is auto-generated (ls-0001) on save — never client-supplied.
        read_only_fields = ("id", "code", "created_at", "updated_at", "version")


class CourseLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ("id", "course", "lesson", "order", "required", "hours")


class CourseLessonsField(serializers.Field):
    def get_attribute(self, instance):
        # خودِ نمونه به to_representation داده می‌شود: «درس‌ها» باید از سرفصل
        # زنده خوانده شود (``instance.lesson_links``)، نه از مدیر M2M که
        # لینک‌های soft-deleted را هم برمی‌گرداند.
        return instance

    def to_representation(self, course) -> list:
        return [str(link.lesson_id) for link in course.lesson_links]

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("lessons باید فهرستی از شناسه‌ها باشد.")
        values = []
        for item in data:
            try:
                values.append(str(item))
            except Exception as exc:  # pragma: no cover
                raise serializers.ValidationError("شناسه درس نامعتبر است.") from exc
        return values


class CourseSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    # lessons is the M2M through CourseLesson — DRF can't write a through-M2M
    # directly, so we accept a flat id list and manage rows in create/update.
    lessons = CourseLessonsField(required=False)
    lesson_titles = serializers.SerializerMethodField()
    total_tuition = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "code", "title", "description", "objectives",
                  "department", "tuition", "lessons", "lesson_titles",
                  "total_tuition", "is_active", "legacy_id", "created_at", "updated_at")
        fields = fields + ("actions",)
        read_only_fields = ("id", "code", "created_at", "updated_at")

    def get_lesson_titles(self, obj) -> list:
        return [
            {"id": str(link.lesson_id), "title": link.lesson.title,
             "tuition": (link.lesson.tuition or 0) if link.lesson_id else 0}
            for link in obj.lesson_links
        ]

    def get_total_tuition(self, obj) -> int:
        """Sum of the linked lessons' tuition (the course bundle price)."""
        return sum(
            (link.lesson.tuition or 0) for link in obj.lesson_links if link.lesson_id
        )

    def _sync_lessons(self, course, lesson_ids) -> bool:
        """Apply only the curriculum delta of a course (idempotent).

        The form always posts the whole lesson list, so the sync must be a
        *diff*, never a rebuild: the old delete-then-recreate left soft-deleted
        ``CourseLesson`` rows behind on every save, and Django's M2M manager
        joins the through table without its soft-delete filter — the same
        lesson then showed up twice in «درس‌ها»/«شهریهٔ کل» and in every
        offering/price built from the course.

        Returns True when the curriculum actually changed, so ``update()`` can
        skip the write entirely when it did not.
        """
        # Order matters (it is the curriculum order) and duplicates in the
        # payload must never create two rows for the same lesson.
        wanted = list(dict.fromkeys(str(pk) for pk in lesson_ids or []))
        alive_pks = {
            str(pk)
            for pk in Lesson.objects.filter(pk__in=wanted).values_list("pk", flat=True)
        }
        wanted = [pk for pk in wanted if pk in alive_pks]

        links = {str(link.lesson_id): link for link in course.lesson_links}
        if wanted == list(links):
            return False

        position = {pk: index for index, pk in enumerate(wanted, start=1)}
        # ۱) لینک‌های حذف‌شده یا جابه‌جاشده اول (و فیزیکی) پاک می‌شوند: حذف
        # منطقی دوباره در مدیر M2M ظاهر می‌شود و شماره‌گذاری درجا هم با
        # محدودیت یکتای (course, order) برخورد می‌کند.
        doomed = [
            link.pk for pk, link in links.items()
            if position.get(pk) != link.order
        ]
        doomed_set = set(doomed)
        if doomed:
            CourseLesson.all_objects.filter(pk__in=doomed).delete()

        # ۲) فقط لینک‌هایی ساخته می‌شوند که جای درست ندارند.
        for pk, order in position.items():
            link = links.get(pk)
            if link is not None and link.pk not in doomed_set:
                continue
            CourseLesson.objects.create(course=course, lesson_id=pk, order=order)
        return True

    @transaction.atomic
    def create(self, validated_data):
        lesson_ids = validated_data.pop("lessons", [])
        course = Course.objects.create(**validated_data)
        self._sync_lessons(course, lesson_ids)
        return course

    @transaction.atomic
    def update(self, instance, validated_data):
        """Write only what really changed (انجام فقط تغییرات واقعی).

        Nothing changed → no write at all; a lessons-only change touches only
        the link rows (plus the course's ``updated_at``), never re-creating
        rows that are already correct.
        """
        lesson_ids = validated_data.pop("lessons", None)

        changed = {
            field: value for field, value in validated_data.items()
            if getattr(instance, field, None) != value
        }
        if changed:
            for field, value in changed.items():
                setattr(instance, field, value)
            instance.save(update_fields=[*changed, "updated_at"])

        if lesson_ids is not None and self._sync_lessons(instance, lesson_ids) and not changed:
            # The curriculum changed but no course field did: keep the record's
            # modification time honest without rewriting the row.
            instance.save(update_fields=["updated_at"])
        return instance


class CourseOfferingSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    seats_left = serializers.IntegerField(read_only=True, allow_null=True)
    seats_left_display = serializers.CharField(read_only=True)
    start_date = JalaliDateField(required=False, allow_null=True)
    end_date = JalaliDateField(required=False, allow_null=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_tuition = serializers.SerializerMethodField()
    lesson_titles = serializers.SerializerMethodField()
    classes = serializers.SerializerMethodField()
    location_name = serializers.CharField(source="location.name", read_only=True,
                                          default="")
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = ("id", "course", "course_title", "course_tuition", "code", "title",
                  "department", "capacity", "enrolled_count", "seats_left",
                  "seats_left_display", "start_date", "end_date", "location",
                  "location_name", "instructor", "instructor_name", "schedule",
                  "total_sessions", "auto_skip_holidays",
                  "lesson_titles", "status", "classes",
                  "tuition", "is_active", "legacy_id", "created_at", "updated_at", "actions")
        read_only_fields = ("id", "created_at", "updated_at", "enrolled_count",
                            "classes")

    def get_instructor_name(self, obj) -> str:
        t = getattr(obj, "instructor", None)
        return f"{t.first_name} {t.last_name}".strip() if t else ""

    def get_course_tuition(self, obj) -> int:
        """Use the curriculum total when the legacy course amount is unset."""
        course = getattr(obj, "course", None)
        if course is None:
            return int(obj.tuition or 0)
        total = sum(int(link.lesson.tuition or 0) for link in course.lesson_links)
        return int(obj.tuition or course.tuition or total or 0)

    def get_lesson_titles(self, obj) -> list:
        """The offering's course lessons — shown read-only in the offering form."""
        course = getattr(obj, "course", None)
        if course is None:
            return []
        return [
            {"id": str(link.lesson_id), "title": link.lesson.title,
             "tuition": (link.lesson.tuition or 0) if link.lesson_id else 0}
            for link in course.lesson_links
        ]

    def get_classes(self, obj) -> list:
        """Formed classes under this offering (فرم تشکیل کلاس) — grouped rows."""
        request = self.context.get("request")
        return classes_of_offering(obj, user=request.user if request else None)

    def validate_code(self, value: str) -> str:
        """Alive-unique, exact-cased business key (the DB constraint is the
        final arbiter; this turns a race into a clean field error)."""
        code = (value or "").strip()
        if not code:
            return ""          # save() auto-fills of-0001
        clash = CourseOffering.objects.filter(code=code, is_deleted=False)
        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("این کد برگزاری قبلاً استفاده شده است.")
        return code

    def validate_total_sessions(self, value: int) -> int:
        if value and value > 200:
            raise serializers.ValidationError(
                "تعداد جلسات نمی‌تواند از ۲۰۰ بیشتر باشد."
            )
        return value

    def validate_schedule(self, value: dict) -> dict:
        """Fail fast on a malformed recurrence rule (the engine raises later)."""
        return validate_schedule_payload(value)


#: Shared recurrence-rule validator: the offering form and the class-formation
#: form both post {days:[sat..fri], start:"HH:MM", end:"HH:MM"}.
def validate_schedule_payload(value: dict, *, required: bool = False) -> dict:
    if value in (None, {}):
        if required:
            raise serializers.ValidationError(
                "روزها و ساعت شروع/پایان برگزاری را مشخص کنید."
            )
        return value or {}
    days = value.get("days") or []
    if not isinstance(days, list) or any(d not in _VALID_DAYS for d in days):
        raise serializers.ValidationError(
            "days باید فهرستی از " + "/".join(sorted(_VALID_DAYS)) + " باشد."
        )
    for key in ("start", "end"):
        text = str(value.get(key) or "")
        if text and not _HHMM_RE.match(text):
            raise serializers.ValidationError({key: "قالب ساعت باید HH:MM باشد."})
    if value.get("start") and value.get("end") and value["end"] <= value["start"]:
        raise serializers.ValidationError("ساعت پایان باید بعد از شروع باشد.")
    return value


def classes_of_offering(offering, *, user=None) -> list:
    """
    The classes formed inside one offering (grouped by class_code), newest
    form first. Powers the offering detail page and the «مدیریت جلسات» table.
    """
    from django.db.models import Count, Min, Max

    sessions = ClassSession.objects.filter(offering=offering, is_deleted=False)
    if user is not None:
        from apps.academics.scoping import education_sessions_visible_to

        sessions = education_sessions_visible_to(user).filter(offering=offering)

    rows = (
        sessions
        .values("class_code", "lesson", "lesson__title", "teacher",
                "location")
        .annotate(
            session_count=Count("id", distinct=True),
            first_date=Min("session_date"),
            last_date=Max("session_date"),
            first_number=Min("session_number"),
            last_number=Max("session_number"),
        )
        .order_by("class_code")
    )
    out = []
    for r in rows:
        teacher = Person.objects.filter(pk=r["teacher"]).first() if r["teacher"] else None
        lesson = Lesson.objects.filter(pk=r["lesson"]).first() if r["lesson"] else None
        out.append({
            "class_code": r["class_code"] or "—",
            "lesson_id": r["lesson"],
            "lesson_title": lesson.title if lesson else (r["lesson__title"] or ""),
            "teacher_id": r["teacher"],
            "teacher_name": f"{teacher.first_name} {teacher.last_name}".strip() if teacher else "",
            "location_id": r["location"],
            "sessions": r["session_count"],
            "first_number": r["first_number"],
            "last_number": r["last_number"],
            "first_date": jalali_date_str(r["first_date"]),
            "last_date": jalali_date_str(r["last_date"]),
        })
    return out


class ClassSessionSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    actions = serializers.SerializerMethodField()
    session_date = JalaliDateField()
    offering_title = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source="lesson.title", read_only=True,
                                         default="")
    teacher_name = serializers.SerializerMethodField()
    location_name = serializers.CharField(source="location.name", read_only=True,
                                          default="")
    materials = serializers.SerializerMethodField()
    schedule_version = serializers.SerializerMethodField()
    schedule_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = ("id", "offering", "offering_title", "class_group", "class_code",
                  "lesson", "lesson_title", "session_number",
                  "title", "topic", "session_date", "start_time", "end_time", "teacher",
                  "teacher_name", "location", "location_name", "status",
                  "materials", "schedule_version", "schedule_updated_at",
                  "legacy_id", "created_at", "updated_at", "actions")
        # session_number stays writable (the generator supplies 1..N; a manual
        # create may pin one) — validate() pre-checks it against the
        # (offering, class_code, session_number) alive-unique constraint.
        read_only_fields = ("created_at", "updated_at")

    def get_offering_title(self, obj) -> str:
        off = obj.offering
        if off is None:
            return ""
        code = getattr(off, "code", "") or ""
        title = off.title or getattr(off.course, "title", "") or ""
        return f"{code} — {title}".strip(" —") if code else title

    def get_teacher_name(self, obj) -> str:
        t = obj.teacher
        return f"{t.first_name} {t.last_name}".strip() if t else ""

    def get_materials(self, obj) -> list[dict]:
        return SessionMaterialSerializer(
            obj.materials.filter(is_deleted=False, is_visible=True), many=True,
            context=self.context,
        ).data

    def get_schedule_version(self, obj) -> int:
        return obj.schedule_revisions.filter(is_deleted=False).count() + 1

    def get_schedule_updated_at(self, obj) -> str:
        latest = obj.schedule_revisions.filter(is_deleted=False).order_by("-version").first()
        stamp = latest.created_at if latest else obj.updated_at
        return stamp.isoformat() if stamp else ""

    def validate(self, attrs):
        # Class create/edit paths must not fight the generator's numbering.
        offering = attrs.get("offering") or (self.instance.offering if self.instance else None)
        class_code = attrs.get("class_code", getattr(self.instance, "class_code", "") if self.instance else "")
        number = attrs.get("session_number")
        if offering is not None and number:
            clash = ClassSession.objects.filter(
                offering=offering, class_code=(class_code or "").strip(),
                session_number=number, is_deleted=False,
            )
            if self.instance is not None:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {"session_number": "این شماره جلسه در این کلاس قبلاً ثبت شده است."}
                )
        return attrs



class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ("id", "session", "student", "status", "note",
                  "recorded_by", "created_at")
        read_only_fields = ("created_at",)


class SessionMaterialSerializer(serializers.ModelSerializer):
    public_url = serializers.ReadOnlyField()

    class Meta:
        model = SessionMaterial
        fields = (
            "id", "session", "title", "kind", "url", "file", "public_url",
            "sort_order", "is_visible", "created_at", "updated_at",
        )
        read_only_fields = ("id", "public_url", "created_at", "updated_at")

    def validate(self, attrs):
        if not attrs.get("url") and not attrs.get("file"):
            raise serializers.ValidationError("برای ضمیمه، پیوند یا فایل را وارد کنید.")
        return attrs


class EnrollmentWaitlistSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    offering_title = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    requested_at = serializers.DateTimeField(read_only=True)
    offered_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = EnrollmentWaitlist
        fields = (
            "id", "offering", "offering_title", "student", "student_name",
            "status", "position", "requested_at", "offered_at", "responded_at",
            "note", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "status", "position", "requested_at", "offered_at",
            "created_at", "updated_at",
        )

    def get_student_name(self, obj) -> str:
        return obj.student.display_name

    def get_offering_title(self, obj) -> str:
        return obj.offering.title or (obj.offering.course.title if obj.offering.course_id else "")

    def get_position(self, obj) -> int | None:
        if obj.status not in {EnrollmentWaitlist.Status.WAITING, EnrollmentWaitlist.Status.OFFERED}:
            return None
        return EnrollmentWaitlist.objects.filter(
            offering=obj.offering, status=EnrollmentWaitlist.Status.WAITING,
            is_deleted=False, requested_at__lte=obj.requested_at,
        ).count()


class GradeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeRecord
        fields = ("id", "student", "session", "offering", "lesson", "result",
                  "teacher_note", "evaluated_by", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class OfferingEnrollmentSerializer(CRUDActionsMixin, serializers.ModelSerializer):
    lead = serializers.PrimaryKeyRelatedField(
        queryset=Lead.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
        write_only=True,
    )
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)
    offering_title = serializers.CharField(source="offering.title", read_only=True)
    enrolled_at = JalaliDateField(required=False)
    final_class_enrollment_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = OfferingEnrollment
        fields = ("id", "offering", "offering_title", "student", "student_name",
                  "course_amount", "discount_type", "discount_value", "final_amount",
                  "payment_method", "cheque_count", "cheques", "reference",
                  "enrolled_at", "is_active", "lifecycle_status",
                  "final_class_enrollment_id", "created_at", "updated_at", "lead")
        read_only_fields = (
            "id", "final_amount", "lifecycle_status", "final_class_enrollment_id",
            "created_at", "updated_at",
        )

    def validate(self, attrs):
        # Mirror the model's single rule so the API returns field errors, not 500.
        offering = attrs.get("offering") or (self.instance.offering if self.instance else None)
        student = attrs.get("student") or (self.instance.student if self.instance else None)
        if offering is not None and student is not None:
            course_amount = attrs.get("course_amount")
            if course_amount in (None, 0):
                attrs["course_amount"] = sum(
                    link.lesson.tuition or 0 for link in offering.course.lesson_links
                )
        lead = attrs.get("lead")
        if lead is not None:
            if lead.status not in (Lead.Status.RECOMMENDED, Lead.Status.ASSESSED):
                raise serializers.ValidationError({"lead": "این لید هنوز برای ثبت‌نام آماده نیست."})
            if lead.enrolled_person_id and student is not None and lead.enrolled_person_id != student.pk:
                raise serializers.ValidationError({"lead": "این لید قبلاً به دانش‌آموز دیگری متصل شده است."})
        dt = attrs.get("discount_type", getattr(self.instance, "discount_type", "none"))
        dv = attrs.get("discount_value", getattr(self.instance, "discount_value", 0)) or 0
        if dt == OfferingEnrollment.DiscountType.PERCENT and dv > 100:
            raise serializers.ValidationError({"discount_value": "درصد تخفیف نمی‌تواند بیش از ۱۰۰ باشد."})
        pm = attrs.get("payment_method", getattr(self.instance, "payment_method", "cash"))
        cheques = attrs.get("cheques", getattr(self.instance, "cheques", []))
        if pm == OfferingEnrollment.PaymentMethod.CHEQUE and not cheques:
            raise serializers.ValidationError({"cheques": "برای پرداخت چک، حداقل یک چک وارد کنید."})
        # compute final_amount server-side (never trust client)
        base = attrs.get("course_amount", getattr(self.instance, "course_amount", 0)) or 0
        if dt == OfferingEnrollment.DiscountType.PERCENT:
            attrs["_final"] = base - int(round(base * min(max(dv, 0), 100) / 100))
        elif dt == OfferingEnrollment.DiscountType.AMOUNT:
            attrs["_final"] = max(base - dv, 0)
        else:
            attrs["_final"] = base
        return attrs


class EnrollmentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrollmentRefund
        fields = (
            "id", "enrollment", "amount", "status", "reason", "reference",
            "requested_by", "processed_by", "processed_at", "metadata",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "status", "requested_by", "processed_by", "processed_at",
            "created_at", "updated_at",
        )

    def create(self, validated_data):
        final = validated_data.pop("_final", 0)
        validated_data.pop("lead", None)
        validated_data["final_amount"] = final
        return super().create(validated_data)

    def update(self, instance, validated_data):
        final = validated_data.pop("_final", None)
        if final is not None:
            validated_data["final_amount"] = final
        return super().update(instance, validated_data)


# ═════════════════════════════════════════════════════════════════════════
# «تشکیل کلاس» (class formation) — command serializer over the service layer
# ═════════════════════════════════════════════════════════════════════════

class ClassFormationSerializer(serializers.Serializer):
    """
    Form 2 payload. teacher/location/start_date/schedule may be omitted —
    the offering's PROPOSED values fill them (client-side auto-fill stays
    editable; the server re-applies the same defaults so raw API posts
    behave identically). ``count`` omitted → derived from the lesson's hours
    ÷ session length (مدت ÷ طول جلسه). ``create`` runs the atomic engine.
    """

    offering = serializers.UUIDField()
    class_code = serializers.CharField(max_length=64, required=False, allow_blank=True,
                                       default="")
    lesson = serializers.UUIDField()
    teacher = serializers.UUIDField(required=False, allow_null=True)
    location = serializers.UUIDField(required=False, allow_null=True)
    start_date = JalaliDateField(required=False, allow_null=True)
    schedule = serializers.DictField(required=False)
    count = serializers.IntegerField(required=False, min_value=1, max_value=200)
    skip_holidays = serializers.BooleanField(required=False)
    strict = serializers.BooleanField(required=False, default=False)
    regenerate = serializers.BooleanField(required=False, default=False)

    def validate_offering(self, value):
        offering = CourseOffering.objects.filter(pk=value, is_deleted=False).first()
        if offering is None:
            raise serializers.ValidationError("برگزاری دوره یافت نشد.")
        return offering

    def validate_class_code(self, value):
        code = (value or "").strip()
        if code and not _CODE_RE.match(code):
            raise serializers.ValidationError(
                "کد کلاس فقط می‌تواند شامل حروف لاتین، رقم، «-»، «_» یا «.» باشد."
            )
        return code

    def validate_lesson(self, value):
        lesson = Lesson.objects.filter(pk=value, is_deleted=False).first()
        if lesson is None:
            raise serializers.ValidationError("درس یافت نشد.")
        return lesson

    def validate_teacher(self, value):
        if value is None:
            return None
        person = Person.objects.filter(
            pk=value, is_deleted=False, is_active=True,
        ).first()
        if person is None or not person.has_type("teacher"):
            raise serializers.ValidationError("استاد انتخابی فعال نیست.")
        return person

    def validate_location(self, value):
        if value is None:
            return None
        loc = Location.objects.filter(pk=value, is_deleted=False, is_active=True).first()
        if loc is None:
            raise serializers.ValidationError("فضای انتخابی یافت نشد یا غیرفعال است.")
        return loc

    def validate_schedule(self, value):
        return validate_schedule_payload(value)

    def create(self, validated_data):
        from apps.education.class_formation import form_class

        offering = validated_data.pop("offering")
        # schedule={} → explicit "use the offering's proposal" (None override).
        schedule = validated_data.pop("schedule", None) or None
        request = self.context.get("request")
        return form_class(
            offering=offering, schedule=schedule,
            actor=getattr(request, "user", None),
            **validated_data,
        )
