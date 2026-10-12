"""Read teaching identity from live relationships; never copy names to enrollments."""
from django.db.models import Q

from apps.academics.models import ClassEnrollment
from apps.education.models import OfferingEnrollment


def teacher_identity(person):
    if person is None or person.is_deleted:
        return None
    return {"id": str(person.pk), "name": person.display_name}


def teaching_identity(offering=None, group=None):
    """Keep the offering instructor and the actual class teacher distinguishable."""
    if group is not None and group.is_deleted:
        group = None
    instructor = teacher_identity(offering.instructor) if offering else None
    class_teacher = teacher_identity(group.teacher) if group else None
    return {"instructor": instructor, "class_teacher": class_teacher,
            "teacher": class_teacher or instructor}


def offering_status_label(offering):
    return "پیش‌ثبت‌نام" if offering.status == "open" else offering.get_status_display()


def learner_courses(student):
    """Called only after the portal has resolved the permitted learner."""
    enrollments = OfferingEnrollment.objects.filter(
        student=student, offering__is_deleted=False,
    ).select_related("offering__course", "offering__instructor",
                     "final_class_enrollment__class_group__teacher")
    memberships = ClassEnrollment.objects.filter(
        student=student, class_group__is_deleted=False,
    ).filter(Q(class_group__offering__isnull=True) | Q(class_group__offering__is_deleted=False)).select_related(
        "class_group__teacher", "class_group__offering__course", "class_group__offering__instructor")
    result, linked_ids = [], set()

    def row(offering, group, active, status):
        return {"id": str(offering.pk if offering else group.pk),
                "course": offering.course.title if offering else group.name,
                "title": (offering.title or offering.course.title) if offering else group.name,
                "class_name": group.name if group else "",
                "status": offering.status if offering else ("running" if group.is_active else "closed"),
                "status_label": offering_status_label(offering) if offering else ("فعال" if group.is_active else "غیرفعال"),
                "enrollment_status": status, "is_active": active,
                "start_date": offering.start_date.isoformat() if offering and offering.start_date else "",
                "end_date": offering.end_date.isoformat() if offering and offering.end_date else "",
                "schedule": (group.schedule if group else offering.schedule) or {},
                **teaching_identity(offering, group)}

    for enrollment in enrollments:
        membership = enrollment.final_class_enrollment
        group = membership.class_group if membership and not membership.is_deleted and not membership.class_group.is_deleted else None
        if membership:
            linked_ids.add(membership.pk)
        result.append(row(enrollment.offering, group, enrollment.is_active,
                          enrollment.get_lifecycle_status_display()))
    for membership in memberships:
        if membership.pk not in linked_ids:
            result.append(row(membership.class_group.offering, membership.class_group,
                              membership.is_active, "فعال" if membership.is_active else "لغوشده"))
    return result


def teacher_standalone_classes(user):
    """Classes without an offering still belong in their teacher's panel."""
    from apps.academics.scoping import class_groups_visible_to

    person = getattr(user, "person", None)
    if person is None:
        return []
    groups = class_groups_visible_to(user).filter(teacher=person, offering__isnull=True).select_related("term", "teacher")
    return [{"id": str(group.pk), "name": group.name, "code": group.code,
             "term": group.term.title, "room": group.room, "schedule": group.schedule,
             "is_active": group.is_active, **teaching_identity(group=group)} for group in groups]
