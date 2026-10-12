"""Free registrations remain distinct from discounts and the payment ledger."""
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.models import AuditEvent
from apps.education.models import Course, CourseOffering, OfferingEnrollment
from apps.education.services import (
    EducationServiceError, create_offering_enrollment, record_enrollment_payment,
    request_enrollment_refund,
)
from apps.forms.tests.factories import UserFactory, make_person
from apps.org.models import PersonACLEntry
from apps.reports.selectors.reports import ReportFilters, financial_report


class FreeEnrollmentTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(roles=['manager'])
        self.manager.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='education', content_type__model='offeringenrollment',
        ))
        self.student = make_person()
        self.course = Course.objects.create(title='دوره آزمایشی')
        self.offering = CourseOffering.objects.create(
            course=self.course, title='دوره پاییز', capacity=5, status=CourseOffering.Status.OPEN,
        )
        self.client = APIClient()
        self.client.force_login(self.manager)

    def payload(self, **changes):
        return {'offering': str(self.offering.pk), 'student': str(self.student.pk),
                'course_amount': 100000, 'is_free': True, **changes}

    def create_free(self):
        return create_offering_enrollment(
            offering=self.offering, student=self.student, actor=self.manager,
            course_amount=100000, is_free=True, free_reason='بورسیه آموزشی',
        )

    def test_authorized_api_creation_has_no_debt_or_payment_and_records_audit(self):
        response = self.client.post('/api/education/enrollments/', self.payload(
            payments=[], free_reason='بورسیه آموزشی', final_amount=99999,
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        enrollment = OfferingEnrollment.objects.get(pk=response.data['id'])
        self.assertTrue(enrollment.is_free)
        self.assertEqual(enrollment.final_amount, 0)
        self.assertEqual(enrollment.course_amount, 100000)
        self.assertEqual(enrollment.discount_type, 'none')
        self.assertEqual(enrollment.discount_value, 0)
        self.assertEqual(enrollment.lifecycle_status, 'confirmed')
        self.assertFalse(enrollment.payments.exists())
        self.offering.refresh_from_db()
        self.assertEqual(self.offering.enrolled_count, 1)
        audit = AuditEvent.objects.get(object_id=str(enrollment.pk))
        self.assertEqual(audit.actor, self.manager)
        self.assertEqual(audit.metadata['free_reason'], 'بورسیه آموزشی')

    def test_free_creation_needs_no_reason_or_payment_field(self):
        response = self.client.post('/api/education/enrollments/', self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['final_amount'], 0)

    def test_free_api_rejects_discounts_and_payment_details_atomically(self):
        for changes in (
            {'discount_type': 'percent', 'discount_value': 100},
            {'payments': [{'method': 'cash', 'amount': 1}]},
            {'payment_method': 'pos'}, {'reference': 'fake receipt'},
            {'cheques': [{'amount': 1}]}, {'cheque_count': 1},
        ):
            with self.subTest(changes=changes):
                response = self.client.post('/api/education/enrollments/', self.payload(**changes), format='json')
                self.assertEqual(response.status_code, 400, response.data)
                self.assertFalse(OfferingEnrollment.objects.exists())
        self.offering.refresh_from_db()
        self.assertEqual(self.offering.enrolled_count, 0)

    def test_role_without_model_permission_cannot_create_or_see_option(self):
        user = UserFactory(roles=['manager'])
        self.client.force_login(user)
        response = self.client.post('/api/education/enrollments/', self.payload(), format='json')
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(self.client.get('/workspace/enrollments/'), 'id="enr-is-free"')
        with self.assertRaises(PermissionDenied):
            create_offering_enrollment(offering=self.offering, student=self.student, actor=user, is_free=True)

    def test_employee_with_model_permission_is_still_denied(self):
        employee = UserFactory(roles=['employee'])
        employee.user_permissions.add(Permission.objects.get(
            content_type__app_label='education', codename='add_offeringenrollment',
        ))
        self.client.force_login(employee)
        self.assertEqual(self.client.post('/api/education/enrollments/', self.payload(), format='json').status_code, 403)
        self.assertNotContains(self.client.get('/workspace/enrollments/'), 'id="enr-is-free"')

    def test_explicit_acl_denial_controls_form_and_server(self):
        PersonACLEntry.objects.create(
            user=self.manager, resource_type='model', resource_key='education.offeringenrollment', verbs=['view'],
        )
        self.assertNotContains(self.client.get('/workspace/enrollments/'), 'id="enr-is-free"')
        self.assertEqual(self.client.post('/api/education/enrollments/', self.payload(), format='json').status_code, 403)

    def test_authorized_form_shows_option(self):
        self.assertContains(self.client.get('/workspace/enrollments/'), 'id="enr-is-free"')

    def test_free_enrollment_cannot_receive_payment_or_refund(self):
        enrollment = self.create_free()
        response = self.client.post(f'/api/education/enrollments/{enrollment.pk}/payments/',
                                    {'amount': 1, 'method': 'cash'}, format='json')
        self.assertEqual(response.status_code, 400, response.data)
        with self.assertRaises(EducationServiceError):
            record_enrollment_payment(enrollment=enrollment, actor=self.manager, payment={'amount': 1, 'method': 'cash'})
        with self.assertRaises(EducationServiceError):
            request_enrollment_refund(enrollment=enrollment, amount=1, requested_by=self.manager)
        self.assertFalse(enrollment.payments.exists())
        self.assertFalse(enrollment.refunds.exists())

    def test_service_rejects_payment_lines_and_discounts(self):
        for changes in ({'payment_lines': [{'amount': 1, 'method': 'cash'}]}, {'discount_value': 100}):
            with self.subTest(changes=changes), self.assertRaises(EducationServiceError):
                create_offering_enrollment(offering=self.offering, student=self.student,
                                          actor=self.manager, is_free=True, **changes)

    def test_retry_does_not_duplicate_capacity_audit_or_money(self):
        first = self.create_free()
        second = self.create_free()
        self.assertEqual(first.pk, second.pk)
        self.offering.refresh_from_db()
        self.assertEqual(self.offering.enrolled_count, 1)
        self.assertEqual(AuditEvent.objects.filter(object_id=str(first.pk)).count(), 1)
        self.assertFalse(first.payments.exists())

    def test_free_status_is_visible_in_detail_directory_and_finance(self):
        enrollment = self.create_free()
        detail = self.client.get(f'/api/education/registration-directory/records/offering/{enrollment.pk}/')
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertTrue(detail.data['is_free'])
        self.assertEqual(detail.data['history'][0]['reason'], 'بورسیه آموزشی')
        directory = self.client.get('/api/education/registration-directory/')
        self.assertTrue(directory.data['results'][0]['is_free'])
        finances = self.client.get('/api/education/enrollments/?is_free=true')
        self.assertEqual(finances.status_code, 200, finances.data)
        self.assertEqual(finances.data['results'][0]['id'], str(enrollment.pk))
        self.assertEqual(self.client.get('/api/education/payments/').data['results'], [])
        self.assertContains(self.client.get('/workspace/enrollments/payments/'), 'ثبت‌نام‌های رایگان')

    def test_financial_report_does_not_count_free_as_paid(self):
        self.create_free()
        totals = financial_report(self.manager, ReportFilters.from_query({}))['totals']
        self.assertEqual(totals['free_count'], 1)
        self.assertEqual(totals['paid_count'], 0)
        self.assertEqual(totals['revenue'], 0)
        self.assertEqual(totals['pending_amount'], 0)

    def test_free_status_cannot_be_changed_or_payment_details_added_on_update(self):
        enrollment = self.create_free()
        for changes in ({'is_free': False}, {'discount_value': 1}, {'payment_method': 'cheque'}, {'reference': 'receipt'}):
            with self.subTest(changes=changes):
                response = self.client.patch(f'/api/education/enrollments/{enrollment.pk}/', changes, format='json')
                self.assertEqual(response.status_code, 400, response.data)
        response = self.client.patch(f'/api/education/enrollments/{enrollment.pk}/', {'course_amount': 200000}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.final_amount, 0)

    def test_database_refuses_positive_debt_for_free_enrollment(self):
        enrollment = self.create_free()
        with self.assertRaises(IntegrityError), transaction.atomic():
            OfferingEnrollment.objects.filter(pk=enrollment.pk).update(final_amount=1)

    def test_normal_discount_and_installment_work_as_before(self):
        response = self.client.post('/api/education/enrollments/', self.payload(
            is_free=False, discount_type='percent', discount_value=10,
            payments=[{'method': 'pos', 'amount': 40000}],
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        enrollment = OfferingEnrollment.objects.get(pk=response.data['id'])
        self.assertFalse(enrollment.is_free)
        self.assertEqual(enrollment.final_amount, 90000)
        self.assertEqual(enrollment.payments.get().amount, 40000)
        payment = self.client.post(f'/api/education/enrollments/{enrollment.pk}/payments/',
                                  {'method': 'cash', 'amount': 50000}, format='json')
        self.assertEqual(payment.status_code, 201, payment.data)
        self.assertEqual(payment.data['remaining_balance'], 0)
        forbidden = self.client.patch(f'/api/education/enrollments/{enrollment.pk}/', {'is_free': True}, format='json')
        self.assertEqual(forbidden.status_code, 400)

    def test_full_discount_is_distinct_from_free_and_remains_supported(self):
        response = self.client.post('/api/education/enrollments/', self.payload(
            is_free=False, discount_type='percent', discount_value=100,
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data['is_free'])
        self.assertEqual(response.data['discount_value'], 100)
        self.assertEqual(response.data['final_amount'], 0)
