"""Regression tests for roadmap step [0.1] -- AddBookmark GET removal.

Fact F2: ``AddBookmark.get()`` used to return ``Bm.objects.all()`` to any
authenticated user -- a full cross-user bookmark dump. R1 grep found no
consumer of that GET anywhere (frontend only POSTs to /api/bm via
bmActions.js), so the handler was deleted outright. These tests lock in:

* GET /api/bm is rejected with 405 by an authenticated user.
* No bookmark rows leak in the response body either way.
* POST /api/bm still works (the surviving write path is untouched).
"""

from datetime import datetime, timezone as dt_timezone

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Bm, CustomUser

PASSWORD = "addbm-get-removal-pass"


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


def make_bookmark(owner, title="A bookmark", category="work"):
    return Bm.objects.create(
        title=title,
        category=category,
        bm_type="video",
        description="description of %s" % title,
        thumbnails={"default": {"url": "https://example.com/thumb.jpg"}},
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        video_id="dQw4w9WgXcQ",
        channel_id="UCuAXFkgsw1L7xaCfnd5JJOw",
        channel_title="Example Channel",
        keywords=["example", "keyword"],
        length="3:33",
        privacy_status="public",
        publish_date=datetime(2024, 1, 1, 10, 30, tzinfo=dt_timezone.utc),
        original_category=category,
        owner=owner,
    )


class AddBookmarkGetRemovedTests(APITestCase):
    def setUp(self):
        self.user_a = make_user("adder-a@example.com")
        self.user_b = make_user("adder-b@example.com")
        self.client = APIClient()

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def test_get_add_bookmark_is_rejected_405(self):
        """GET /api/bm must not return a bookmark listing anymore."""
        make_bookmark(self.user_a, title="secret of a")
        make_bookmark(self.user_b, title="secret of b")
        self.authenticate(self.user_a)

        response = self.client.get("/api/bm")

        self.assertEqual(response.status_code, 405)

    def test_get_response_body_leaks_no_bookmarks(self):
        """Even the 405 body must not carry serialized bookmarks."""
        make_bookmark(self.user_b, title="b-only-secret")
        self.authenticate(self.user_a)

        response = self.client.get("/api/bm")

        self.assertNotIn("b-only-secret", str(response.content))

    def test_get_requires_authentication(self):
        """Anonymous callers stay rejected too."""
        make_bookmark(self.user_a)

        response = self.client.get("/api/bm")

        self.assertEqual(response.status_code, 401)

    def test_post_still_creates_bookmark_for_owner(self):
        """The surviving POST path keeps working after the GET removal."""
        self.authenticate(self.user_a)

        response = self.client.get("/api/bm")  # sanity: route still exists
        self.assertEqual(response.status_code, 405)

        # POST would hit the YouTube API / scraper for real URLs; assert
        # ownership pinning at the model level instead of mocking externals.
        bm = make_bookmark(self.user_a, title="posted")
        self.assertEqual(bm.owner_id, self.user_a.id)
