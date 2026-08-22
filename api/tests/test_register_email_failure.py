"""RegisterView must survive SMTP failure -- signup defect fix.

The activation email is sent synchronously after the user row is saved.
When the SMTP host is unreachable that send used to raise out of the view
and surface as a 500 AFTER the account existed (is_active=False), leaving
the client with an error and no way to know the account was created.
Contract pinned here:

* transport raising -> 201, user exists, body carries ``email_sent``=false;
* healthy transport -> 201, ``email_sent``=true;
* duplicate email stays a 400 and never attempts a send.
"""

from unittest import mock

from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase

from api.models import CustomUser

REGISTER_URL = "/api/register/"
PASSWORD = "register-suite-Pass-7x!"


class RegisterEmailDeliveryTests(APITestCase):
    def setUp(self):
        # RegisterView owns the anonymous 'register' throttle bucket
        # (keyed by IP); clear it so tests never 429.
        cache.clear()
        self.client = APIClient()

    def _payload(self, email):
        return {
            "email": email,
            "password": PASSWORD,
            "password2": PASSWORD,
        }

    def test_smtp_failure_still_returns_201_with_email_sent_false(self):
        with mock.patch(
            "api.views.send_mail", side_effect=Exception("SMTP unreachable")
        ):
            res = self.client.post(
                REGISTER_URL,
                self._payload("smtpdown@example.com"),
                format="json",
            )
        self.assertEqual(res.status_code, 201)
        self.assertFalse(res.data["email_sent"])
        # The account row must exist despite the failed delivery...
        self.assertTrue(
            CustomUser.objects.filter(email="smtpdown@example.com").exists()
        )
        # ...and stay unactivated exactly as before.
        user = CustomUser.objects.get(email="smtpdown@example.com")
        self.assertFalse(user.is_active)

    def test_healthy_transport_returns_201_with_email_sent_true(self):
        with mock.patch("api.views.send_mail") as fake_send:
            res = self.client.post(
                REGISTER_URL,
                self._payload("smtpok@example.com"),
                format="json",
            )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["email_sent"])
        fake_send.assert_called_once()

    def test_success_response_keeps_legacy_msg_field(self):
        # Backward compatibility: pre-existing clients read res.data.msg.
        with mock.patch("api.views.send_mail"):
            res = self.client.post(
                REGISTER_URL,
                self._payload("legacymsg@example.com"),
                format="json",
            )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["msg"], "Verification link sent to your email")

    def test_duplicate_email_is_still_400(self):
        CustomUser.objects.create_user(
            email="dupe@example.com", password=PASSWORD
        )
        res = self.client.post(
            REGISTER_URL, self._payload("dupe@example.com"), format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("email", res.data)
