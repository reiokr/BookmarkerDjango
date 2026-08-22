"""Tests for the HttpOnly refresh-cookie migration -- roadmap step [2.2].

Option (a): the refresh JWT lives ONLY in an HttpOnly SameSite=Lax cookie
scoped to /api/login/; the JSON bodies never carry it again.

Contract pinned here:

* login sets the cookie with EXACT flags -- HttpOnly, SameSite=Lax,
  Path=/api/login/, Secure when DEBUG=False, NOT Secure when DEBUG=True;
* the login response body contains NO refresh token (substring-level);
* /api/login/refresh/ reads the cookie, rotates it, and REPLACES the
  cookie (rotation + blacklist stay on);
* replaying the pre-rotation cookie fails (blacklisted);
* explicit body tokens are rejected;
* a missing cookie is a 401;
* logout blacklists the token and clears the cookie;
* cross-site Origin headers are rejected on cookie-consuming POSTs.
"""

from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser

PASSWORD = "cookie-suite-pass-1"
LOGIN_URL = "/api/login/"
REFRESH_URL = "/api/login/refresh/"
LOGOUT_URL = "/api/login/logout/"


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


class RefreshCookieTestBase(APITestCase):
    def setUp(self):
        # The login/refresh/logout surfaces share the anonymous 'login'
        # throttle bucket (keyed by IP); clear it so tests never 429.
        cache.clear()
        self.client = APIClient()
        self.user = make_user("cookie-user@example.com")

    def _login(self):
        return self.client.post(
            LOGIN_URL,
            {"email": "cookie-user@example.com", "password": PASSWORD},
            format="json",
        )


class LoginSetsCookieTests(RefreshCookieTestBase):
    def test_login_sets_cookie_with_exact_flags(self):
        res = self._login()
        self.assertEqual(res.status_code, 200)

        morsel = res.cookies["refresh_token"]
        self.assertEqual(morsel["httponly"], True)
        self.assertEqual(morsel["samesite"], "Lax")
        self.assertEqual(morsel["path"], "/api/login/")
        # Test runs have DEBUG=False -> Secure must be present.
        self.assertEqual(morsel["secure"], True)
        # Max-Age mirrors REFRESH_TOKEN_LIFETIME = 14 days.
        self.assertEqual(int(morsel["max-age"]), 14 * 24 * 3600)

    def test_login_sets_secure_false_under_debug(self):
        with override_settings(DEBUG=True):
            res = self._login()
        self.assertEqual(res.status_code, 200)
        # Morsel stores an absent flag as '' -- assert it is NOT set.
        self.assertFalse(res.cookies["refresh_token"]["secure"])

    def test_login_body_contains_no_refresh_substring(self):
        res = self._login()
        self.assertNotIn(b"refresh", res.content)
        self.assertIn("access", res.data)

    def test_failed_login_sets_no_cookie(self):
        res = self.client.post(
            LOGIN_URL,
            {"email": "ghost@example.com", "password": PASSWORD},
            format="json",
        )
        # not_registered body passes through without a cookie.
        self.assertNotIn("refresh_token", res.cookies)


class CookieRefreshRoundTripTests(RefreshCookieTestBase):
    def test_refresh_via_cookie_returns_access_and_rotates_cookie(self):
        login_res = self._login()
        old_refresh = login_res.cookies["refresh_token"].value

        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        # Rotation: a NEW refresh token lands in the cookie...
        new_morsel = res.cookies["refresh_token"]
        self.assertTrue(new_morsel.value)
        self.assertNotEqual(new_morsel.value, old_refresh)
        # ...with the same exact flags.
        self.assertEqual(new_morsel["httponly"], True)
        self.assertEqual(new_morsel["samesite"], "Lax")
        self.assertEqual(new_morsel["path"], "/api/login/")
        # And the body carries no refresh token either.
        self.assertNotIn(b"refresh", res.content)

    def test_pre_rotation_cookie_is_blacklisted(self):
        login_res = self._login()
        old_refresh = login_res.cookies["refresh_token"].value

        first = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(first.status_code, 200)

        # Replay the stale cookie: blacklisted after rotation.
        self.client.cookies["refresh_token"] = old_refresh
        replay = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(replay.status_code, 401)

    def test_missing_cookie_is_401(self):
        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, 401)

    def test_explicit_body_token_is_rejected(self):
        raw = str(RefreshToken.for_user(self.user))
        res = self.client.post(
            REFRESH_URL, {"refresh": raw}, format="json"
        )
        self.assertEqual(res.status_code, 400)

    def test_garbage_cookie_is_401(self):
        self.client.cookies["refresh_token"] = "not-a-jwt"
        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, 401)


