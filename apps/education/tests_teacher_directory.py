import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.academics.models import AcademicTerm, ClassGroup
from apps.education.models import Course, CourseOffering, ClassSession
from apps.forms.tests.factories import UserFactory, make_person


class TeacherDirectoryTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username='teacher-directory-manager', roles=['manager'])
        self.teacher = make_person(person_type='teacher', first_name='مدرس', last_name='الف')
        self.other = make_person(person_type='teacher', first_name='مدرس', last_name='دیگر')
        self.course = Course.objects.create(title='زبان')
        self.running = CourseOffering.objects.create(course=self.course, instructor=self.teacher, status='running')
        self.open = CourseOffering.objects.create(course=self.course, instructor=self.teacher, status='open')
        self.foreign = CourseOffering.objects.create(course=self.course, instructor=self.other, status='running')
        self.term = AcademicTerm.objects.create(title='پاییز', start_date='2026-09-01', end_date='2026-12-31')
        self.group = ClassGroup.objects.create(term=self.term, teacher=self.teacher, name='کلاس مستقل', code='independent')
        self.client = APIClient()
        self.client.force_login(self.manager)

    def context(self, person=None):
        return self.client.get(f'/api/education/registration-directory/context/teacher/{(person or self.teacher).pk}/')

    def test_manager_sees_teacher_without_user_account_and_own_assignments(self):
        response = self.context()
        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data['kind'], 'teacher')
        self.assertEqual(data['identity']['id'], str(self.teacher.pk))
        self.assertEqual({row['id'] for row in data['teaching']['offerings']}, {str(self.running.pk), str(self.open.pk)})
        self.assertEqual(data['teaching']['summary'], {'offerings': 2, 'running': 1, 'preregistration': 1, 'classes': 1})
        self.assertEqual(data['teaching']['classes'][0]['id'], str(self.group.pk))

    def test_management_page_uses_reference_template(self):
        response = self.client.get(f'/workspace/enrollments/teacher/{self.teacher.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'registration-teaching-content')
        self.assertContains(response, 'دوره‌ها و کلاس‌های مدرس')
        self.assertContains(response, '"kind": "teacher"')

    def test_assignment_by_class_and_session_and_soft_delete(self):
        group = ClassGroup.objects.create(term=self.term, offering=self.foreign, teacher=self.teacher, name='انتساب کلاسی', code='assigned')
        data = self.context().json()['teaching']
        self.assertIn(str(self.foreign.pk), {row['id'] for row in data['offerings']})
        self.assertEqual(next(row for row in data['offerings'] if row['id'] == str(self.foreign.pk))['assignment_label'], 'مدرس کلاس')
        group.is_deleted = True
        group.save()
        self.assertNotIn(str(self.foreign.pk), {row['id'] for row in self.context().json()['teaching']['offerings']})
        session = ClassSession.objects.create(offering=self.foreign, teacher=self.teacher, session_number=1,
                                             session_date=datetime.date(2026, 11, 1), start_time=datetime.time(10), end_time=datetime.time(11))
        self.assertIn(str(self.foreign.pk), {row['id'] for row in self.context().json()['teaching']['offerings']})
        session.is_deleted = True
        session.save()
        self.assertNotIn(str(self.foreign.pk), {row['id'] for row in self.context().json()['teaching']['offerings']})

    def test_reassignment_and_empty_profile(self):
        self.running.instructor = self.other
        self.running.save()
        self.assertNotIn(str(self.running.pk), {row['id'] for row in self.context().json()['teaching']['offerings']})
        empty = make_person(person_type='teacher')
        response = self.context(empty)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['teaching']['offerings'], [])
        self.assertEqual(response.json()['teaching']['classes'], [])

    def test_non_teacher_or_deleted_teacher_returns_not_found(self):
        student = make_person(person_type='student')
        self.assertEqual(self.context(student).status_code, 404)
        self.teacher.is_deleted = True
        self.teacher.save()
        self.assertEqual(self.context().status_code, 404)

    def test_learner_and_foreign_teacher_cannot_read_teacher_profile(self):
        for role in ('teacher', 'student'):
            user = UserFactory(username='teacher-directory-' + role, roles=[role])
            make_person(user=user, person_type=role)
            self.client.force_login(user)
            self.assertEqual(self.context().status_code, 404)
            self.assertIn(self.client.get(f'/workspace/enrollments/teacher/{self.teacher.pk}/').status_code, (403, 404))

    def test_multi_role_person_with_teacher_assignment_has_profile(self):
        from apps.persons.models import PersonTypeAssignment
        person = make_person(person_type='employee')
        PersonTypeAssignment.objects.create(person=person, type='teacher')
        self.assertEqual(self.context(person).status_code, 200)
