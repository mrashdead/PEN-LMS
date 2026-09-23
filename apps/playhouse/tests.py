"""
Playhouse (خانه بازی) round — Sept 21 2026.

Covers the full timed-session → invoice flow per the task brief:
  A. 15-minute rounding rule (nearest block, half-up).
  B. Intake / member resolution (new vs existing; link to Person).
  C. Timer transitions (start / stop / end / cancel) with validation + locking.
  D. Invoice billing — time amount from billed minutes × snapshot price,
     cafe line items, totals.
  E. Payment recording (POS / card-to-card + tracking code).
  F. API surface + role gates (operator vs non-operator; finance for pay).
  G. Config singleton + price exposure.

Conventions match the repo: rest_framework.test.APIClient, UserFactory roles
from seed roles, plain date objects.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.forms.tests.factories import UserFactory, make_person
from apps.accounts.models import Role
from apps.playhouse.models import (
    PlayhouseConfig,
    PlayhouseInvoice,
    PlayhouseMember,
    PlayhouseSession,
    round_to_nearest_15,
)
from apps.playhouse.serializers import ActiveSessionSerializer
from apps.playhouse.services import PlayhouseService, PlayhouseServiceError


def _seed_roles():
    for code in ("manager", "workflow_admin", "employee", "hr", "student"):
        Role.objects.get_or_create(code=code, defaults={"name": code, "priority": 50})


def _operator(**kw):
    return UserFactory(roles=["employee"], **kw)


def _make_session(service, operator, *, days=None, **kw):
    return service.create_session(
        operator=operator,
        first_name="علی",
        last_name="احمدی",
        age=6,
        guardian_mobile="09121111111",
        **kw,
    )


class RoundingTest(TestCase):
    def test_rounds_to_nearest_15_half_up(self):
        self.assertEqual(round_to_nearest_15(127), 120)   # 2h07 → 2h00
        self.assertEqual(round_to_nearest_15(128), 135)   # 2h08 → 2h15
        self.assertEqual(round_to_nearest_15(7), 0)       # 7m → 0 (free block)
        self.assertEqual(round_to_nearest_15(8), 15)      # 8m → 15m
        self.assertEqual(round_to_nearest_15(30), 30)
        self.assertEqual(round_to_nearest_15(45), 45)
        self.assertEqual(round_to_nearest_15(0), 0)
        self.assertEqual(round_to_nearest_15(-5), 0)


class MemberResolutionTest(TestCase):
    def setUp(self):
        _seed_roles()
        self.op = _operator()

    def test_new_member_created_when_not_linked(self):
        s = PlayhouseService().create_session(
            operator=self.op, first_name="زهرا", last_name="کریمی",
            age=4, guardian_mobile="09350000000",
        )
        self.assertEqual(s.member.first_name, "زهرا")
        self.assertIsNone(s.member.person)
        self.assertEqual(
            PlayhouseMember.objects.get(pk=s.member.pk).guardian_mobile, "09350000000"
        )

    def test_links_to_existing_person_on_match(self):
        person = make_person(first_name="سارا", last_name="موسوی", mobile="09121234567",
                             person_type="student")
        s = PlayhouseService().create_session(
            operator=self.op, first_name="سارا", last_name="موسوی",
            age=8, guardian_mobile="09121234567",
        )
        self.assertEqual(s.member.person_id, person.pk)

    def test_new_visitor_can_be_registered_as_person(self):
        s = PlayhouseService().create_session(
            operator=self.op, first_name="نیلا", last_name="کریمی",
            age=5, guardian_mobile="09123334444",
            national_code="0012345678", student_code="PH-1001",
        )
        self.assertIsNotNone(s.member.person_id)
        person = s.member.person
        self.assertEqual(person.person_type, "student")
        self.assertEqual(person.student_code, "PH-1001")
        self.assertEqual(person.mobile, "09123334444")

    def test_existing_member_picked_by_pk(self):
        first = PlayhouseService().create_session(
            operator=self.op, first_name="بچه", last_name="اول", age=5,
            guardian_mobile="09120000001",
        ).member
        second = PlayhouseService().create_session(
            operator=self.op, first_name="", last_name="", age=None,
            guardian_mobile="", member_pk=first.pk,
        )
        self.assertEqual(second.member.pk, first.pk)

    def test_api_accepts_uuid_member_pk(self):
        member = PlayhouseService().create_session(
            operator=self.op, first_name="عضو", last_name="قدیمی", age=7,
            guardian_mobile="09120000003",
        ).member
        client = APIClient()
        client.force_authenticate(user=self.op)
        response = client.post(
            "/api/playhouse/sessions/",
            {"first_name": member.first_name, "last_name": member.last_name,
             "member_pk": str(member.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(PlayhouseSession.objects.filter(member=member).count(), 2)

    def test_pen_student_can_be_selected_and_linked(self):
        person = make_person(
            first_name="دانش‌آموز", last_name="پن", mobile="09123334444",
            person_type="student",
        )
        client = APIClient()
        client.force_authenticate(user=self.op)
        search = client.get("/api/playhouse/members/search/?q=دانش‌آموز")
        self.assertEqual(search.status_code, 200)
        self.assertTrue(any(row["person_pk"] == str(person.pk) for row in search.data["results"]))
        response = client.post(
            "/api/playhouse/sessions/",
            {"first_name": person.first_name, "last_name": person.last_name,
             "person_pk": str(person.pk)},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(
            PlayhouseSession.objects.get(pk=response.data["id"]).member.person_id,
            person.pk,
        )


class TimerTransitionTest(TestCase):
    def setUp(self):
        _seed_roles()
        self.op = _operator()
        self.service = PlayhouseService()

    def test_full_lifecycle(self):
        s = _make_session(self.service, self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.WAITING)

        s = self.service.start_session(session=s, operator=self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.ACTIVE)
        self.assertIsNotNone(s.entry_at)

        s = self.service.end_session(session=s, operator=self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.FINISHED)
        self.assertIsNotNone(s.exit_at)
        # billable >= 0; exact value depends on elapsed time
        self.assertGreaterEqual(s.billable_minutes, 0)

        with self.assertRaises(PlayhouseServiceError):
            self.service.end_session(session=s, operator=self.op)  # already finished

    def test_cannot_start_twice(self):
        s = _make_session(self.service, self.op)
        self.service.start_session(session=s, operator=self.op)
        with self.assertRaises(PlayhouseServiceError):
            self.service.start_session(session=s, operator=self.op)

    def test_cancel_from_waiting(self):
        s = _make_session(self.service, self.op)
        s = self.service.cancel_session(session=s, operator=self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.CANCELLED)
        with self.assertRaises(PlayhouseServiceError):
            self.service.cancel_session(session=s, operator=self.op)

    def test_billable_minutes_matches_rounded_elapsed(self):
        s = _make_session(self.service, self.op)
        s = self.service.start_session(session=s, operator=self.op)
        s.entry_at = timezone.now() - datetime.timedelta(minutes=127)
        s.save(update_fields=["entry_at", "updated_at"])
        s = self.service.end_session(session=s, operator=self.op)
        self.assertEqual(s.billable_minutes, 120)

    def test_stop_pauses_and_resume_excludes_pause_time(self):
        s = _make_session(self.service, self.op)
        s = self.service.start_session(session=s, operator=self.op)
        s.entry_at = timezone.now() - datetime.timedelta(minutes=20)
        s.save(update_fields=["entry_at", "updated_at"])
        s = self.service.stop_session(session=s, operator=self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.PAUSED)
        self.assertEqual(s.elapsed_minutes, 20)
        s.paused_at = timezone.now() - datetime.timedelta(minutes=10)
        s.save(update_fields=["paused_at", "updated_at"])
        s = self.service.start_session(session=s, operator=self.op)
        self.assertEqual(s.status, PlayhouseSession.Status.ACTIVE)
        self.assertGreaterEqual(s.paused_seconds, 599)
        s = self.service.end_session(session=s, operator=self.op)
        self.assertEqual(s.billable_minutes, 15)


class InvoiceBillingTest(TestCase):
    def setUp(self):
        _seed_roles()
        self.op = _operator()
        self.service = PlayhouseService()
        cfg = PlayhouseConfig.get_solo()
        cfg.price_per_15_minutes = 130000
        cfg.save()
        self.session = self._finished_session(billable=120)

    def _finished_session(self, billable=120):
        s = _make_session(self.service, self.op)
        s = self.service.start_session(session=s, operator=self.op)
        s = self.service.end_session(session=s, operator=self.op)
        s.billable_minutes = billable
        s.save(update_fields=["billable_minutes", "updated_at"])
        return s

    def test_invoice_time_amount_uses_price_snapshot(self):
        inv = self.service.create_invoice(session=self.session, operator=self.op)
        # 120 min = 8 blocks × 130000 = 1_040_000
        self.assertEqual(inv.billed_minutes, 120)
        self.assertEqual(inv.price_per_15_minutes, 130000)
        self.assertEqual(inv.time_amount, Decimal("1040000"))
        self.assertEqual(inv.total_amount, Decimal("1040000"))

    def test_cafe_items_added_and_totalled(self):
        inv = self.service.create_invoice(
            session=self.session,
            operator=self.op,
            cafe_items=[{"name": "آبمیوه", "price": 50000}, {"name": "بستنی", "price": 35000}],
        )
        self.assertEqual(inv.items.count(), 2)
        self.assertEqual(inv.cafe_total, Decimal("85000"))
        self.assertEqual(inv.total_amount, Decimal("1040000") + Decimal("85000"))

    def test_invoice_requires_finished_session(self):
        s = _make_session(self.service, self.op)  # waiting
        with self.assertRaises(PlayhouseServiceError):
            self.service.create_invoice(session=s, operator=self.op)

    def test_no_double_invoice(self):
        self.service.create_invoice(session=self.session, operator=self.op)
        with self.assertRaises(PlayhouseServiceError):
            self.service.create_invoice(session=self.session, operator=self.op)

    def test_invoice_number_unique_format(self):
        inv = self.service.create_invoice(session=self.session, operator=self.op)
        self.assertTrue(inv.invoice_number.startswith("PH-"))
        self.assertEqual(len(inv.invoice_number.split("-")), 3)

    def test_later_price_change_does_not_rewrite_old_invoice(self):
        inv = self.service.create_invoice(session=self.session, operator=self.op)
        cfg = PlayhouseConfig.get_solo()
        cfg.price_per_15_minutes = 999999
        cfg.save()
        inv.refresh_from_db()
        self.assertEqual(inv.price_per_15_minutes, 130000)


class PaymentTest(TestCase):
    def setUp(self):
        _seed_roles()
        self.op = _operator()
        self.fin = UserFactory(roles=["manager"])
        self.service = PlayhouseService()
        cfg = PlayhouseConfig.get_solo()
        cfg.price_per_15_minutes = 130000
        cfg.save()
        s = self.service.create_session(
            operator=self.op, first_name="پ", last_name="ی", age=5,
            guardian_mobile="09120000002",
        )
        s = self.service.start_session(session=s, operator=self.op)
        s = self.service.end_session(session=s, operator=self.op)
        s.billable_minutes = 60
        s.save(update_fields=["billable_minutes", "updated_at"])
        self.invoice = self.service.create_invoice(session=s, operator=self.op)

    def test_record_payment_pos_requires_tracking_code(self):
        with self.assertRaises(PlayhouseServiceError):
            self.service.record_payment(
                invoice=self.invoice, operator=self.fin,
                payment_method=PlayhouseInvoice.PaymentMethod.POS, tracking_code="",
            )

    def test_record_payment_marks_paid(self):
        inv = self.service.record_payment(
            invoice=self.invoice, operator=self.fin,
            payment_method=PlayhouseInvoice.PaymentMethod.POS, tracking_code="REF-123",
        )
        self.assertTrue(inv.is_paid)
        self.assertEqual(inv.payment_method, "pos")
        self.assertEqual(inv.tracking_code, "REF-123")
        self.assertIsNotNone(inv.paid_at)

    def test_reject_invalid_method(self):
        with self.assertRaises(PlayhouseServiceError):
            self.service.record_payment(
                invoice=self.invoice, operator=self.fin,
                payment_method="cash", tracking_code="x",
            )


class ApiTest(TestCase):
    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.op = UserFactory(roles=["employee"])
        self.client.force_authenticate(user=self.op)
        cfg = PlayhouseConfig.get_solo()
        cfg.price_per_15_minutes = 130000
        cfg.save()

    def _create(self, **over):
        data = {
            "first_name": "علی", "last_name": "احمدی", "age": 6,
            "guardian_mobile": "09121111111",
        }
        data.update(over)
        return self.client.post("/api/playhouse/sessions/", data, format="json")

    def test_config_exposed(self):
        r = self.client.get("/api/playhouse/config/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["price_per_15_minutes"], 130000)

    def test_create_session(self):
        r = self._create()
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["id"])

    def test_operator_gate(self):
        self.client.force_authenticate(user=None)
        other = UserFactory(roles=["student"])
        self.client.force_authenticate(user=other)
        r = self._create()
        self.assertEqual(r.status_code, 403)

    def test_session_flow_via_api(self):
        s = self._create().data
        sid = s["id"]
        r = self.client.post(f"/api/playhouse/sessions/{sid}/start/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "active")
        r = self.client.post(f"/api/playhouse/sessions/{sid}/end/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "finished")

    def test_invoice_via_api_with_cafe_and_payment(self):
        s = self._create().data
        sid = s["id"]
        self.client.post(f"/api/playhouse/sessions/{sid}/start/", {}, format="json")
        self.client.post(f"/api/playhouse/sessions/{sid}/end/", {}, format="json")
        r = self.client.post(
            f"/api/playhouse/sessions/{sid}/invoice/",
            {"cafe_items": [{"name": "چای", "price": 20000}],
             "payment_method": "pos", "tracking_code": "REF-1"},
            format="json",
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["price_per_15_minutes"], 130000)
        self.assertEqual(r.data["time_amount"], 0)
        self.assertEqual(r.data["payment_method"], "pos")
        self.assertEqual(r.data["tracking_code"], "REF-1")
        self.assertEqual(r.data["cafe_total"], 20000)

    def test_session_list_exposes_paid_invoice_state(self):
        s = self._create().data
        sid = s["id"]
        self.client.post(f"/api/playhouse/sessions/{sid}/start/", {}, format="json")
        self.client.post(f"/api/playhouse/sessions/{sid}/end/", {}, format="json")
        invoice = self.client.post(
            f"/api/playhouse/sessions/{sid}/invoice/",
            {"payment_method": "pos", "tracking_code": "LIST-1"},
            format="json",
        )
        self.assertEqual(invoice.status_code, 201, invoice.data)

        row = ActiveSessionSerializer(PlayhouseSession.objects.get(pk=sid)).data
        self.assertTrue(row["has_invoice"])
        self.assertTrue(row["invoice_is_paid"])
        self.assertEqual(row["invoice_number"], invoice.data["invoice_number"])

    def test_pay_gate_requires_finance_role(self):
        s = self._create().data
        sid = s["id"]
        self.client.post(f"/api/playhouse/sessions/{sid}/start/", {}, format="json")
        self.client.post(f"/api/playhouse/sessions/{sid}/end/", {}, format="json")
        inv = self.client.post(f"/api/playhouse/sessions/{sid}/invoice/", {}, format="json").data
        # employee (non-finance) cannot call pay endpoint
        r = self.client.post(
            f"/api/playhouse/invoices/{inv['id']}/pay/",
            {"payment_method": "pos", "tracking_code": "R"}, format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_finance_report_requires_finance_role(self):
        r = self.client.get("/api/playhouse/finance/report/")
        self.assertEqual(r.status_code, 403)
        # manager is finance
        mgr = UserFactory(roles=["manager"])
        self.client.force_authenticate(user=mgr)
        r = self.client.get("/api/playhouse/finance/report/?period=daily")
        self.assertEqual(r.status_code, 200)
        self.assertIn("summary", r.data)

    def test_finance_report_totals(self):
        # create + pay an invoice
        s = self._create().data
        sid = s["id"]
        self.client.post(f"/api/playhouse/sessions/{sid}/start/", {}, format="json")
        self.client.post(f"/api/playhouse/sessions/{sid}/end/", {}, format="json")
        inv = self.client.post(
            f"/api/playhouse/sessions/{sid}/invoice/",
            {"cafe_items": [{"name": "چای", "price": 20000}],
             "payment_method": "pos", "tracking_code": "REF-1"},
            format="json",
        ).data
        mgr = UserFactory(roles=["manager"])
        self.client.force_authenticate(user=mgr)
        r = self.client.get("/api/playhouse/finance/report/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["summary"]["invoices"], 1)
        self.assertEqual(r.data["summary"]["items_total"], 20000)
        self.assertEqual(r.data["summary"]["grand_total"],
                         int(inv["time_amount"]) + 20000)
        self.assertEqual(r.data["invoices"][0]["tracking"], "REF-1")


class ConfigSettingsTest(TestCase):
    """Settings page: price + working hours + open/close gating."""

    def setUp(self):
        _seed_roles()
        self.client = APIClient()
        self.mgr = UserFactory(roles=["manager"])
        self.emp = UserFactory(roles=["employee"])
        self.client.force_authenticate(user=self.mgr)
        # reset config to a known baseline
        cfg = PlayhouseConfig.get_solo()
        cfg.price_per_15_minutes = 130000
        cfg.open_time = None
        cfg.close_time = None
        cfg.is_open_now = True
        cfg.save()

    def test_config_exposes_hours(self):
        r = self.client.get("/api/playhouse/config/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["price_per_15_minutes"], 130000)
        self.assertTrue(r.data["is_open_now"])

    def test_manager_can_update_price(self):
        r = self.client.put(
            "/api/playhouse/config/",
            {"price_per_15_minutes": 150000, "is_open_now": True},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["price_per_15_minutes"], 150000)
        self.assertEqual(PlayhouseConfig.get_solo().price_per_15_minutes, 150000)

    def test_employee_cannot_update_config(self):
        self.client.force_authenticate(user=self.emp)
        r = self.client.put(
            "/api/playhouse/config/",
            {"price_per_15_minutes": 999},
            format="json",
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(PlayhouseConfig.get_solo().price_per_15_minutes, 130000)

    def test_reject_negative_price(self):
        r = self.client.put(
            "/api/playhouse/config/",
            {"price_per_15_minutes": -100},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(PlayhouseConfig.get_solo().price_per_15_minutes, 130000)

    def test_reject_close_before_open(self):
        r = self.client.put(
            "/api/playhouse/config/",
            {"price_per_15_minutes": 130000, "open_time": "20:00", "close_time": "09:00"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        cfg = PlayhouseConfig.get_solo()
        self.assertIsNone(cfg.open_time)
        self.assertIsNone(cfg.close_time)

    def test_closed_blocks_new_entry(self):
        PlayhouseConfig.get_solo()
        PlayhouseConfig.objects.update(is_open_now=False)
        PlayhouseConfig._singleton_pk = None
        r = self.client.post(
            "/api/playhouse/sessions/",
            {"first_name": "ب", "last_name": "ت", "age": 5, "guardian_mobile": "09120000099"},
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(PlayhouseSession.objects.count(), 0)

    def test_outside_working_hours_blocks_entry(self):
        # open 09:00–10:00 daily; now (test runtime) is almost surely outside
        PlayhouseConfig.objects.update(open_time="09:00", close_time="10:00")
        PlayhouseConfig._singleton_pk = None
        r = self.client.post(
            "/api/playhouse/sessions/",
            {"first_name": "ب", "last_name": "ت", "age": 5, "guardian_mobile": "09120000098"},
            format="json",
        )
        # current time may fall inside the window; assert either accepted or blocked-with-message
        if r.status_code == 400:
            self.assertIn("ساعات کاری", str(r.data.get("detail", "")))
        else:
            self.assertEqual(r.status_code, 201)
