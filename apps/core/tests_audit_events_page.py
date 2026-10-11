from __future__ import annotations

from django.test import TestCase

from apps.core.models import AuditEvent
from apps.forms.tests.factories import UserFactory


class AuditEventsPageTests(TestCase):
    def setUp(self):
        self.manager = UserFactory(username="audit-page-manager", roles=["manager"])
        self.teacher = UserFactory(username="audit-page-teacher", roles=["teacher"])
        self.event = AuditEvent.objects.create(
            kind=AuditEvent.Kind.ACCESS_DENIED,
            actor=self.teacher,
            summary="درخواست دسترسی رد شد",
            metadata={"method": "GET", "path": "/api/private/", "status": 403},
            ip_address="192.0.2.10",
        )

    def test_admin_can_view_and_filter_recorded_events(self):
        self.client.force_login(self.manager)

        response = self.client.get("/workspace/security/events/?kind=access_denied")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "درخواست دسترسی رد شد")
        self.assertContains(response, "/api/private/")
        self.assertContains(response, "192.0.2.10")
        self.assertContains(response, "رخدادهای امنیتی")
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_non_admin_cannot_view_security_events(self):
        self.client.force_login(self.teacher)

        response = self.client.get("/workspace/security/events/")

        self.assertEqual(response.status_code, 404)

    def test_unknown_kind_filter_falls_back_to_all_events(self):
        self.client.force_login(self.manager)

        response = self.client.get("/workspace/security/events/?kind=unknown")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "درخواست دسترسی رد شد")
