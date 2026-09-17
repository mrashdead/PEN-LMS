from __future__ import annotations

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase

from apps.core.login_security import blocked, record_failure


class LoginSecurityTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.request = RequestFactory().post("/dashboard/login/")
        self.request.META["REMOTE_ADDR"] = "192.0.2.10"

    def tearDown(self):
        cache.clear()

    def test_fifth_failure_activates_one_minute_rate_limit(self):
        for _ in range(5):
            record_failure(self.request, "teacher-1")

        self.assertIn("یک دقیقه", blocked(self.request, "teacher-1"))

    def test_ten_failures_activate_temporary_lock(self):
        for _ in range(10):
            record_failure(self.request, "teacher-2")

        self.assertIn("۱۵ دقیقه", blocked(self.request, "teacher-2"))
