import datetime as dt
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import AcademicTerm, ClassEnrollment, ClassGroup
from apps.accounts.models import Role, UserRole
from apps.core.access_catalog import get_resource
from apps.core.sidebar import SIDEBAR_ITEMS
from apps.education.models import Course, CourseOffering, OfferingEnrollment
from apps.org.models import PersonACLEntry
from apps.persons.models import Person
from apps.reports.permissions import CAPACITY_REPORT_RESOURCE
from apps.reports.selectors.enrollment_capacity import CapacityFilters, report_query, report_rows, report_summary, row_data


class EnrollmentCapacityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username='capacity-admin', password='test-only')
        cls.course = Course.objects.create(code='capacity-course', title='دورهٔ آزمایشی')
        cls.full = CourseOffering.objects.create(course=cls.course, code='full', title='تکمیل', capacity=2, enrolled_count=2, status='open')
        cls.available = CourseOffering.objects.create(course=cls.course, code='available', title='دارای ظرفیت', capacity=10, enrolled_count=1, status='running')
        cls.unlimited = CourseOffering.objects.create(course=cls.course, code='unlimited', title='نامحدود', capacity=0, enrolled_count=1)
        cls.today = timezone.localdate()
        cls.students = [Person.objects.create(national_code=f'70000000{i:02}', first_name='دانش‌آموز', last_name=str(i), person_type='student') for i in range(8)]
        for i, offering in enumerate([cls.full, cls.full, cls.available, cls.unlimited]):
            OfferingEnrollment.objects.create(offering=offering, student=cls.students[i], enrolled_at=cls.today if i != 1 else cls.today - dt.timedelta(days=60))
        OfferingEnrollment.objects.create(offering=cls.available, student=cls.students[4], is_active=False, lifecycle_status='cancelled', enrolled_at=cls.today)
        OfferingEnrollment.objects.create(offering=cls.available, student=cls.students[5], is_deleted=True, enrolled_at=cls.today)
        cls.term = AcademicTerm.objects.create(title='ترم آزمایشی', start_date=cls.today, end_date=cls.today + dt.timedelta(days=90))
        cls.group = ClassGroup.objects.create(term=cls.term, name='گروه اول', code='group-1', capacity=3)
        ClassEnrollment.objects.create(class_group=cls.group, student=cls.students[0], enrollment_date=cls.today)
        ClassEnrollment.objects.create(class_group=cls.group, student=cls.students[1], enrollment_date=cls.today, is_active=False)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def fetch(self, **params):
        response = self.client.get('/api/reports/enrollment-capacity/', params)
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def user(self, role):
        user = get_user_model().objects.create_user(username=role)
        role_obj, _ = Role.objects.get_or_create(code=role, defaults={'name': role})
        UserRole.objects.create(user=user, role=role_obj)
        return user

    def acl(self, user, verbs):
        return PersonACLEntry.objects.create(user=user, resource_type='page', resource_key=CAPACITY_REPORT_RESOURCE, verbs=verbs)

    def test_totals_and_current_capacity_are_independent_of_date_range(self):
        data = self.fetch(**{'from': self.today.isoformat(), 'to': self.today.isoformat()})
        totals = data['overview']['totals']
        self.assertEqual(totals, dict(total=3, enrolled=4, capacity=12, remaining=9, full=1, unlimited=1, available=2, registrations=3))
        rows = {row['code']: row for row in data['results']}
        self.assertEqual(rows['full']['enrolled'], 2)
        self.assertEqual(rows['full']['period_enrollments'], 1)
        self.assertIsNone(rows['unlimited']['remaining'])
        self.assertFalse(rows['unlimited']['full'])
        self.assertEqual(sum(row['total'] for row in data['overview']['trend']), 3)

    def test_refunded_or_deleted_memberships_do_not_rely_on_stale_counter(self):
        OfferingEnrollment.objects.filter(offering=self.full, student=self.students[0]).update(is_active=False, lifecycle_status='refunded')
        row = self.fetch(classroom=str(self.full.pk))['results'][0]
        self.assertEqual(row['enrolled'], 1)
        self.assertEqual(row['remaining'], 1)
        self.assertFalse(row['full'])

    def test_capacity_status_course_and_class_filters(self):
        self.assertEqual(self.fetch(capacity='full')['overview']['totals']['total'], 1)
        self.assertEqual(self.fetch(capacity='available')['overview']['totals']['total'], 2)
        self.assertEqual(self.fetch(status='running')['results'][0]['code'], 'available')
        self.assertEqual(len(self.fetch(course=str(self.course.pk), classroom=str(self.full.pk))['results']), 1)
        self.assertEqual(self.fetch(classroom='00000000-0000-0000-0000-000000000000')['overview']['totals']['total'], 0)

    def test_class_groups_count_only_live_active_memberships(self):
        data = self.fetch(source='classes')
        self.assertEqual(data['results'][0]['enrolled'], 1)
        self.assertEqual(data['results'][0]['remaining'], 2)
        self.assertEqual(data['overview']['totals']['registrations'], 1)

    def test_cursor_pages_do_not_repeat_overview_aggregates(self):
        data = self.fetch(page_size=1)
        seen = {data['results'][0]['id']}
        while data['next']:
            url = urlsplit(data['next'])
            response = self.client.get(url.path + '?' + url.query)
            self.assertEqual(response.status_code, 200)
            data = response.data
            self.assertNotIn('overview', data)
            self.assertNotIn(data['results'][0]['id'], seen)
            seen.add(data['results'][0]['id'])
        self.assertEqual(len(seen), 3)

    def test_invalid_filters_are_400_not_server_errors(self):
        for params in [{'course': 'invalid'}, {'from': 'bad'}, {'from': '2026-01-02', 'to': '2026-01-01'}, {'source': 'bad'}, {'capacity': 'bad'}, {'status': 'invalid'}, {'from': '2020-01-01', 'to': '2026-01-01'}]:
            with self.subTest(params=params):
                self.assertEqual(self.client.get('/api/reports/enrollment-capacity/', params).status_code, 400)

    def test_acl_denial_applies_to_api_options_and_page(self):
        manager = self.user('manager')
        self.acl(manager, [])
        self.client.force_authenticate(manager)
        for url in ['/api/reports/enrollment-capacity/', '/api/reports/enrollment-capacity/options/']:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(manager)
        self.assertEqual(self.client.get('/workspace/reports/enrollment-capacity/').status_code, 403)

    def test_employee_requires_explicit_grant_and_student_never_gets_totals(self):
        employee = self.user('employee')
        self.client.force_authenticate(employee)
        self.assertEqual(self.client.get('/api/reports/enrollment-capacity/').status_code, 403)
        self.acl(employee, ['view'])
        self.assertEqual(self.fetch()['overview']['totals']['total'], 3)
        student = self.user('student')
        self.acl(student, ['view'])
        self.client.force_authenticate(student)
        self.assertEqual(self.fetch()['overview']['totals']['total'], 0)

    def test_teacher_grant_still_limits_report_and_options_to_own_classes(self):
        teacher = self.user('teacher')
        person = Person.objects.create(user=teacher, national_code='7900000000', first_name='مدرس', last_name='آزمایش', person_type='teacher')
        CourseOffering.objects.filter(pk=self.full.pk).update(instructor=person)
        self.acl(teacher, ['view'])
        self.client.force_authenticate(teacher)
        self.assertEqual(self.fetch()['overview']['totals']['total'], 1)
        options = self.client.get('/api/reports/enrollment-capacity/options/', {'kind': 'classroom'}).data
        self.assertEqual([row['id'] for row in options['results']], [str(self.full.pk)])

    def test_inactive_user_is_denied_even_with_explicit_grant(self):
        employee = self.user('employee')
        self.acl(employee, ['view'])
        employee.is_active = False
        self.client.force_authenticate(employee)
        self.assertEqual(self.client.get('/api/reports/enrollment-capacity/').status_code, 403)

    def test_query_budget_is_independent_of_row_count(self):
        filters = CapacityFilters.parse({})
        qs, registrations, fk, date_field = report_query(self.admin, filters)
        for count in [1, 100]:
            with CaptureQueriesContext(connection) as queries:
                rows = [row_data(row, 'offerings') for row in report_rows(qs, 'offerings')[:count]]
            self.assertTrue(rows)
            self.assertEqual(len(queries), 1)
        with CaptureQueriesContext(connection) as queries:
            report_summary(qs, registrations, fk, date_field, filters)
        self.assertEqual(len(queries), 2)
        filters = CapacityFilters.parse({'source': 'classes'})
        qs, _, _, _ = report_query(self.admin, filters)
        with self.assertNumQueries(1):
            list(row_data(row, 'classes') for row in report_rows(qs, 'classes')[:100])

    def test_options_are_bounded_and_permission_registered_in_settings(self):
        CourseOffering.objects.bulk_create([CourseOffering(course=self.course, code=f'extra-{i}', title=f'برگزاری {i}') for i in range(35)])
        response = self.client.get('/api/reports/enrollment-capacity/options/', {'kind': 'classroom'})
        self.assertEqual(len(response.data['results']), 30)
        self.assertTrue(response.data['has_more'])
        self.assertIsNotNone(get_resource('page', CAPACITY_REPORT_RESOURCE))
        self.assertTrue(any(item['key'] == CAPACITY_REPORT_RESOURCE for item in SIDEBAR_ITEMS))

    def test_jalali_dates_and_saturday_week_grouping(self):
        filters = CapacityFilters.parse({'from': '۱۴۰۵/۰۷/۰۴', 'to': '۱۴۰۵/۰۷/۰۴', 'group': 'week'})
        self.assertEqual(filters.start, dt.date(2026, 9, 26))
        qs, regs, fk, date_field = report_query(self.admin, filters)
        self.assertEqual(report_summary(qs, regs, fk, date_field, filters)['trend'][0]['label'], 'هفتهٔ 1405/07/04')

    def test_page_renders_for_superuser(self):
        self.client.force_login(self.admin)
        response = self.client.get('/workspace/reports/enrollment-capacity/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'capacity-endpoints')
