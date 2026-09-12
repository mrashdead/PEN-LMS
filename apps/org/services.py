"""
Organizational read-models + delegation service.

Everything here is DERIVED from existing tables (single source of truth):
  • org chart      ← User.manager (self-FK) + department + Role/UserRole
  • org profile    ← User + Person + roles + groups + tasks + delegation
  • permission matrix ← Django Group permissions (seed_groups) + role codes
  • access simulator  ← the SAME checks the APIs make (role trio + group perm)
  • responsibilities  ← Workflow Transition.allowed_role_codes (who approves)
  • unit performance  ← WorkflowTask completion/overdue grouped by department

No new tables except Delegation (models.py). Read functions never mutate.
"""
from __future__ import annotations

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import Role
from apps.org.models import Delegation
from apps.tasks.models import WorkflowTask
from apps.workflow.models import Transition, WorkflowDefinition

User = get_user_model()

# The role trios the APIs actually enforce (kept in sync with the permission
# classes; used by the simulator to explain a verdict, not to grant one).
ELEVATED = {"manager", "workflow_admin", "hr"}
STAFF = {"manager", "workflow_admin", "hr", "employee", "teacher"}

# Verb → Django model-permission codename prefix, for the matrix.
VERB_PERM = {
    "view": "view",
    "add": "add",
    "change": "change",
    "delete": "delete",
}


# ── org chart ───────────────────────────────────────────────────────────────

def org_chart() -> list[dict]:
    """
    Tree of users by manager chain, grouped under departments.

    Roots = active users with no manager. Each node carries its direct
    reports. Depth is bounded by the manager graph (assumed acyclic; a
    visited-set guards against accidental cycles).
    """
    users = list(
        User.objects.filter(is_active=True, is_deleted=False)
        .select_related("manager")
        .order_by("first_name", "last_name")
    )
    by_manager: dict = defaultdict(list)
    for u in users:
        by_manager[u.manager_id].append(u)

    def node(u, seen):
        children = []
        for child in by_manager.get(u.pk, []):
            if child.pk in seen:
                continue
            children.append(node(child, seen | {child.pk}))
        return {
            "id": str(u.pk),
            "name": u.get_full_name() or u.username,
            "username": u.username,
            "department": u.department or "",
            "job_title": u.job_title or "",
            "roles": sorted(u.role_codes()),
            "reports": children,
        }

    roots = []
    seen = set()
    for u in users:
        if u.manager_id is None and u.pk not in seen:
            roots.append(node(u, {u.pk}))
            seen.add(u.pk)
    return roots


def departments() -> list[dict]:
    """Distinct departments with member counts (for the chart's unit cards)."""
    rows = (
        User.objects.filter(is_active=True, is_deleted=False)
        .exclude(department="")
        .values("department")
        .annotate(count=Count("pk"))
        .order_by("department")
    )
    return [{"department": r["department"], "count": r["count"]} for r in rows]


# ── org profile ──────────────────────────────────────────────────────────────

def person_profile(user_id) -> dict | None:
    """Organizational profile of one user (never PII beyond what's shown)."""
    u = (
        User.objects.filter(pk=user_id, is_deleted=False)
        .select_related("manager")
        .prefetch_related("user_roles__role", "groups")
        .first()
    )
    if u is None:
        return None
    roles = sorted(u.role_codes())
    groups = sorted(g.name for g in u.groups.all())
    person = getattr(u, "person", None)
    pending = WorkflowTask.objects.filter(assignee=u, status=WorkflowTask.Status.PENDING).count()
    active_delegations = Delegation.objects.filter(
        principal=u, is_active=True, valid_to__gte=timezone.now()
    ).select_related("delegate")
    return {
        "id": str(u.pk),
        "name": u.get_full_name() or u.username,
        "username": u.username,
        "email": u.email or "",
        "department": u.department or "",
        "job_title": u.job_title or "",
        "employee_code": u.employee_code or "",
        "is_active": u.is_active,
        "manager": (u.manager.get_full_name() or u.manager.username) if u.manager else None,
        "manager_id": str(u.manager_id) if u.manager_id else None,
        "roles": roles,
        "groups": groups,
        "person_type": person.person_type if person else "",
        "person_type_display": person.get_person_type_display() if person else "",
        "pending_tasks": pending,
        "delegations": [
            {
                "id": str(d.pk),
                "delegate_name": d.delegate.get_full_name() or d.delegate.username,
                "department": d.department,
                "workflow_code": d.workflow_code,
                "valid_from": d.valid_from.date().isoformat(),
                "valid_to": d.valid_to.date().isoformat(),
            }
            for d in active_delegations
        ],
    }


