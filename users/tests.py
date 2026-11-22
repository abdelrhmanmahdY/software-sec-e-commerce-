import re

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class RegistrationConfirmationTests(TestCase):
    def test_web_signup_routes_require_email_confirmation(self):
        for path, username in (
            ("/signup/", "root_signup"),
            ("/dashboard/signup/", "dashboard_signup"),
        ):
            with self.subTest(path=path):
                response = self.client.post(
                    path,
                    {
                        "username": username,
                        "first_name": "Test",
                        "last_name": "User",
                        "email": f"{username}@example.test",
                        "password1": "Strong-Disposable-Password-927!",
                        "password2": "Strong-Disposable-Password-927!",
                    },
                )
                self.assertEqual(response.status_code, 302)

                user = User.objects.get(username=username)
                self.assertFalse(user.is_active)
                self.assertFalse(user.profile.email_confirmed)

                email = mail.outbox[-1]
                self.assertIn(user.email, email.to)
                confirmation = re.search(
                    r"https?://[^\s]+(/dashboard/confirm/[^\s]+)",
                    email.body,
                )
                self.assertIsNotNone(confirmation)
                self.client.get(confirmation.group(1))

                user.refresh_from_db()
                user.profile.refresh_from_db()
                self.assertTrue(user.is_active)
                self.assertTrue(user.profile.email_confirmed)
