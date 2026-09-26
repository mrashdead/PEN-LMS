"""Shared query selector for workflow requests and their form submissions."""
from __future__ import annotations

import uuid

from django.db.models import Count, IntegerField, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.functions import Coalesce

from apps.reports.permissions import REPORT_ACCESS_ROLES
from apps.reports.selectors.reports import ReportFilterError, ReportFilters, _parse_report_date


REPORT_VIEWER_ROLES = REPORT_ACCESS_ROLES
REVIEW_ACTIONS = ("approve", "approved", "reject", "rejected", "return", "review", "request_changes")


def _user_filter(queryset, prefix: str, value: str):
    try:
        user_id = uuid.UUID(value)
    except (ValueError, TypeError, AttributeError):
        return queryset.filter(**{f"{prefix}__username__iexact": value})
    return queryset.filter(**{f"{prefix}_id": user_id})


def workflow_report_queryset(query, *, user=None):
    """Build the filtered, prefetched request report queryset.

    Workflow instances remain the compatibility root so requests created by
    legacy workflow callers stay reportable; linked FormSubmission/Request
    records enrich the same rows rather than creating duplicate report rows.
    """
    from apps.forms.models import FormSubmission
    from apps.tasks.models import WorkflowTask
    from apps.workflow.models import ActionLog, Instance

    qs = Instance.objects.filter(is_deleted=False)
    if user is not None and not (set(user.role_codes()) & REPORT_VIEWER_ROLES):
        qs = qs.filter(Q(requester=user) | Q(tasks__assignee=user))

    raw_start = query.get("from") or query.get("date_from")
    raw_end = query.get("to") or query.get("date_to")
    period = str(query.get("period") or "").strip().lower()
    if period:
        date_query = {"period": period}
        if raw_start:
            date_query["from"] = raw_start
        if raw_end:
            date_query["to"] = raw_end
        date_range = ReportFilters.from_query(date_query)
        start, end = date_range.start, date_range.end
    else:
        start = _parse_report_date(raw_start) if raw_start else None
        end = _parse_report_date(raw_end) if raw_end else None
        if start and end and end < start:
            raise ReportFilterError("تاریخ پایان باید بعد از تاریخ شروع باشد.")
        if start and end and (end - start).days > 366 * 5:
            raise ReportFilterError("بازهٔ گزارش نمی‌تواند بیشتر از پنج سال باشد.")
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    for key, field in (("workflow", "workflow_definition__code"), ("status", "status"), ("step", "current_state__code")):
        value = str(query.get(key) or "").strip()
        if value:
            qs = qs.filter(**{field: value})

    request_type = str(query.get("request_type") or "").strip()
    if request_type:
        qs = qs.filter(
            Q(form_submissions__business_request__request_type__code__iexact=request_type)
            | Q(form_submissions__form_schema__request_type__code__iexact=request_type)
        )

    request_status = str(query.get("request_status") or "").strip()
    if request_status:
        qs = qs.filter(
            Q(form_submissions__business_request__status__iexact=request_status)
            | Q(form_submissions__status__iexact=request_status)
        )

    form_slug = str(query.get("form") or "").strip()
    if form_slug:
        qs = qs.filter(form_submissions__form_schema__slug__iexact=form_slug)

    requester = str(query.get("requester") or "").strip()
    if requester:
        qs = _user_filter(qs, "requester", requester)

    assigned_to = str(query.get("assigned_to") or "").strip()
    if assigned_to:
        qs = _user_filter(
            qs.filter(tasks__status=WorkflowTask.Status.PENDING, tasks__is_deleted=False),
            "tasks__assignee",
            assigned_to,
        )

    user_query = str(query.get("user") or "").strip()
    if user_query:
        qs = qs.filter(
            Q(requester__username__icontains=user_query)
            | Q(tasks__assignee__username__icontains=user_query, tasks__status=WorkflowTask.Status.PENDING)
            | Q(action_logs__actor__username__icontains=user_query)
        )

    department = str(query.get("request_department") or "").strip()
    if department:
        qs = qs.filter(
            Q(requester__department__icontains=department)
            | Q(
                tasks__assignee__department__icontains=department,
                tasks__status=WorkflowTask.Status.PENDING,
                tasks__is_deleted=False,
            )
        )

    action_by = str(query.get("action_by") or "").strip()
    if action_by:
        qs = _user_filter(qs, "action_logs__actor", action_by)

    review_start = _parse_report_date(query.get("review_from")) if query.get("review_from") else None
    review_end = _parse_report_date(query.get("review_to")) if query.get("review_to") else None
    if review_start and review_end and review_end < review_start:
        raise ReportFilterError("تاریخ پایان بررسی باید بعد از تاریخ شروع باشد.")
    if review_start and review_end and (review_end - review_start).days > 366 * 5:
        raise ReportFilterError("بازهٔ بررسی نمی‌تواند بیشتر از پنج سال باشد.")
    review_query = {}
    if review_start:
        review_query["action_logs__created_at__date__gte"] = review_start
    if review_end:
        review_query["action_logs__created_at__date__lte"] = review_end
    if review_query:
        qs = qs.filter(
            action_logs__action__in=REVIEW_ACTIONS,
            action_logs__is_deleted=False,
            **review_query,
        )

    submissions = FormSubmission.objects.filter(is_deleted=False).select_related(
        "form_schema", "form_schema__request_type", "submitted_by", "reviewed_by",
        "business_request", "business_request__request_type",
    ).order_by("-created_at")
    pending_tasks = WorkflowTask.objects.filter(
        status=WorkflowTask.Status.PENDING,
        is_deleted=False,
    ).select_related("assignee").order_by("-created_at", "assignee__username")
    action_history = ActionLog.objects.filter(is_deleted=False).select_related(
        "actor", "from_state", "to_state",
    ).order_by("created_at", "pk")
    latest_review = ActionLog.objects.filter(
        instance_id=OuterRef("pk"), is_deleted=False, action__in=REVIEW_ACTIONS,
    ).order_by("-created_at")
    first_approval = ActionLog.objects.filter(
        instance_id=OuterRef("pk"), is_deleted=False, action__in=("approve", "approved"),
    ).order_by("created_at")
    first_rejection = ActionLog.objects.filter(
        instance_id=OuterRef("pk"), is_deleted=False, action__in=("reject", "rejected"),
    ).order_by("created_at")
    action_total = ActionLog.objects.filter(
        instance_id=OuterRef("pk"), is_deleted=False,
    ).order_by().values("instance_id").annotate(total=Count("id")).values("total")[:1]

    return qs.select_related(
        "workflow_definition", "current_state", "requester", "requester__person",
    ).annotate(
        last_reviewed_at=Subquery(latest_review.values("created_at")[:1]),
        approved_at=Subquery(first_approval.values("created_at")[:1]),
        rejected_at=Subquery(first_rejection.values("created_at")[:1]),
        action_count=Coalesce(
            Subquery(action_total, output_field=IntegerField()), Value(0), output_field=IntegerField(),
        ),
    ).prefetch_related(
        Prefetch("form_submissions", queryset=submissions, to_attr="report_submissions"),
        Prefetch("tasks", queryset=pending_tasks, to_attr="report_pending_tasks"),
        Prefetch("action_logs", queryset=action_history, to_attr="report_action_history"),
    ).distinct().order_by("-created_at", "-pk")