# ── permission matrix ────────────────────────────────────────────────────────

# Curated, human-readable resources → the model permissions that gate them.
MATRIX_RESOURCES = [
    {"key": "persons", "label": "اشخاص", "model": "persons.person"},
    {"key": "forms", "label": "فرم‌ها", "model": "forms.formsubmission"},
    {"key": "schemas", "label": "تعریف فرم", "model": "forms.formschema"},
    {"key": "workflow", "label": "درخواست‌ها", "model": "workflow.instance"},
    {"key": "academics", "label": "آموزش", "model": "academics.classgroup"},
    {"key": "education", "label": "دوره/جلسه", "model": "education.lesson"},
]


def permission_matrix() -> dict:
    """
    Group × resource × verb matrix, straight from seeded Django permissions.
    Two sources are distinguished: direct group grant vs. inherited role.
    """
    groups = list(Group.objects.prefetch_related("permissions").order_by("name"))
    # map "app.model" → set of "verb" granted to each group
    matrix = []
    for g in groups:
        perms = {p.codename for p in g.permissions.all()}  # e.g. "add_person"
        row = {"group": g.name, "resources": {}}
        for res in MATRIX_RESOURCES:
            app_label, model = res["model"].split(".")
            verbs = {}
            for verb in VERB_PERM:
                # Django stores codename as "<verb>_<model>"; check app via
                # permission string is unnecessary — codename is unique per
                # content type, and we already loaded this group's perms.
                verbs[verb] = f"{verb}_{model}" in perms
            row["resources"][res["key"]] = verbs
        matrix.append(row)
    return {"resources": MATRIX_RESOURCES, "rows": matrix}


# ── access simulator ─────────────────────────────────────────────────────────

def simulate_access(user_id, resource_key: str, verb: str) -> dict:
    """
    Explain whether a user may do <verb> on <resource>, and WHY.

    Mirrors the two real layers: (1) Django model permission via groups
    (what StrictDjangoModelPermissions/HasGroupPermission check), and
    (2) the role trio the sensitive views add. Returns a verdict + reasons;
    it does NOT grant anything.
    """
    u = User.objects.filter(pk=user_id, is_deleted=False).prefetch_related(
        "groups__permissions"
    ).first()
    if u is None:
        return {"allowed": False, "reasons": ["کاربر یافت نشد."]}

    res = next((r for r in MATRIX_RESOURCES if r["key"] == resource_key), None)
    if res is None:
        return {"allowed": False, "reasons": ["منبع نامشخص."]}
    if verb not in VERB_PERM:
        return {"allowed": False, "reasons": ["عملیات نامعتبر."]}

    reasons = []
    if u.is_superuser:
        return {"allowed": True, "reasons": ["کاربر ارشد (superuser) — دسترسی کامل."]}

    # Layer 1: model permission (group grant). Django perm string is
    # "<app_label>.<codename>" where codename is "<verb>_<model>".
    app_label, model = res["model"].split(".")
    codename = f"{VERB_PERM[verb]}_{model}"
    perm = f"{app_label}.{codename}"
    has_model_perm = u.has_perm(perm)
    if has_model_perm:
        # find which group(s) grant it, to explain inheritance
        granting = [
            g.name for g in u.groups.all()
            if g.permissions.filter(codename=codename).exists()
        ]
        reasons.append("مجوز مدل از گروه(ها): " + ("، ".join(granting) if granting else "مستقیم"))
    else:
        reasons.append(f"مجوز مدل «{perm}» وجود ندارد.")

    # Layer 2: role trio for sensitive verbs (approve-ish = change on workflow)
    roles = u.role_codes()
    verdict = has_model_perm
    if resource_key == "workflow" and verb == "change":
        if roles & ELEVATED:
            reasons.append("نقش تأییدکننده (مدیر/HR/ادمین فرآیند) ✓")
        else:
            reasons.append("نقش تأیید لازم نیست (فقط مدیر/HR/ادمین فرآیند).")
            verdict = False
    if resource_key == "schemas" and verb in {"add", "change"}:
        if roles & ELEVATED:
            reasons.append("نقش مدیریت فرم ✓")
        else:
            reasons.append("فقط نقش‌های ارشد می‌توانند تعریف فرم را تغییر دهند.")
            verdict = False

    return {"allowed": bool(verdict), "reasons": reasons, "roles": sorted(roles)}


