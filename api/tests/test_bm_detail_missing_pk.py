"""Regression tests for roadmap step [0.5] -- BmDetailView missing-pk 404.

Fact F14 bonus defect: ``BmDetailView.get_object`` used
``Bm.objects.filter(pk=pk).first()`` and immediately dereferenced the result;
a nonexistent pk therefore crashed with a 500 (AttributeError on None)
instead of a clean 404.

These tests pin: missing pk -> 404 for GET / PUT / DELETE, while an existing
own bookmark still serves 200. Cross-user ownership of EXISTING bookmarks is
Lane B's suite (api/tests/test_ownership.py) -- deliberately not duplicated
here beyond what the 404 path needs.
"""

from datetime import datetime, timezone as dt_timezone

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Bm, CustomUser

PASSWORD = "bm-detail-404-pass"
MISSING_PK = 987654321


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


class BmDetailMissingPkTests(APITestCase):
    def setUp(self):
        self.user = make_user("detail-404@example.com")
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def test_get_missing_pk_is_404_not_500(self):
        response = self.client.get("/api/bm/%d" % MISSING_PK)
        self.assertEqual(response.status_code, 404)

    def test_put_missing_pk_is_404_not_500(self):
        # video_data must carry list_id/list_index so the request survives
        # put()'s field normalization and actually reaches get_object.
        response = self.client.put(
            "/api/bm/%d" % MISSING_PK,
            {"video_data": {"list_id": None, "list_index": None}},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_missing_pk_is_404_not_500(self):
        response = self.client.delete("/api/bm/%d" % MISSING_PK)
        self.assertEqual(response.status_code, 404)

    def test_existing_own_bookmark_still_serves_200(self):
        bm = make_bookmark(self.user, title="still here")
        response = self.client.get("/api/bm/%d" % bm.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "still here")
