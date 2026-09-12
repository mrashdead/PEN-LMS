"""
Workflow Serializers — تبدیل مدل‌های گردش کار به JSON و بالعکس

تمام تاریخ‌ها به صورت خودکار به شمسی (Persian/Jalali) نمایش داده می‌شوند.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.core.fields import PersianCharField
from apps.workflow.models import (
    ActionLog,
    ApprovalRecord,
    EntityWorkflow,
    Instance,
    Transition,
    WorkflowDefinition,
)


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    """سریالایزر تعریف فرآیند — خواندنی"""

    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)

    class Meta:
        model = WorkflowDefinition
        fields = ("id", "code", "name", "description", "is_active", "version", "created_at", "updated_at")


class InstanceListSerializer(serializers.ModelSerializer):
    """سریالایزر خلاصه Instance — برای لیست"""

    workflow_definition_code = serializers.SlugRelatedField(
        source="workflow_definition", slug_field="code", read_only=True
    )
    current_state_code = serializers.SlugRelatedField(
        source="current_state", slug_field="code", read_only=True, allow_null=True
    )
    requester_username = serializers.SlugRelatedField(
        source="requester", slug_field="username", read_only=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)

    class Meta:
        model = Instance
        fields = (
            "id",
            "workflow_definition_code",
            "current_state_code",
            "requester_username",
            "title",
            "description",
            "status",
            "created_at",
            "updated_at",
        )


class InstanceDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات Instance — برای نمایش تکی"""

    workflow_definition = WorkflowDefinitionSerializer(read_only=True)
    current_state_code = serializers.SlugRelatedField(
        source="current_state", slug_field="code", read_only=True, allow_null=True
    )
    requester_username = serializers.SlugRelatedField(
        source="requester", slug_field="username", read_only=True
    )
    task_count = serializers.SerializerMethodField()
    submission = serializers.SerializerMethodField()
    created_at = PersianCharField(source="created_at_jalali", read_only=True)
    updated_at = PersianCharField(source="updated_at_jalali", read_only=True)

    class Meta:
        model = Instance
        fields = (
            "id",
            "workflow_definition",
            "current_state_code",
            "requester_username",
            "title",
            "description",
            "status",
            "task_count",
            "submission",
            "created_at",
            "updated_at",
        )

    def get_task_count(self, obj) -> dict:
        from apps.tasks.models import WorkflowTask

        pending = WorkflowTask.objects.filter(instance=obj, status=WorkflowTask.Status.PENDING).count()
        total = WorkflowTask.objects.filter(instance=obj).count()
        return {"pending": pending, "total": total}

    def get_submission(self, obj) -> dict | None:
        """Resolve the linked FormSubmission (if any) for the request detail page.

        Read-only convenience: the UI shows the form data/attachments/comments
        inline instead of a bare link. Returns None when the instance is not a
        form-driven request. Uses the existing EntityWorkflow bridge; no new
        model, no write path.
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.forms.models import FormSubmission

        ct = ContentType.objects.get_for_model(FormSubmission)
        link = obj.entity_links.filter(content_type=ct).first()
        if link is None:
            return None
        submission = FormSubmission.objects.filter(pk=link.object_id).first()
        if submission is None:
            return None
        return {
            "id": str(submission.pk),
            "submission_number": submission.submission_number,
            "schema_slug": submission.form_schema.slug,
            "schema_title": submission.form_schema.title,
            "status": submission.status,
            "data": submission.data,
            "notes": submission.notes,
            "attachment_count": submission.attachments.count(),
            "detail_url": f"/forms/submissions/{submission.pk}/",
        }


class CreateInstanceSerializer(serializers.Serializer):
    """سریالایزر ساخت Instance جدید"""

    workflow_code = serializers.SlugField(
        help_text="کد WorkflowDefinition — مثلاً leave-request"
    )
    title = serializers.CharField(max_length=512, help_text="عنوان درخواست")
    description = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="توضیحات (اختیاری)",
    )


class TransitionSerializer(serializers.ModelSerializer):
    """سریالایزر Transition — برای نمایش اقدامات مجاز"""

    from_state_code = serializers.SlugRelatedField(
        source="from_state", slug_field="code", read_only=True
    )
    to_state_code = serializers.SlugRelatedField(
        source="to_state", slug_field="code", read_only=True
    )

    class Meta:
        model = Transition
        fields = (
            "id",
            "name",
            "from_state_code",
            "to_state_code",
            "allowed_role_codes",
            "requires_comment",
        )


class ExecuteTransitionSerializer(serializers.Serializer):
    """سریالایزر اجرای Transition"""

    transition_id = serializers.UUIDField(help_text="شناسه Transition مورد نظر")
    comment = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="کامنت (اختیاری)",
    )
    metadata = serializers.JSONField(
        required=False, default=dict,
        help_text="داده‌های اضافی (اختیاری)",
    )
    idempotency_key = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=200,
        help_text=(
            "کلید یکتای کلاینت برای double-click/retry — اجرای دوباره با همان "
            "کلید، وضعیت فعلی را بازمی‌گرداند نه خطا (§13-3)."
        ),
    )


class CancelInstanceSerializer(serializers.Serializer):
    """سریالایزر لغو Instance"""

    reason = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="دلیل لغو (اختیاری)",
    )


class CommentActionSerializer(serializers.Serializer):
    """سریالایزر مشترک عملیات معنایی (approve/reject/return/complete)."""

    comment = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="توضیح اقدام (برای برخی انتقال‌ها الزامی است).",
    )
    metadata = serializers.JSONField(
        required=False, default=dict,
        help_text="داده‌های اضافی (اختیاری)",
    )
    idempotency_key = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=200,
        help_text="کلید یکتای کلاینت برای replay-safe اجرا.",
    )


class SendCopySerializer(serializers.Serializer):
    """سریالایزر رونوشت (send_copy)."""

    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False,
        help_text="شناسه کاربران گیرنده‌ی رونوشت",
    )
    note = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=500,
        help_text="یادداشت همراه رونوشت",
    )


class DelegateSerializer(serializers.Serializer):
    """سریالایزر ارجاع/تفویض تسک."""

    recipient = serializers.UUIDField(help_text="شناسه کاربر گیرنده‌ی ارجاع")
    comment = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=500,
    )


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """سریالایزر رکورد تایید — چه کسی، با چه نقشی، کی، با چه توضیحی."""

    approver_username = serializers.SlugRelatedField(
        source="approver", slug_field="username", read_only=True
    )
    state_code = serializers.SlugRelatedField(
        source="state", slug_field="code", read_only=True, allow_null=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = ApprovalRecord
        fields = (
            "id", "instance", "action", "approver", "approver_username",
            "role_code", "unit", "state_code", "comment",
            "is_revoked", "revoked_at", "created_at",
        )
        read_only_fields = fields


class LinkEntitySerializer(serializers.Serializer):
    """سریالایزر اتصال موجودیت دامنه به Instance"""

    entity_type = serializers.CharField(
        help_text="app_label.model — مثلاً education.courseoffering"
    )
    entity_id = serializers.UUIDField(
        help_text="شناسه (PK) موجودیت دامنه"
    )


class EntityWorkflowSerializer(serializers.ModelSerializer):
    """سریالایزر EntityWorkflow — نمایش اتصال موجودیت به Instance"""

    content_type_name = serializers.StringRelatedField(
        source="content_type", read_only=True
    )

    class Meta:
        model = EntityWorkflow
        fields = (
            "id", "instance_id", "content_type",
            "content_type_name", "object_id", "created_at",
        )
        read_only_fields = ("created_at",)


class ActionLogSerializer(serializers.ModelSerializer):
    """سریالایزر تاریخچه اقدامات"""

    from_state_code = serializers.SlugRelatedField(
        source="from_state", slug_field="code", read_only=True, allow_null=True
    )
    to_state_code = serializers.SlugRelatedField(
        source="to_state", slug_field="code", read_only=True, allow_null=True
    )
    actor_username = serializers.SlugRelatedField(
        source="actor", slug_field="username", read_only=True
    )
    created_at = PersianCharField(source="created_at_jalali", read_only=True)

    class Meta:
        model = ActionLog
        fields = (
            "id",
            "action",
            "actor_username",
            "from_state_code",
            "to_state_code",
            "comment",
            "metadata",
            "created_at",
        )
        read_only_fields = fields