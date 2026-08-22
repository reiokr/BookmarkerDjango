"""Contract tests for roadmap step [0.4] -- extensionLogin rewrite.

Fact F4: ``extensionLogin`` was an AllowAny FBV reachable via GET with
credentials in the query string; it interpolated email+password into inline
JavaScript with quote-strip-only sanitization (backslash and ``</script>``
breakouts) and called ``postMessage(result, '*')``, leaking the JWT to any
framing parent.

New contract (documented in the view docstring):

* POST only -- GET (and everything else) gets DRF's standard 405.
* JSON request/response only -- no HTML, no inline JS, no template.
* Submitted credentials are never echoed into ANY response body.
* No postMessage at all: the client performs its own fetch and owns its
  messaging (the ``'*'`` targetOrigin leak is gone entirely).

Risk R7 note: repo-wide grep found no in-repo consumer of the legacy flow;
these tests pin the new contract so an external extension consumer can be
migrated against it.
"""

from rest_framework.test import APIClient, APITestCase

from api.models import CustomUser

EMAIL = "ext.agent@example.com"
PASSWORD = 'Ext-Pass!"\'\\</script>breakout'
# Distinctive markers whose absence from every response body proves zero
# credential reflection (the legacy vector interpolated these verbatim).
FIRST_NAME = "Extension"


def make_user(email, password=PASSWORD, is_active=True, **extra_fields):
    return CustomUser.objects.create_user(
        email=email, password=password, is_active=is_active, **extra_fields
    )


class ExtensionLoginContractTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/extension-login/"

    def login(self, email=EMAIL, password=PASSWORD, **extra):
        return self.client.post(
            self.url,
            {"email": email, "password": password},
            format="json",
            **extra,
        )

    # --- (b) method enforcement -------------------------------------------

    def test_get_is_rejected_405(self):
        make_user(EMAIL)

        response = self.client.get(
            self.url + "?email=%s&password=%s" % (EMAIL, PASSWORD)
        )

        self.assertEqual(response.status_code, 405)

    def test_put_and_delete_are_rejected_too(self):
        for method in ("put", "delete"):
            response = getattr(self.client, method)(self.url, format="json")
            self.assertEqual(response.status_code, 405, method)

    # --- (c) JSON-only surface, no script/postMessage anywhere ------------

    def test_responses_are_json_only_no_script_no_postmessage(self):
        make_user(EMAIL)

        bodies = [
            self.login(),  # success
            self.login(password="wrong-password"),  # auth failure
            self.client.post(self.url, {}, format="json"),  # missing fields
            self.client.get(self.url),  # 405 body
        ]

        for response in bodies:
            self.assertTrue(
                str(response["Content-Type"]).startswith("application/json"),
                response["Content-Type"],
            )
            text = response.content.decode()
            self.assertNotIn("<script", text.lower())
            self.assertNotIn("postMessage", text)
            self.assertNotIn("window.parent", text)

    # --- (a) zero credential substrings in ANY response body --------------

    def test_success_response_never_echoes_credentials(self):
        make_user(EMAIL, first_name=FIRST_NAME)

        response = self.login()

        self.assertEqual(response.status_code, 200)
        text = response.content.decode()
        self.assertNotIn(EMAIL, text)
        self.assertNotIn(PASSWORD, text)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["first_name"], FIRST_NAME)

    def test_wrong_password_never_echoes_credentials(self):
        make_user(EMAIL)

        response = self.login(password="totally-wrong")

        self.assertEqual(response.status_code, 401)
        text = response.content.decode()
        self.assertNotIn(EMAIL, text)
        self.assertNotIn(PASSWORD, text)

    def test_unknown_email_never_echoes_credentials(self):
        response = self.login(email="ghost.user@example.com")

        self.assertEqual(response.status_code, 401)
        text = response.content.decode()
        self.assertNotIn("ghost.user@example.com", text)
        self.assertNotIn(PASSWORD, text)

    def test_unverified_account_never_echoes_credentials(self):
        make_user(EMAIL, is_active=False)

        response = self.login()

        self.assertEqual(response.status_code, 401)
        text = response.content.decode()
        self.assertNotIn(EMAIL, text)
        self.assertNotIn(PASSWORD, text)

    def test_missing_fields_rejected_without_echo(self):
        for payload in ({}, {"email": EMAIL}, {"password": PASSWORD}):
            response = self.client.post(self.url, payload, format="json")
            self.assertEqual(response.status_code, 400, payload)
            text = response.content.decode()
            self.assertNotIn(EMAIL, text)
            self.assertNotIn(PASSWORD, text)

    def test_query_string_credentials_are_ignored(self):
        """The legacy channel (creds in the URL) must not authenticate."""
        make_user(EMAIL)

        response = self.client.post(
            self.url + "?email=%s&password=%s" % (EMAIL, PASSWORD),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(EMAIL, response.content.decode())

    # --- functional parity -------------------------------------------------

    def test_success_returns_categories_for_the_caller(self):
        user = make_user(EMAIL)
        user.categories = ["work", "videos"]
        user.save(update_fields=["categories"])

        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["categories"], ["work", "videos"])
