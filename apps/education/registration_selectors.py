"""Two existing tables, one bounded registration read model; no copied relationships."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef, Q
from django.http import Http404
from django.utils import timezone

from apps.academics.models import ClassEnrollment, ClassGroup
from apps.academics.scoping import ward_student_ids_for
from apps.core.access_enforcer import acl_strict
from apps.core.crud import roles_for
from apps.core.models import AuditEvent
from apps.core.utils import english_numbers, jalali_date_str
from apps.education.models import AttendanceRecord, Course, CourseOffering, OfferingEnrollment
from apps.education.registration_permissions import STAFF_ROLES, registration_permission
from apps.persons.models import Person
from apps.persons.services import mask_identifier
from apps.reports.selectors.reports import ReportFilterError, _clean_uuid, _parse_report_date

STATUS_LABELS = dict(OfferingEnrollment.LifecycleStatus.choices)
STATUS_LABELS['inactive'] = 'غیرفعال'


class RegistrationScope:
    def __init__(self, user):
        self.user, self.roles = user, roles_for(user)
        self.staff = bool(user.is_superuser or self.roles & STAFF_ROLES)
        self.person = getattr(user, 'person', None)
        self.wards = set(ward_student_ids_for(user)) if 'guardian' in self.roles else set()
        self.full_identity = bool(user.is_superuser or self.roles & {'manager', 'workflow_admin', 'hr'} or user.has_perm('persons.view_person_detail'))
        self.person_links = acl_strict(user, 'model', 'persons.person', 'view', True)
        self.permissions = {s: {v: registration_permission(user, s, v) for v in ('view', 'add', 'change', 'delete')} for s in ('offering', 'class')}

    def offerings(self):
        qs = CourseOffering.objects.filter(is_deleted=False)
        if self.staff:
            return qs
        if not self.person:
            return qs.none()
        condition = Q(pk__in=[])
        if 'teacher' in self.roles:
            condition |= Q(instructor=self.person) | Q(class_groups__teacher=self.person, class_groups__is_deleted=False)
        if 'student' in self.roles:
            condition |= Q(enrollments__student=self.person, enrollments__is_deleted=False)
        if self.wards:
            condition |= Q(enrollments__student_id__in=self.wards, enrollments__is_deleted=False)
        return qs.filter(condition).distinct()

    def classes(self):
        qs = ClassGroup.objects.filter(is_deleted=False)
        if self.staff:
            return qs
        if not self.person:
            return qs.none()
        condition = Q(pk__in=[])
        if 'teacher' in self.roles:
            condition |= Q(teacher=self.person) | Q(offering__instructor=self.person)
        if 'student' in self.roles:
            condition |= Q(enrollments__student=self.person, enrollments__is_deleted=False)
        if self.wards:
            condition |= Q(enrollments__student_id__in=self.wards, enrollments__is_deleted=False)
        return qs.filter(condition).distinct()

    def roots(self):
        offered = OfferingEnrollment.objects.filter(is_deleted=False, offering__is_deleted=False)
        members = ClassEnrollment.objects.filter(is_deleted=False, class_group__is_deleted=False)
        if not self.staff:
            condition = Q(pk__in=[])
            group_condition = Q(pk__in=[])
            if self.person and 'teacher' in self.roles:
                condition |= Q(offering__instructor=self.person) | Q(final_class_enrollment__class_group__teacher=self.person)
                group_condition |= Q(class_group__teacher=self.person) | Q(class_group__offering__instructor=self.person)
            ids = set(self.wards)
            if self.person and 'student' in self.roles:
                ids.add(self.person.pk)
            condition |= Q(student_id__in=ids)
            group_condition |= Q(student_id__in=ids)
            offered = offered.filter(condition)
            members = members.filter(group_condition)
        if not self.permissions['offering']['view']:
            offered = offered.none()
        if not self.permissions['class']['view']:
            members = members.none()
        # Only suppress memberships whose canonical parent is itself visible.
        members = members.alias(has_parent=Exists(offered.filter(final_class_enrollment_id=OuterRef('pk')))).filter(has_parent=False)
        return offered, members

    def identity(self, person):
        full = self.full_identity or person.user_id == self.user.pk or person.pk in self.wards
        return {'id': str(person.pk), 'name': person.display_name,
                'national_code': person.national_code if full else mask_identifier(person.national_code),
                'mobile': person.mobile if full else mask_identifier(person.mobile),
                'student_code': person.student_code, 'masked': not full,
                'url': f'/workspace/enrollments/people/{person.pk}/' if self.person_links else None}


@dataclass(frozen=True)
class RegistrationFilters:
    course: str = ''
    offering: str = ''
    class_group: str = ''
    student: str = ''
    status: str = ''
    search: str = ''
    start: object = None
    end: object = None

    @classmethod
    def parse(cls, params):
        identifiers = {key: _clean_uuid(params.get(key)) for key in ('course', 'offering', 'class_group', 'student')}
        status = params.get('status', '')
        if status and status not in STATUS_LABELS:
            raise ReportFilterError('وضعیت ثبت‌نام معتبر نیست.')
        start, end = _parse_report_date(params.get('from')), _parse_report_date(params.get('to'))
        if start and end and end < start:
            raise ReportFilterError('تاریخ پایان باید بعد از تاریخ شروع باشد.')
        return cls(**identifiers, status=status, search=english_numbers(params.get('search', '').strip())[:128], start=start, end=end)

    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.__dict__, sort_keys=True, default=str).encode()).hexdigest()[:20]


def filtered_roots(scope, filters):
    offered, members = scope.roots()
    if filters.course:
        offered = offered.filter(offering__course_id=filters.course)
        members = members.filter(class_group__offering__course_id=filters.course)
    if filters.offering:
        offered = offered.filter(offering_id=filters.offering)
        members = members.filter(class_group__offering_id=filters.offering)
    if filters.class_group:
        offered = offered.filter(final_class_enrollment__class_group_id=filters.class_group)
        members = members.filter(class_group_id=filters.class_group)
    if filters.student:
        offered, members = offered.filter(student_id=filters.student), members.filter(student_id=filters.student)
    if filters.status:
        if filters.status == 'inactive':
            offered, members = offered.filter(is_active=False), members.filter(is_active=False)
        else:
            offered = offered.filter(lifecycle_status=filters.status)
            members = members.filter(is_active=filters.status == 'confirmed') if filters.status in {'confirmed', 'cancelled'} else members.none()
    for value, lookup in ((filters.start, 'gte'), (filters.end, 'lte')):
        if value:
            offered = offered.filter(**{'enrolled_at__' + lookup: value})
            members = members.filter(**{'enrollment_date__' + lookup: value})
    if filters.search:
        text = filters.search
        condition = Q(student__first_name__istartswith=text) | Q(student__last_name__istartswith=text) | Q(student__student_code__istartswith=text)
        # Do not expose masked identifiers through a search oracle.
        if scope.full_identity:
            condition |= Q(student__national_code__startswith=text)
        offered = offered.filter(condition)
        members = members.filter(condition)
    return offered, members


def hydrate(offered, members):
    return (
        offered.select_related('student', 'offering__course', 'final_class_enrollment__class_group__term').defer('cheques', 'reference', 'student__address', 'offering__schedule'),
        members.select_related('student', 'class_group__term', 'class_group__offering__course', 'source_offering_enrollment').defer('student__address', 'class_group__schedule'),
    )


def registration_row(obj, source, scope):
    if source == 'offering':
        offering = obj.offering
        membership = obj.final_class_enrollment
        group = membership.class_group if membership else None
        status, date = obj.lifecycle_status, obj.enrolled_at
    else:
        membership, group = obj, obj.class_group
        offering = group.offering
        status, date = ('confirmed' if obj.is_active else 'cancelled'), obj.enrollment_date
    if not obj.is_active and status not in {'cancelled', 'refunded'}:
        status = 'inactive'
    course = offering.course if offering else None
    linked = source == 'class' and getattr(obj, 'source_offering_enrollment', None)
    may_change = scope.permissions[source]['change'] and (not linked or scope.permissions['offering']['change'])
    return {
        'id': str(obj.pk), 'source': source, 'created_at': obj.created_at.isoformat(),
        'student': scope.identity(obj.student),
        'course': {'id': str(course.pk), 'title': course.title, 'url': f'/workspace/enrollments/courses/{course.pk}/'} if course else None,
        'offering': {'id': str(offering.pk), 'title': offering.title or course.title, 'code': offering.code,
                     'url': f'/workspace/enrollments/offerings/{offering.pk}/', 'status': offering.get_status_display()} if offering else None,
        'class_group': {'id': str(group.pk), 'title': group.name, 'code': group.code, 'term': group.term.title,
                        'url': f'/workspace/enrollments/classes/{group.pk}/'} if group else None,
        'membership_active': bool(membership and membership.is_active and not membership.is_deleted),
        'status': status, 'status_label': STATUS_LABELS.get(status, status),
        'is_active': obj.is_active, 'date': date.isoformat(), 'date_label': jalali_date_str(date),
        'url': f'/workspace/enrollments/records/{source}/{obj.pk}/',
        'actions': {'change': bool(may_change), 'assign_class': bool(may_change and source == 'offering' and not membership and obj.is_active),
                    'reactivate': bool(may_change and not obj.is_active and status != 'refunded'),
                    'cancel': bool(may_change and obj.is_active)},
    }


def list_registrations(scope, filters, params):
    offered, members = filtered_roots(scope, filters)
    try:
        size = int(params.get('page_size', 25))
    except (ValueError, TypeError):
        raise ReportFilterError('تعداد ردیف نامعتبر است.')
    size = max(1, min(100, size))
    token = params.get('cursor')
    cursor = None
    if token:
        try:
            cursor = signing.loads(token, salt='registration-directory', max_age=86400)
            if cursor['filter'] != filters.fingerprint() or cursor['direction'] not in ('before', 'after'):
                raise ValueError
            boundary_time, boundary_id = datetime.fromisoformat(cursor['time']), UUID(cursor['id'])
        except (signing.BadSignature, ValueError, KeyError, TypeError):
            raise ReportFilterError('صفحه‌بندی معتبر نیست؛ از صفحهٔ اول شروع کنید.')
    before = bool(cursor and cursor['direction'] == 'before')
    queries = hydrate(offered, members)
    combined = []
    for source, qs in zip(('offering', 'class'), queries):
        if cursor:
            compare = 'gt' if before else 'lt'
            condition = Q(**{'created_at__' + compare: boundary_time}) | Q(created_at=boundary_time, **{'pk__' + compare: boundary_id})
            if (source > cursor['source']) if before else (source < cursor['source']):
                condition |= Q(created_at=boundary_time, pk=boundary_id)
            qs = qs.filter(condition)
        order = ('created_at', 'pk') if before else ('-created_at', '-pk')
        combined.extend((obj, source) for obj in qs.order_by(*order)[:size + 1])
    combined.sort(key=lambda pair: (pair[0].created_at, str(pair[0].pk), pair[1]), reverse=not before)
    more = len(combined) > size
    page = combined[:size]
    if before:
        page.reverse()
    def make_cursor(pair, direction):
        obj, source = pair
        return signing.dumps({'time': obj.created_at.isoformat(), 'id': str(obj.pk), 'source': source, 'direction': direction, 'filter': filters.fingerprint()}, salt='registration-directory')
    result = {'results': [registration_row(obj, source, scope) for obj, source in page],
              'next_cursor': make_cursor(page[-1], 'after') if page and (bool(cursor) if before else more) else None,
              'previous_cursor': make_cursor(page[0], 'before') if page and (more if before else bool(cursor)) else None}
    if not cursor:
        total, active, pending = 0, 0, 0
        for source, qs in zip(('offering', 'class'), (offered, members)):
            values = qs.aggregate(total=Count('pk'), active=Count('pk', filter=Q(is_active=True)), pending=Count('pk', filter=Q(lifecycle_status='pending')) if source == 'offering' else Count('pk', filter=Q(pk__isnull=True)))
            total += values['total']; active += values['active']; pending += values['pending']
        result['summary'] = {'total': total, 'active': active, 'inactive': total - active, 'pending': pending}
    return result


def get_registration(scope, source, pk):
    if source not in {'offering', 'class'} or not scope.permissions[source]['view']:
        raise PermissionDenied('مجوز مشاهدهٔ این ثبت‌نام را ندارید.')
    roots = scope.roots()
    # Direct linked membership URLs resolve through their visible canonical parent.
    if source == 'class':
        parent = roots[0].filter(final_class_enrollment_id=pk).first()
        if parent:
            source, pk = 'offering', parent.pk
    queries = hydrate(*roots)
    obj = queries[0 if source == 'offering' else 1].filter(pk=pk).first()
    if obj is None:
        raise Http404('ثبت‌نام یافت نشد.')
    return obj, source


def registration_detail(scope, source, pk):
    obj, source = get_registration(scope, source, pk)
    row = registration_row(obj, source, scope)
    target = Q(session__offering_id=row['offering']['id']) if row['offering'] else Q(pk__in=[])
    if row['class_group']:
        target |= Q(session__class_group_id=row['class_group']['id'])
    attendance = AttendanceRecord.objects.filter(target, student=obj.student, is_deleted=False, session__is_deleted=False)
    row['attendance'] = list(attendance.order_by().values('status').annotate(total=Count('pk')))
    from django.contrib.contenttypes.models import ContentType
    events = AuditEvent.objects.filter(content_type=ContentType.objects.get_for_model(obj), object_id=str(obj.pk)).select_related('actor').order_by('-created_at')[:20]
    row['history'] = [{'summary': event.summary, 'date': event.created_at_jalali, 'actor': event.actor.get_full_name() if event.actor else 'سامانه'} for event in events]
    if source == 'offering':
        membership = obj.final_class_enrollment
        capacity_target = membership.class_group if membership else obj.offering
    else:
        capacity_target = obj.class_group
    row['capacity'] = entity_capacity(capacity_target)
    return row


def entity_capacity(obj):
    active = obj.enrollments.filter(is_active=True, is_deleted=False).count()
    return {'total': obj.capacity or None, 'enrolled': active, 'remaining': max(obj.capacity - active, 0) if obj.capacity else None,
            'full': bool(obj.capacity and active >= obj.capacity)}


def entity_context(scope, kind, pk):
    kind = {'people': 'person', 'courses': 'course', 'offerings': 'offering', 'classes': 'class'}.get(kind, kind)
    if kind == 'person':
        if not scope.person_links:
            raise PermissionDenied('مجوز مشاهدهٔ شخص را ندارید.')
        a, b = scope.roots()
        qs = Person.objects.filter(is_deleted=False)
        if not scope.staff:
            qs = qs.filter(Q(pk__in=a.values('student_id')) | Q(pk__in=b.values('student_id')) | Q(pk=getattr(scope.person, 'pk', None)))
        obj = qs.filter(pk=pk).first()
        if obj is None: raise Http404
        return {'kind': kind, 'title': obj.display_name, 'identity': scope.identity(obj), 'filters': {'student': str(obj.pk)}, 'capacity': None}
    if kind == 'course':
        qs = Course.objects.filter(is_deleted=False).filter(Q(pk__in=scope.offerings().values('course_id')) | Q(pk__in=scope.classes().values('offering__course_id')))
        model_key, field = 'education.course', 'course'
    elif kind == 'offering':
        qs, model_key, field = scope.offerings().select_related('course'), 'education.courseoffering', 'offering'
    elif kind == 'class':
        qs, model_key, field = scope.classes().select_related('term', 'offering__course'), 'academics.classgroup', 'class_group'
    else:
        raise Http404
    if not acl_strict(scope.user, 'model', model_key, 'view', True):
        raise PermissionDenied('مجوز مشاهدهٔ این مورد را ندارید.')
    obj = qs.filter(pk=pk).first()
    if obj is None: raise Http404
    data = {'kind': kind, 'title': getattr(obj, 'title', '') or getattr(obj, 'name', '') or str(obj), 'code': obj.code,
            'filters': {field: str(obj.pk)}, 'capacity': None, 'description': getattr(obj, 'description', ''), 'links': [],
            'can_add': scope.permissions['class' if kind == 'class' else 'offering']['add']}
    if kind in {'offering', 'class'}:
        data['capacity'] = entity_capacity(obj)
        data['status'] = obj.get_status_display() if kind == 'offering' else ('فعال' if obj.is_active else 'غیرفعال')
        offering = obj if kind == 'offering' else obj.offering
        if offering:
            data['links'].append({'title': offering.course.title, 'url': f'/workspace/enrollments/courses/{offering.course_id}/'})
            if kind == 'class': data['links'].append({'title': offering.title or offering.code, 'url': f'/workspace/enrollments/offerings/{offering.pk}/'})
        if kind == 'class': data['term'] = obj.term.title
    return data


def picker_options(scope, params):
    kind = params.get('kind', 'student')
    selected = _clean_uuid(params.get('selected'))
    search = english_numbers(params.get('q', '').strip())[:128]
    if kind == 'student':
        a, b = scope.roots()
        qs = Person.objects.filter(is_deleted=False)
        if not scope.staff:
            qs = qs.filter(Q(pk__in=a.values('student_id')) | Q(pk__in=b.values('student_id')) | Q(pk=getattr(scope.person, 'pk', None)))
        if params.get('for_create') == 'true':
            from apps.persons.models import PersonTypeAssignment
            qs = qs.filter(Q(person_type='student') | Q(pk__in=PersonTypeAssignment.objects.filter(type='student', is_deleted=False, is_active=True).values('person_id')))
        if search:
            cond = Q(first_name__istartswith=search) | Q(last_name__istartswith=search) | Q(student_code__istartswith=search)
            if scope.full_identity: cond |= Q(national_code__startswith=search)
            qs = qs.filter(cond)
        order = ('last_name', 'first_name', 'pk')
    elif kind == 'class_group':
        qs = scope.classes()
        offering = _clean_uuid(params.get('offering'))
        if offering:
            qs = qs.filter(Q(offering_id=offering) | Q(offering__isnull=True))
        if search: qs = qs.filter(Q(name__istartswith=search) | Q(code__istartswith=search))
        order = ('name', 'pk')
    elif kind == 'offering':
        qs = scope.offerings().select_related('course')
        course = _clean_uuid(params.get('course'))
        if course: qs = qs.filter(course_id=course)
        if search: qs = qs.filter(Q(title__istartswith=search) | Q(code__istartswith=search) | Q(course__title__istartswith=search))
        order = ('title', 'pk')
    elif kind == 'course':
        qs = Course.objects.filter(is_deleted=False).filter(Q(pk__in=scope.offerings().values('course_id')) | Q(pk__in=scope.classes().values('offering__course_id')))
        if search: qs = qs.filter(Q(title__istartswith=search) | Q(code__istartswith=search))
        order = ('title', 'pk')
    else:
        raise ReportFilterError('نوع فهرست معتبر نیست.')
    if selected: qs = qs.filter(pk=selected)
    rows = list(qs.order_by(*order)[:31])
    def label(obj):
        if kind == 'student': return obj.display_name + (' · ' + obj.student_code if obj.student_code else '')
        return (getattr(obj, 'title', '') or getattr(obj, 'name', '') or obj.code) + ' · ' + obj.code
    return {'results': [{'id': str(obj.pk), 'label': label(obj)} for obj in rows[:30]], 'has_more': len(rows) > 30}