# ── responsibilities (AssignmentPolicy UI) ───────────────────────────────────

def responsibilities() -> list[dict]:
    """
    «چه کسی مسئول تأیید چیست؟» — derived from Transition.allowed_role_codes
    across active workflow definitions. Each row: process, action, roles.
    """
    out = []
    for wf in WorkflowDefinition.objects.filter(is_active=True).order_by("code"):
        trans = Transition.objects.filter(workflow_definition=wf).select_related(
            "from_state", "to_state"
        )
        for t in trans:
            roles = t.allowed_role_codes or []
            if not roles:
                continue
            out.append({
                "workflow": wf.name,
                "workflow_code": wf.code,
                "action": t.name,
                "kind": t.kind or "",
                "from_state": t.from_state.name if t.from_state else "",
                "to_state": t.to_state.name if t.to_state else "",
                "roles": roles,
                "requires_comment": t.requires_comment,
            })
    return out


# ── unit performance ─────────────────────────────────────────────────────────

def unit_performance() -> list[dict]:
    """
    Per-department task throughput + SLA health (green/amber/red), derived
    from WorkflowTask joined to assignee.department.
    """
    now = timezone.now()
    rows = (
        WorkflowTask.objects.filter(assignee__isnull=False)
        .values("assignee__department")
        .annotate(
            total=Count("pk"),
            done=Count("pk", filter=Q(status=WorkflowTask.Status.COMPLETED)),
            pending=Count("pk", filter=Q(status=WorkflowTask.Status.PENDING)),
            overdue=Count("pk", filter=Q(status=WorkflowTask.Status.PENDING, due_date__isnull=False, due_date__lt=now)),
        )
    )
    out = []
    for r in rows:
        dept = r["assignee__department"] or "بدون واحد"
        total = r["total"] or 0
        done = r["done"] or 0
        overdue = r["overdue"] or 0
        rate = round(done * 100 / total) if total else 0
        if overdue > 0:
            health = "red"
        elif rate >= 80:
            health = "green"
        else:
            health = "amber"
        out.append({
            "department": dept,
            "total": total,
            "done": done,
            "pending": r["pending"] or 0,
            "overdue": overdue,
            "rate": rate,
            "health": health,
        })
    out.sort(key=lambda x: (-x["total"], x["department"]))
    return out


# ── delegation CRUD ──────────────────────────────────────────────────────────

def create_delegation(*, principal_id, delegate_id, department, workflow_code,
                      reason, valid_from, valid_to, actor) -> Delegation:
    d = Delegation(
        principal_id=principal_id, delegate_id=delegate_id,
        department=(department or "").strip(), workflow_code=(workflow_code or "").strip(),
        reason=(reason or "").strip(), valid_from=valid_from, valid_to=valid_to,
        created_by=actor,
    )
    d.full_clean()
    d.save()
    return d


def revoke_delegation(*, delegation_id, actor) -> bool:
    d = Delegation.objects.filter(pk=delegation_id, is_active=True).first()
    if d is None:
        return False
    d.is_active = False
    d.revoked_at = timezone.now()
    d.revoked_by = actor
    d.save(update_fields=["is_active", "revoked_at", "revoked_by", "updated_at"])
    return True


def list_delegations() -> list[dict]:
    now = timezone.now()
    rows = Delegation.objects.filter(is_deleted=False).select_related(
        "principal", "delegate"
    ).order_by("-valid_from")[:200]
    return [
        {
            "id": str(d.pk),
            "principal": d.principal.get_full_name() or d.principal.username,
            "delegate": d.delegate.get_full_name() or d.delegate.username,
            "department": d.department,
            "workflow_code": d.workflow_code,
            "reason": d.reason,
            "valid_from": d.valid_from.date().isoformat(),
            "valid_to": d.valid_to.date().isoformat(),
            "is_live": d.is_live,
            "is_active": d.is_active,
        }
        for d in rows
    ]