class LogoutTests(RefreshCookieTestBase):
    def test_logout_clears_cookie_and_blacklists_token(self):
        login_res = self._login()
        cookie_token = login_res.cookies["refresh_token"].value

        logout_res = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(logout_res.status_code, 200)

        morsel = logout_res.cookies["refresh_token"]
        # delete_cookie expires immediately at the scoped path.
        self.assertEqual(morsel["max-age"], 0)
        self.assertEqual(morsel["path"], "/api/login/")
        self.assertEqual(morsel["expires"], "Thu, 01 Jan 1970 00:00:00 GMT")

        # The logged-out token can no longer mint access tokens: its jti
        # was blacklisted server-side.
        self.client.cookies["refresh_token"] = cookie_token
        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, 401)

    def test_logout_without_cookie_still_succeeds(self):
        res = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b"refresh", res.content)


class CrossOriginRejectionTests(RefreshCookieTestBase):
    """Defense-in-depth CSRF posture: SameSite=Lax plus Origin allowlist."""

    def _post_with_origin(self, url, origin):
        return self.client.post(
            url, format="json", HTTP_ORIGIN=origin
        )

    def test_unknown_origin_is_rejected_on_refresh(self):
        self._login()
        res = self._post_with_origin(REFRESH_URL, "https://evil.example")
        self.assertEqual(res.status_code, 403)

    def test_unknown_origin_is_rejected_on_logout(self):
        res = self._post_with_origin(LOGOUT_URL, "https://evil.example")
        self.assertEqual(res.status_code, 403)

    def test_frontend_origin_is_accepted_on_refresh(self):
        from django.conf import settings

        self._login()
        res = self._post_with_origin(REFRESH_URL, settings.FRONTEND_URL)
        self.assertEqual(res.status_code, 200)

    def test_backend_origin_is_accepted_on_logout(self):
        from django.conf import settings

        res = self._post_with_origin(LOGOUT_URL, settings.BACKEND_URL)
        self.assertEqual(res.status_code, 200)

    def test_no_origin_header_is_accepted(self):
        # Non-browser clients send no Origin; they cannot be CSRFed.
        self._login()
        res = self.client.post(REFRESH_URL, format="json")
        self.assertEqual(res.status_code, 200)

    # --- /api/login/ carries the same gate (port-drift fix) ---

    def test_unknown_origin_is_rejected_on_login(self):
        res = self._post_with_origin(LOGIN_URL, "https://evil.example")
        self.assertEqual(res.status_code, 403)

    def test_frontend_origin_is_accepted_on_login(self):
        from django.conf import settings

        # Login needs credentials -- unlike refresh/logout, an empty body
        # would 400 on serializer validation before anything else.
        res = self.client.post(
            LOGIN_URL,
            {"email": "cookie-user@example.com", "password": PASSWORD},
            format="json",
            HTTP_ORIGIN=settings.FRONTEND_URL,
        )
        self.assertEqual(res.status_code, 200)

    def test_backend_origin_is_accepted_on_login(self):
        from django.conf import settings

        res = self.client.post(
            LOGIN_URL,
            {"email": "cookie-user@example.com", "password": PASSWORD},
            format="json",
            HTTP_ORIGIN=settings.BACKEND_URL,
        )
        self.assertEqual(res.status_code, 200)

    def test_no_origin_header_is_accepted_on_login(self):
        # curl/tests/server-to-server: no Origin header, allowed.
        res = self.client.post(
            LOGIN_URL,
            {"email": "cookie-user@example.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(res.status_code, 200)

    # --- CRA dev-proxy loopback aliasing (proxy rewrites Origin) ---

    def test_proxy_rewritten_origin_is_accepted_on_login(self):
        # react-dev-utils' onProxyReq rewrites every proxied request's
        # Origin to the proxy target -- historically the exact form
        # "http://127.0.0.1:8000/" -- which must pass the gate.
        res = self.client.post(
            LOGIN_URL,
            {"email": "cookie-user@example.com", "password": PASSWORD},
            format="json",
            HTTP_ORIGIN="http://127.0.0.1:8000/",
        )
        self.assertEqual(res.status_code, 200)

    def test_proxy_rewritten_origin_passes_gate_on_refresh(self):
        # Gate passes -> request proceeds to cookie validation; with no
        # cookie that is a 401, NOT the gate's 403.
        res = self._post_with_origin(REFRESH_URL, "http://127.0.0.1:8000/")
        self.assertEqual(res.status_code, 401)

    def test_foreign_origin_with_trailing_slash_still_rejected(self):
        res = self._post_with_origin(LOGIN_URL, "https://evil.example/")
        self.assertEqual(res.status_code, 403)

    def test_trailing_slash_frontend_origin_accepted_on_refresh(self):
        from django.conf import settings

        self._login()
        res = self._post_with_origin(REFRESH_URL, settings.FRONTEND_URL + "/")
        self.assertEqual(res.status_code, 200)


class OriginAllowlistReadsSettingsTests(APITestCase):
    """Unit-level pin of the allowlist source: settings, read per request.

    Incident: .env shipped FRONTEND_URL=:3001 / BACKEND_URL=:8001 while
    the real dev topology is CRA on :3000 proxying to Django on :8000 --
    every in-browser refresh 403'd. These tests prove the allowlist is
    derived from FRONTEND_URL/BACKEND_URL at request time, so correcting
    the two .env values is the single knob that fixes it.
    """

    DEV_FRONTEND = "http://localhost:3000"
    DEV_BACKEND = "http://localhost:8000"
    DRIFTED_FRONTEND = "http://localhost:3001"

    def _request_with_origin(self, origin):
        from django.test import RequestFactory

        from api.auth_cookies import origin_allowed

        return origin_allowed(
            RequestFactory().post(REFRESH_URL, HTTP_ORIGIN=origin)
        )

    def test_corrected_dev_ports_are_allowed_on_refresh_semantics(self):
        with override_settings(
            FRONTEND_URL=self.DEV_FRONTEND, BACKEND_URL=self.DEV_BACKEND
        ):
            self.assertTrue(self._request_with_origin(self.DEV_FRONTEND))
            self.assertTrue(self._request_with_origin(self.DEV_BACKEND))

    def test_drifted_port_is_rejected(self):
        with override_settings(
            FRONTEND_URL=self.DRIFTED_FRONTEND, BACKEND_URL=self.DEV_BACKEND
        ):
            # The browser really runs on :3000; the allowlist says :3001
            # -> exactly the incident's 403 behaviour.
            self.assertFalse(self._request_with_origin(self.DEV_FRONTEND))

    def test_trailing_slash_is_normalised(self):
        with override_settings(
            FRONTEND_URL=self.DEV_FRONTEND + "/", BACKEND_URL=self.DEV_BACKEND
        ):
            self.assertTrue(self._request_with_origin(self.DEV_FRONTEND))

    # --- loopback aliasing: localhost <-> 127.0.0.1 (dev proxy) ---

    def test_loopback_alias_of_configured_urls_is_allowed(self):
        with override_settings(
            FRONTEND_URL=self.DEV_FRONTEND, BACKEND_URL=self.DEV_BACKEND
        ):
            self.assertTrue(self._request_with_origin("http://127.0.0.1:8000/"))
            self.assertTrue(self._request_with_origin("http://127.0.0.1:3000"))
            self.assertTrue(self._request_with_origin("http://localhost:3000/"))

    def test_wrong_port_loopback_alias_is_rejected(self):
        with override_settings(
            FRONTEND_URL=self.DEV_FRONTEND, BACKEND_URL=self.DEV_BACKEND
        ):
            self.assertFalse(
                self._request_with_origin("http://127.0.0.1:9999")
            )

    def test_non_loopback_config_gains_no_aliases(self):
        prod = "https://bookmarks.example.com"
        with override_settings(FRONTEND_URL=prod, BACKEND_URL=prod):
            self.assertTrue(self._request_with_origin(prod))
            self.assertFalse(self._request_with_origin("https://127.0.0.1"))
            self.assertFalse(
                self._request_with_origin("https://localhost")
            )
