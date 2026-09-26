"""Read-only serializers for report-specific projections."""
from __future__ import annotations

from rest_framework import serializers

from apps.workflow.models import Instance


def _user_label(user) -> str:
    person = getattr(user, "person", None)
    if person:
        return person.display_name
    return user.get_full_name() or user.username


class WorkflowRequestReportSerializer(serializers.ModelSerializer):
    workflow_code = serializers.CharField(source="workflow_definition.code", read_only=True)
    workflow_name = serializers.CharField(source="workflow_definition.name", read_only=True)
    current_step = serializers.CharField(source="current_state.name", read_only=True, allow_null=True)
    current_step_code = serializers.CharField(source="current_state.code", read_only=True, allow_null=True)
    requester_name = serializers.SerializerMethodField()
    requester_department = serializers.CharField(source="requester.department", read_only=True)
    assigned_to = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    assigned_department = serializers.SerializerMethodField()
    assigned_users = serializers.SerializerMethodField()
    request_number = serializers.SerializerMethodField()
    request_status = serializers.SerializerMethodField()
    request_type_code = serializers.SerializerMethodField()
    request_type_title = serializers.SerializerMethodField()
    form_title = serializers.SerializerMethodField()
    form_slug = serializers.SerializerMethodField()
    form_status = serializers.SerializerMethodField()
    form_submission_number = serializers.SerializerMethodField()
    form_submitted_at = serializers.SerializerMethodField()
    reviewed_at = serializers.SerializerMethodField()
    reviewed_by = serializers.SerializerMethodField()
    last_reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    approved_at = serializers.DateTimeField(read_only=True, allow_null=True)
    rejected_at = serializers.DateTimeField(read_only=True, allow_null=True)
    action_count = serializers.IntegerField(read_only=True)
    action_history = serializers.SerializerMethodField()

    class Meta:
        model = Instance
        fields = (
            "id", "tracking_number", "request_number", "workflow_code", "workflow_name",
            "title", "status", "request_status", "current_step", "current_step_code",
            "request_type_code", "request_type_title", "form_title", "form_slug",
            "form_status", "form_submission_number", "requester_name", "requester_department",
            "assigned_to", "assigned_to_name", "assigned_department", "assigned_users",
            "created_at", "form_submitted_at", "reviewed_at", "reviewed_by",
            "last_reviewed_at", "approved_at", "rejected_at", "action_count", "action_history",
        )

    @staticmethod
    def _submission(obj):
        submissions = getattr(obj, "report_submissions", None)
        if submissions is None:
            submissions = list(obj.form_submissions.select_related(
                "form_schema", "form_schema__request_type", "business_request__request_type",
                "reviewed_by",
            ).order_by("-created_at")[:1])
        return submissions[0] if submissions else None

    @staticmethod
    def _pending_tasks(obj):
        tasks = getattr(obj, "report_pending_tasks", None)
        if tasks is None:
            tasks = list(obj.tasks.filter(status="pending", is_deleted=False).select_related("assignee"))
        return tasks

    def get_requester_name(self, obj):
        return _user_label(obj.requester)

    def get_assigned_to(self, obj):
        tasks = self._pending_tasks(obj)
        return tasks[0].assignee.username if tasks else ""

    def get_assigned_to_name(self, obj):
        tasks = self._pending_tasks(obj)
        return _user_label(tasks[0].assignee) if tasks else ""

    def get_assigned_department(self, obj):
        tasks = self._pending_tasks(obj)
        return tasks[0].assignee.department if tasks else ""

    def get_assigned_users(self, obj):
        return [
            {
                "username": task.assignee.username,
                "name": _user_label(task.assignee),
                "department": task.assignee.department,
            }
            for task in self._pending_tasks(obj)
        ]

    def get_request_number(self, obj):
        submission = self._submission(obj)
        business_request = getattr(submission, "business_request", None) if submission else None
        return (
            getattr(business_request, "request_number", None)
            or getattr(submission, "submission_number", None)
            or obj.tracking_number
        )

    def get_request_status(self, obj):
        submission = self._submission(obj)
        business_request = getattr(submission, "business_request", None) if submission else None
        return getattr(business_request, "status", None) or getattr(submission, "status", "")

    def get_request_type_code(self, obj):
        submission = self._submission(obj)
        business_request = getattr(submission, "business_request", None) if submission else None
        request_type = getattr(business_request, "request_type", None)
        request_type = request_type or getattr(submission.form_schema, "request_type", None) if submission else request_type
        return getattr(request_type, "code", "")

    def get_request_type_title(self, obj):
        submission = self._submission(obj)
        business_request = getattr(submission, "business_request", None) if submission else None
        request_type = getattr(business_request, "request_type", None)
        request_type = request_type or getattr(submission.form_schema, "request_type", None) if submission else request_type
        return getattr(request_type, "title", "")

    def get_form_title(self, obj):
        submission = self._submission(obj)
        return submission.form_schema.title if submission else ""

    def get_form_slug(self, obj):
        submission = self._submission(obj)
        return submission.form_schema.slug if submission else ""

    def get_form_status(self, obj):
        submission = self._submission(obj)
        return submission.status if submission else ""

    def get_form_submission_number(self, obj):
        submission = self._submission(obj)
        return submission.submission_number if submission else ""

    def get_form_submitted_at(self, obj):
        submission = self._submission(obj)
        return submission.submitted_at if submission else None

    def get_reviewed_at(self, obj):
        submission = self._submission(obj)
        return submission.reviewed_at if submission else None

    def get_reviewed_by(self, obj):
        submission = self._submission(obj)
        return _user_label(submission.reviewed_by) if submission and submission.reviewed_by else ""

    def get_action_history(self, obj):
        history = getattr(obj, "report_action_history", None)
        if history is None:
            history = obj.action_logs.filter(is_deleted=False).select_related(
                "actor", "from_state", "to_state",
            ).order_by("created_at", "pk")
        return [
            {
                "action": item.action,
                "actor": item.actor.username,
                "actor_name": _user_label(item.actor),
                "from_state": item.from_state.name if item.from_state else "",
                "to_state": item.to_state.name if item.to_state else "",
                "comment": item.comment,
                "created_at": item.created_at,
            }
            for item in history
        ]
