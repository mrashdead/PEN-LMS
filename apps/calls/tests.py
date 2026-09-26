from django.test import TestCase
from django.utils import timezone

from apps.calls.models import CallFollowUpLog, FollowUpStatus
from apps.calls.services import log_call, update_follow_up
from apps.forms.tests.factories import UserFactory


class CallFollowUpTests(TestCase):
    def test_call_is_scoped_to_operator_and_follow_up_is_audited(self):
        operator = UserFactory(username="call-operator", roles=["employee"])
        other_operator = UserFactory(username="other-call-operator", roles=["employee"])
        call = log_call(
            actor=operator,
            caller_name="مراجع",
            caller_phone="09120000000",
            called_at=None,
            subject="پیگیری ثبت‌نام",
            follow_up_status=FollowUpStatus.PENDING,
        )

        self.assertTrue(call.__class__.objects.filter(
            pk=call.pk, receiver=operator,
        ).exists())
        from apps.calls.services import calls_visible_to

        self.assertTrue(calls_visible_to(operator).filter(pk=call.pk).exists())
        self.assertFalse(calls_visible_to(other_operator).filter(pk=call.pk).exists())

        updated = update_follow_up(
            call_id=call.pk,
            actor=operator,
            new_status=FollowUpStatus.DONE,
            note="انجام شد",
        )
        self.assertEqual(updated.follow_up_status, FollowUpStatus.DONE)
        self.assertTrue(CallFollowUpLog.objects.filter(
            call=call,
            actor=operator,
            previous_status=FollowUpStatus.PENDING,
            new_status=FollowUpStatus.DONE,
        ).exists())

    def test_call_workspace_renders_and_call_list_is_paginated(self):
        operator = UserFactory(username="call-pagination-operator", roles=["employee"])
        for index in range(25):
            log_call(
                actor=operator,
                caller_name=f"caller-{index}",
                caller_phone=f"0912000{index:04d}",
                called_at=timezone.now(),
                subject="سؤال",
            )
        self.client.force_login(operator)

        page = self.client.get("/api/calls/")
        workspace = self.client.get("/workspace/calls/")

        self.assertEqual(page.status_code, 200)
        self.assertEqual(len(page.json()["results"]), 20)
        self.assertIsNotNone(page.json()["next"])
        self.assertEqual(workspace.status_code, 200)
        self.assertContains(workspace, "ثبت تماس")

    def test_operator_report_only_aggregates_visible_calls(self):
        operator = UserFactory(username="call-report-operator", roles=["employee"])
        coworker = UserFactory(username="call-report-coworker", roles=["employee"])
        for user in (operator, coworker):
            log_call(
                actor=user,
                caller_name="تماس",
                caller_phone="09121111111",
                called_at=timezone.now(),
                subject="گزارش",
            )
        self.client.force_login(operator)

        response = self.client.get("/api/calls/reports/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["totals"]["calls"], 1)
