"""Regression tests for audit spec §4.3 -- scoped throttles.

Proves the exact rates land as configured:

* ``youtube_proxy`` 30/min and ``youtube_search`` 6/min via
  ScopedRateThrottle on authenticated proxy views;
* ``login`` 10/min and ``register`` 5/min via AnonRateThrottle on the
  AllowAny surfaces.

Invalid-ID requests are used for the proxy bursts: DRF throttling runs
BEFORE the view handler, so every request consumes budget even when the
handler answers 400 -- no upstream mocking needed and zero network calls.
"""

from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser

PASSWORD = "throttle-suite-pass-1"


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


class ThrottleTestBase(APITestCase):
    def setUp(self):
        # Throttle history lives in the shared LocMemCache; clear it so
        # every test starts from an empty bucket.
        cache.clear()
        self.client = APIClient()


class YoutubeProxyThrottleTests(ThrottleTestBase):
    """ScopedRateThrottle scope 'youtube_proxy' -- 30/min per user."""

    def setUp(self):
        super().setUp()
        self.user = make_user("proxy-throttle@example.com")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def _hit(self):
        # Invalid comment id -> handler 400s, throttle still counts it.
        return self.client.get("/api/bm/comment/replies/tooshort")

    def test_31st_request_within_minute_is_429(self):
        statuses = [self._hit().status_code for _ in range(30)]

        self.assertTrue(all(code == 400 for code in statuses))
        self.assertEqual(self._hit().status_code, 429)

    def test_other_users_have_their_own_bucket(self):
        for _ in range(30):
            self._hit()
        self.assertEqual(self._hit().status_code, 429)

        other = make_user("proxy-throttle-b@example.com")
        token = str(RefreshToken.for_user(other).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)
        # A different authenticated identity gets a fresh bucket.
        self.assertEqual(self._hit().status_code, 400)


class YoutubeSearchThrottleTests(ThrottleTestBase):
    """ScopedRateThrottle scope 'youtube_search' -- 6/min (100 units/call)."""

    def setUp(self):
        super().setUp()
        self.user = make_user("search-throttle@example.com")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def _hit(self):
        return self.client.get("/api/video/short/related-videos")

    def test_7th_request_within_minute_is_429(self):
        statuses = [self._hit().status_code for _ in range(6)]

        self.assertTrue(all(code == 400 for code in statuses))
        self.assertEqual(self._hit().status_code, 429)


class LoginAnonThrottleTests(ThrottleTestBase):
    """AnonRateThrottle scope 'login' -- 10/min per IP."""

    def _hit(self):
        return self.client.post(
            "/api/login/",
            {"email": "nobody-throttle@example.com", "password": "wrong"},
            format="json",
        )

    def test_11th_request_within_minute_is_429(self):
        statuses = [self._hit().status_code for _ in range(10)]

        self.assertFalse(any(code == 429 for code in statuses))
        self.assertEqual(self._hit().status_code, 429)

    def test_authenticated_requests_bypass_anon_throttle(self):
        user = make_user("login-throttle-authed@example.com")
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

        # AnonRateThrottle ignores authenticated callers entirely.
        for _ in range(12):
            response = self.client.get("/api/user/me")
            self.assertEqual(response.status_code, 200)


class RegisterAnonThrottleTests(ThrottleTestBase):
    """AnonRateThrottle scope 'register' -- 5/min per IP."""

    def _hit(self, n):
        return self.client.post(
            "/api/register/",
            {"email": "reg-throttle-%d@example.com" % n,
             "password": "Sup3r-Secret-Password!",
             "password2": "Sup3r-Secret-Password!"},
            format="json",
        )

    def test_6th_request_within_minute_is_429(self):
        statuses = [self._hit(n).status_code for n in range(5)]

        self.assertFalse(any(code == 429 for code in statuses))
        self.assertEqual(self._hit(99).status_code, 429)
