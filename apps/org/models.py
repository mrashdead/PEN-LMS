"""
Organizational models.

The org UX persists ``Delegation`` (جانشینی) and sidebar visibility rules.
Everything else the org screens show (chart, effective permissions,
responsibilities, unit performance) is derived from existing models
(User.manager/department, Role/UserRole, Group permissions,
Workflow Transition.allowed_role_codes, WorkflowTask). Deriving instead of
duplicating keeps a single source of truth.
"""
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import DomainModel


class Delegation(DomainModel):
    """
    جانشینی: «از تاریخ X تا Y، مهدی جانشین سارا در کارتابل واحد آموزش است».

    - scope: کدام کارتابل/واحد (department string) یا کدام فرآیند (workflow
      code) — حداقل یکی لازم است تا دامنه روشن باشد.
    - status: فعال بودن جانشینی زمان‌محور است (valid_from/valid_to) + flag.
    - audit: created_by + timestamps از DomainModel؛ لغو با is_active=False
      و تاریخ/کاربر لغو ثبت می‌شود (بدون حذف).
    """

    principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_given",
        help_text="کسی که کارش به دیگری سپرده می‌شود (صاحب اصلی کارتابل).",
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="delegations_received",
        help_text="جانشین.",
    )
    department = models.CharField(
        max_length=128, blank=True, default="",
        help_text="واحد/دپارتمان مشمول (خالی = کل کارتابل).",
    )
    workflow_code = models.SlugField(
        max_length=64, blank=True, default="",
        help_text="اگر فقط یک فرآیند خاص مد نظر است (مثلاً leave-request).",
    )
    reason = models.CharField(max_length=255, blank=True, default="")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_delegations",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="revoked_delegations",
    )

    class Meta:
        app_label = "org"
        db_table = "org_delegation"
        verbose_name = "Delegation (جانشینی)"
        verbose_name_plural = "Delegations (جانشینی‌ها)"
        ordering = ("-valid_from",)
        indexes = [
            models.Index(fields=["principal", "is_active"]),
            models.Index(fields=["delegate", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.delegate_id} ⇐ {self.principal_id} [{self.valid_from:%Y-%m-%d}..{self.valid_to:%Y-%m-%d}]"

    def clean(self) -> None:
        if self.delegate_id and self.principal_id and self.delegate_id == self.principal_id:
            raise ValidationError({"delegate": "جانشین نمی‌تواند خودِ صاحب کار باشد."})
        if self.valid_to and self.valid_from and self.valid_to <= self.valid_from:
            raise ValidationError({"valid_to": "پایان باید بعد از شروع باشد."})
        if not (self.department or self.workflow_code):
            raise ValidationError(
                {"department": "حداقل یک دامنه (واحد یا فرآیند) مشخص کنید."}
            )

    @property
    def is_live(self) -> bool:
        now = timezone.now()
        return bool(
            self.is_active
            and self.valid_from and self.valid_from <= now
            and self.valid_to and self.valid_to >= now
        )


class ACLEntryType(models.TextChoices):
    """انواع منبعی که می‌توان روی آن دسترسی صریح (ACL) تعریف کرد."""

    PAGE = "page", "صفحه (workspace)"
    FORM = "form", "فرم داینامیک"
    MODEL = "model", "ماژول / Model"


class ACLVerb(models.TextChoices):
    """فعل‌های قابل اهدا در PersonACL."""

    VIEW = "view", "مشاهده"
    ADD = "add", "ایجاد"
    CHANGE = "change", "ویرایش"
    DELETE = "delete", "حذف"
    SUBMIT = "submit", "ارسال (submit)"
    APPROVE = "approve", "تأیید"
    REJECT = "reject", "رد"


class PersonACLEntry(DomainModel):
    """
    یک گرنت صریح (explicit grant) از یک فعلی‌به روی یک منبع برای یک کاربر.

    حضور ردیف = «تصمیم نهایی همان لیست فعل‌ها است» برای آن (type, key).
    نبود ردیف = رفتار نقش/گروه فعلی (baseline) بدون تغییر.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="person_acl_entries",
        db_index=True,
    )
    resource_type = models.CharField(
        max_length=16,
        choices=ACLEntryType.choices,
        db_index=True,
    )
    resource_key = models.CharField(max_length=120, db_index=True)
    verbs = models.JSONField(
        default=list,
        help_text="لیست ACLVerb — مثل [\"view\",\"add\"]",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="granted_acl_entries",
        help_text="چه کسی این دسترسی صریح را داده (audit).",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="revoked_acl_entries",
    )

    class Meta:
        app_label = "org"
        db_table = "org_person_acl_entry"
        verbose_name = "Person ACL Entry (دسترسی صریح)"
        verbose_name_plural = "Person ACL Entries (دسترسی‌های صریح)"
        ordering = ("resource_type", "resource_key")
        constraints = [
            # فقط یک ردیف زنده به ازای هر (user, type, key).
            # UniqueConstraint روی Postgres ایندکس پشتیبان روی همین ستون‌ها می‌سازد،
            # پس ایندکس جداگانه لازم نیست (نام ایندکس با migration در sync می‌ماند).
            models.UniqueConstraint(
                fields=["user", "resource_type", "resource_key"],
                condition=models.Q(is_deleted=False),
                name="uniq_org_person_acl_live",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.resource_type}:{self.resource_key} [{','.join(self.verbs or [])}]"

    @property
    def verb_set(self) -> set[str]:
        return set(self.verbs or [])


class SidebarVisibilityRule(DomainModel):
    """A stored sidebar visibility override for one role or one user."""

    role_code = models.CharField(max_length=64, blank=True, default="", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sidebar_visibility_rules",
    )
    item_key = models.CharField(max_length=120, db_index=True)
    is_visible = models.BooleanField(default=True)

    class Meta:
        app_label = "org"
        db_table = "org_sidebar_visibility_rule"
        verbose_name = "Sidebar visibility rule (قانون نمایش سایدبار)"
        verbose_name_plural = "Sidebar visibility rules (قوانین نمایش سایدبار)"
        ordering = ("role_code", "item_key")
        constraints = [
            models.UniqueConstraint(
                fields=["role_code", "item_key"],
                condition=models.Q(user__isnull=True, is_deleted=False),
                name="uniq_org_sidebar_role_item_live",
            ),
            models.UniqueConstraint(
                fields=["user", "item_key"],
                condition=models.Q(user__isnull=False, is_deleted=False),
                name="uniq_org_sidebar_user_item_live",
            ),
            models.CheckConstraint(
                condition=(
                    (models.Q(user__isnull=True) & ~models.Q(role_code=""))
                    | (models.Q(user__isnull=False, role_code=""))
                ),
                name="org_sidebar_visibility_scope_valid",
            ),
        ]

    def __str__(self) -> str:
        subject = self.role_code or str(self.user_id)
        return f"{subject} → {self.item_key} ({'show' if self.is_visible else 'hide'})"
