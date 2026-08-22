"""Regression tests for audit spec §6 -- phantom last_login mutation.

``UserDetail.get`` used to run ``user.last_login = timezone.now()`` on the
in-memory instance WITHOUT ever calling ``.save()`` -- the database was never
written; only the serialized response lied about a fresh login on every GET.

Disposition per spec: delete the assignment outright. These tests pin:

* two consecutive GETs return an IDENTICAL last_login;
* the served value equals the persisted DB value (no in-memory drift).
"""

from django.utils import timezone
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser

PASSWORD = "last-login-suite-pass-1"


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


class UserDetailLastLoginTests(APITestCase):
    def setUp(self):
        self.user = make_user("last-login@example.com")
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def test_two_consecutive_gets_return_identical_last_login(self):
        first = self.client.get("/api/users/%d" % self.user.pk)
        second = self.client.get("/api/users/%d" % self.user.pk)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.data["last_login"], second.data["last_login"]
        )

    def test_get_does_not_advance_last_login(self):
        # SIMPLE_JWT UPDATE_LAST_LOGIN is False, so last_login stays at its
        # creation default (None) -- and a profile GET must not change it.
        before = CustomUser.objects.get(pk=self.user.pk).last_login

        response = self.client.get("/api/users/%d" % self.user.pk)

        self.assertEqual(response.status_code, 200)
        after = CustomUser.objects.get(pk=self.user.pk).last_login
        self.assertEqual(before, after)
        self.assertIsNone(after)
        self.assertNotEqual(
            response.data["last_login"],
            timezone.now().isoformat(),
            msg="response must not fabricate a fresh last_login",
        )
