"""
Seed Django Groups with model permissions.

Run after migrations:
    python manage.py seed_groups

Business roles are checked by apps.core.permissions. These groups provide the
second, model-level authorization layer used by API views.
"""
from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction


COMMON = [
    "accounts.view_user",
    "persons.view_person",
    "tasks.view_workflowtask",
]

GROUPS: dict[str, dict[str, object]] = {
    "مدیر سیستم": {
        "codename": "admin",
        "priority": 0,
        "perms": "*",
    },
    "مدیر مؤسسه": {
        "codename": "manager",
        "priority": 10,
        "perms": COMMON + [
            "accounts.add_user",
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.add_person",
            "persons.change_person",
            "persons.delete_person",
            "persons.view_studentprofile",
            "persons.add_studentprofile",
            "persons.change_studentprofile",
            "persons.delete_studentprofile",
            "persons.view_guardianprofile",
            "persons.add_guardianprofile",
            "persons.change_guardianprofile",
            "persons.delete_guardianprofile",
            "persons.view_studentguardian",
            "persons.add_studentguardian",
            "persons.change_studentguardian",
            "persons.delete_studentguardian",
            "persons.view_staffprofile",
            "persons.add_staffprofile",
            "persons.change_staffprofile",
            "persons.delete_staffprofile",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            "persons.view_financial_report",
            "workflow.view_workflowdefinition",
            "workflow.view_instance",
            "workflow.add_instance",
            "workflow.change_instance",
            "workflow.delete_instance",
            "workflow.view_actionlog",
            "workflow.manage_workflow_definition",
            "workflow.view_all_instances",
            "workflow.approve_instance",
            "workflow.cancel_any_instance",
            "academics.view_academicterm",
            "academics.add_academicterm",
            "academics.change_academicterm",
            "academics.delete_academicterm",
            "academics.view_classgroup",
            "academics.add_classgroup",
            "academics.change_classgroup",
            "academics.delete_classgroup",
            "academics.view_all_class_groups",
            "academics.manage_class_group",
            "academics.view_classenrollment",
            "academics.add_classenrollment",
            "academics.change_classenrollment",
            "academics.delete_classenrollment",
            "academics.manage_term",
            "academics.manage_enrollment",
            "forms.view_formschema",
            "forms.add_formschema",
            "forms.change_formschema",
            "forms.view_formsubmission",
            "forms.add_formsubmission",
            "forms.change_formsubmission",
            "forms.delete_formsubmission",
            "forms.view_formattachment",
            "forms.add_formattachment",
            "forms.view_formcomment",
            "forms.add_formcomment",
            "forms.delete_formcomment",
            # Education master data and class sessions
            "education.view_department",
            "education.add_department",
            "education.change_department",
            "education.delete_department",
            "education.view_location",
            "education.add_location",
            "education.change_location",
            "education.delete_location",
            "education.view_lesson",
            "education.add_lesson",
            "education.change_lesson",
            "education.delete_lesson",
            "education.view_course",
            "education.add_course",
            "education.change_course",
            "education.delete_course",
            "education.view_courseoffering",
            "education.add_courseoffering",
            "education.change_courseoffering",
            "education.delete_courseoffering",
            "education.view_classsession",
            "education.add_classsession",
            "education.change_classsession",
            "education.delete_classsession",
            "education.view_offeringenrollment",
            "education.add_offeringenrollment",
            "education.change_offeringenrollment",
            "education.delete_offeringenrollment",
            "education.view_academicholiday",
            "education.add_academicholiday",
            "education.change_academicholiday",
            "education.delete_academicholiday",
        ],
    },
    "کارمند": {
        "codename": "employee",
        "priority": 100,
        # add_person is intentional: the hierarchy matrix (apps.persons.hierarchy)
        # is the *authorization* layer for WHICH type a staff member may create
        # (a plain employee → students/guardians only), while this model perm is
        # the second layer DRF checks. Removing it here would make the bottom
        # tier of the onboarding matrix unreachable.
        "perms": COMMON + [
            "persons.view_person_list",
            "persons.add_person",
            "persons.add_studentprofile",
            "persons.view_studentprofile",
            "persons.add_guardianprofile",
            "persons.view_guardianprofile",
            "persons.add_studentguardian",
            "persons.view_studentguardian",
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "معلم / مدرس": {
        "codename": "teacher",
        "priority": 40,
        "perms": COMMON + [
            "persons.view_person_detail",
            "persons.view_person_list",
            "persons.view_grades_report",
            "persons.view_attendance_report",
            # Teacher-portal READS ride the generic education list/detail
            # endpoints, which carry StrictDjangoModelPermissions — without
            # these view_* rows the teacher's own class/session list screens
            # 403. The portal WRITE endpoints (record-session, sheet,
            # report-cards, roster) are role+ownership gated and need no
            # add_*. Row scope stays enforced by academics.scoping
            # (teacher → only the classes they teach), so view_* here never
            # exposes another teacher's class.
            "education.view_courseoffering",
            "education.view_classsession",
            "education.view_attendancerecord",
            "education.view_graderecord",
            "education.view_lesson",
            "education.view_location",
            "education.view_offeringenrollment",
            # Teacher intake rights: supervisor+ may create students (matrix);
            # a teacher who is also a supervisor inherits this group plus the
            # employee one, so add_person is granted at the tier that needs it.
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    "دانش‌آموز": {
        "codename": "student",
        "priority": 90,
        "perms": COMMON + [
            "workflow.view_instance",
            "workflow.add_instance",
            "academics.view_academicterm",
            "academics.view_classgroup",
            "academics.view_classenrollment",
        ],
    },
    # Read-mostly parent account. NO add_* anywhere: a guardian submits
    # requests through the forms workflow (forms.add_formsubmission), never by
    # writing education/academics rows. Row visibility comes from the
    # StudentGuardian link inside the scoping selectors, not from these perms.
    "والدین": {
        "codename": "guardian",
        "priority": 110,
        "perms": [
            "tasks.view_workflowtask",
            "workflow.view_instance",
            "workflow.add_instance",
            "forms.view_formschema",
            "forms.add_formsubmission",
            "forms.view_formsubmission",
            "forms.add_formattachment",
            "forms.view_formattachment",
            "academics.view_academicterm",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed default Django Groups with model permissions (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        for group_name, config in GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            perms_config = config["perms"]

            if perms_config == "*":
                group.permissions.set(Permission.objects.all())
                self.stdout.write(
                    f"[{'created' if created else 'updated'}] {group_name} (all permissions)"
                )
                continue

            perms_to_add: list[Permission] = []
            missing: list[str] = []
            for perm_str in perms_config:
                try:
                    app_label, codename = perm_str.strip().split(".", 1)
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename,
                    )
                    perms_to_add.append(permission)
                except (Permission.DoesNotExist, ValueError):
                    missing.append(perm_str)

            group.permissions.set(perms_to_add)
            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{group_name}] permissions not found: {missing}"
                    )
                )
            self.stdout.write(
                f"[{'created' if created else 'updated'}] "
                f"{group_name} — {len(perms_to_add)} permission(s)"
            )

        self.stdout.write(self.style.SUCCESS("groups ready"))
