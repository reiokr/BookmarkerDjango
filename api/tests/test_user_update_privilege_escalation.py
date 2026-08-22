"""Regression tests for audit spec §8.4 -- UserDetail.put privilege escalation.

Fact: ``UserSerializer`` exposes ``is_staff`` / ``is_active`` / ``is_superuser``
as writable model booleans, and ``UserDetail.put`` bound ``request.data``
straight into it -- so ``PUT /api/users/<own-pk> {"is_superuser": true}``
promoted the caller to superuser.

Remediation: writes go through ``UserUpdateSerializer`` (first_name /
last_name ONLY). These tests pin:

* privileged fields in PUT/PATCH payloads are ignored -- DB state unchanged;
* legitimate name updates still work (PUT full payload, PATCH partial);
* the response body never echoes a privilege mutation;
* the nested ``options`` key no longer triggers DRF's nested-writable
  AssertionError (the old PUT 500).
"""

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser

PASSWORD = "priv-esc-suite-pass-1"


def make_user(email, **extra):
    defaults = {"is_active": True}
    defaults.update(extra)
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, **defaults
    )


class UserUpdatePrivilegeEscalationTests(APITestCase):
    def setUp(self):
        self.user = make_user("self-promo@example.com")
        # Baseline: a plain active user holds none of the privilege flags.
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.is_active)

        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def _escalation_payload(self):
        return {
            "first_name": "Updated",
            "last_name": "Name",
            "is_superuser": True,
            "is_staff": True,
            "is_active": False,
        }

    def _assert_privilege_flags_unchanged(self):
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.is_active)

    def test_put_cannot_escalate_privileges(self):
        response = self.client.put(
            "/api/users/%d" % self.user.pk,
            self._escalation_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self._assert_privilege_flags_unchanged()

    def test_patch_cannot_escalate_privileges(self):
        response = self.client.patch(
            "/api/users/%d" % self.user.pk,
            {
                "is_superuser": True,
                "is_staff": True,
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self._assert_privilege_flags_unchanged()

    def test_put_updates_legitimate_name_fields(self):
        response = self.client.put(
            "/api/users/%d" % self.user.pk,
            self._escalation_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")

    def test_patch_updates_first_name_alone(self):
        response = self.client.patch(
            "/api/users/%d" % self.user.pk,
            {"first_name": "Patched"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Patched")
        self.assertIsNone(self.user.last_name)

    def test_response_body_contains_no_privilege_fields(self):
        response = self.client.put(
            "/api/users/%d" % self.user.pk,
            self._escalation_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        for forbidden in ("is_superuser", "is_staff", "is_active"):
            self.assertNotIn(forbidden, response.data)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_put_with_nested_options_key_no_longer_500s(self):
        # The old UserSerializer-bound put() hit DRF's nested-writable
        # AssertionError on an "options" key -> 500. Unknown keys are now
        # simply ignored.
        response = self.client.put(
            "/api/users/%d" % self.user.pk,
            {
                "first_name": "Nested",
                "last_name": "Options",
                "options": {"theme": 9},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Nested")
