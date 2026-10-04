import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase


class DeploymentSettingsTests(SimpleTestCase):
    def load_settings(self, **overrides):
        environment = {
            **os.environ,
            "SECRET_KEY": "deployment-settings-test-secret",
            "DEBUG": "False",
            "DB_ENGINE": "django.db.backends.sqlite3",
            "TRUST_PROXY": "False",
            "CACHE_URL": "",
            "SESSION_COOKIE_SECURE": "True",
            "CSRF_COOKIE_SECURE": "True",
            **overrides,
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json, runpy; config = runpy.run_path('pen/settings.py'); "
                "print(json.dumps({name: config.get(name) for name in "
                "('SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', "
                "'SECURE_PROXY_SSL_HEADER', 'CACHES')}))",
            ],
            cwd=settings.BASE_DIR,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_secure_defaults_do_not_trust_an_external_proxy(self):
        config = self.load_settings()
        self.assertTrue(config["SESSION_COOKIE_SECURE"])
        self.assertTrue(config["CSRF_COOKIE_SECURE"])
        self.assertIsNone(config["SECURE_PROXY_SSL_HEADER"])
        self.assertIsNone(config["CACHES"])

    def test_local_http_can_explicitly_disable_secure_cookies(self):
        config = self.load_settings(SESSION_COOKIE_SECURE="False", CSRF_COOKIE_SECURE="False")
        self.assertFalse(config["SESSION_COOKIE_SECURE"])
        self.assertFalse(config["CSRF_COOKIE_SECURE"])

    def test_proxy_and_shared_cache_are_explicitly_enabled(self):
        config = self.load_settings(TRUST_PROXY="True", CACHE_URL="redis://redis:6379/2")
        self.assertEqual(config["SECURE_PROXY_SSL_HEADER"], ["HTTP_X_FORWARDED_PROTO", "https"])
        self.assertEqual(config["CACHES"]["default"]["LOCATION"], "redis://redis:6379/2")
        self.assertEqual(config["CACHES"]["default"]["BACKEND"], "django.core.cache.backends.redis.RedisCache")
