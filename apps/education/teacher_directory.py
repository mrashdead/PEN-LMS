"""Management teaching profile, scoped by the viewer and a canonical Person."""
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Q
from django.http import Http404

from apps.core.access_enforcer import acl_strict
from apps.core.utils import jalali_date_str
from apps.education.teaching import offering_status_label, teaching_identity
from apps.persons.models import Person
from apps.persons.services import mask_identifier
from apps.academics.models import ClassGroup


def teacher_context(scope, pk):
    if not scope.person_links:
        raise PermissionDenied('مجوز مشاهدهٔ مدرس را ندارید.')
    if not scope.staff and not (scope.person and scope.person.pk == pk and 'teacher' in scope.roles):
        raise Http404('مدرس یافت نشد.')
    person = Person.objects.filter(pk=pk).first()
    if person is None or not person.has_type(Person.Type.TEACHER):
        raise Http404('مدرس یافت نشد.')

    offerings = scope.offerings().filter(
        Q(instructor=person)
        | Q(class_groups__teacher=person, class_groups__is_deleted=False)
        | Q(sessions__teacher=person, sessions__is_deleted=False)
    ).select_related('course', 'instructor', 'location').annotate(
        teaches_class=Exists(ClassGroup.objects.filter(offering_id=OuterRef('pk'), teacher=person))
    ).distinct().order_by('-start_date', '-created_at')
    groups = scope.classes().filter(
        Q(teacher=person) | Q(offering__instructor=person, offering__is_deleted=False)
    ).filter(Q(offering__isnull=True) | Q(offering__is_deleted=False)).select_related(
        'teacher', 'term', 'offering__course', 'offering__instructor'
    ).order_by('-term__start_date', 'name', 'pk')
    if not acl_strict(scope.user, 'model', 'education.courseoffering', 'view', True):
        offerings = offerings.none()
    if not acl_strict(scope.user, 'model', 'academics.classgroup', 'view', True):
        groups = groups.none()

    offering_rows = [
        {'id': str(item.pk), 'title': item.title or item.course.title, 'code': item.code,
         'course': item.course.title, 'status': item.status, 'status_label': offering_status_label(item),
         'is_active': item.is_active, 'schedule': item.schedule or {},
         'assignment_label': 'مدرس برگزاری' if item.instructor_id == person.pk else ('مدرس کلاس' if item.teaches_class else 'مدرس جلسات'),
         'start_date': jalali_date_str(item.start_date) if item.start_date else '',
         'end_date': jalali_date_str(item.end_date) if item.end_date else '',
         'location': item.location.name if item.location else '',
         'url': f'/workspace/enrollments/offering/{item.pk}/', **teaching_identity(item)}
        for item in offerings
    ]
    class_rows = [
        {'id': str(item.pk), 'title': item.name, 'code': item.code, 'term': item.term.title,
         'course': item.offering.course.title if item.offering else '',
         'offering': item.offering.title or item.offering.course.title if item.offering else '',
         'status_label': 'فعال' if item.is_active else 'غیرفعال', 'is_active': item.is_active,
         'assignment_label': 'مدرس کلاس' if item.teacher_id == person.pk else 'مدرس برگزاری',
         'schedule': item.schedule or {}, 'location': item.room,
         'start_date': jalali_date_str(item.term.start_date), 'end_date': jalali_date_str(item.term.end_date),
         'url': f'/workspace/enrollments/class/{item.pk}/', **teaching_identity(item.offering, item)}
        for item in groups
    ]
    identity = scope.identity(person)
    identity['url'] = None
    identity['employee_code'] = mask_identifier(person.employee_code) if identity['masked'] else person.employee_code
    return {
        'kind': 'teacher', 'title': f'دوره‌ها و کلاس‌های {person.display_name}',
        'identity': identity, 'status': 'فعال' if person.is_active else 'غیرفعال',
        'description': 'برگزاری‌ها و کلاس‌های مرتبط با مدرس', 'capacity': None,
        'teaching': {'offerings': offering_rows, 'classes': class_rows,
                     'summary': {'offerings': len(offering_rows), 'classes': len(class_rows),
                                 'running': sum(row['status'] == 'running' for row in offering_rows),
                                 'preregistration': sum(row['status'] == 'open' for row in offering_rows)}},
    }
