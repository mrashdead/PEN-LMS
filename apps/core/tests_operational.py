from __future__ import annotations

import uuid
from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase


class OperationalEndpointsTests(TestCase):
    def test_health_is_live_without_database_dependency(self):
        with patch("apps.core.views.connection.cursor", side_effect=OperationalError):
            response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_readiness_checks_database(self):
        response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "database": "ok"})

    def test_readiness_returns_503_when_database_is_down(self):
        with patch("apps.core.views.connection.cursor", side_effect=OperationalError):
            response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "not_ready")

    def test_request_id_is_returned_and_validated(self):
        request_id = str(uuid.uuid4())
        response = self.client.get("/healthz/", HTTP_X_REQUEST_ID=request_id)
        self.assertEqual(response["X-Request-ID"], request_id)

        response = self.client.get("/healthz/", HTTP_X_REQUEST_ID="not-a-uuid")
        self.assertNotEqual(response["X-Request-ID"], "not-a-uuid")
        uuid.UUID(response["X-Request-ID"])

    def test_openapi_contract_is_published(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("openapi:", response.content.decode())
        self.assertIn("/api/auth/token/", response.content.decode())
