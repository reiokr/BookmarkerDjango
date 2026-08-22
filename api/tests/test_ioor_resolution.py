"""Regression tests for audit spec §7 -- IsOwnerOrReadOnly resolution.

End-state pinned here:

* the class is attached to EXACTLY ONE view (BmDetailView) and is LIVE
  there -- check_object_permissions executes on every request;
* unsafe methods by non-owners are denied BY THE PERMISSION CLASS (403);
* reads stay owner-scoped even when the class would allow them (the
  get_object read-gate), matching the Lane B contract in test_ownership.py;
* missing pks are 404 via canonical get_object_or_404.
"""

import inspect
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

import api.views as views_module
from api.models import Bm, CustomUser
from api.permissions import IsOwnerOrReadOnly
from api.views import BmDetailView

PASSWORD = "ioor-resolution-pass-1"


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
        keywords=["example"],
        length="3:33",
        privacy_status="public",
        publish_date=datetime(2024, 1, 1, tzinfo=dt_timezone.utc),
        original_category=category,
        owner=owner,
    )


class AttachmentAuditTests(APITestCase):
    def test_ioor_is_attached_to_exactly_one_view(self):
        # Spec §7: 14 attachments stripped, 1 wired. Any future re-attach
        # without a check_object_permissions call must fail this audit.
        attached = []
        for name, obj in vars(views_module).items():
            if inspect.isclass(obj) and hasattr(obj, "permission_classes"):
                if IsOwnerOrReadOnly in obj.permission_classes:
                    attached.append(name)
        self.assertEqual(attached, ["BmDetailView"])


class IoorEnforcementTests(APITestCase):
    def setUp(self):
        cache_clear = None  # no throttles involved on these routes
        self.user_a = make_user("ioor-a@example.com")
        self.user_b = make_user("ioor-b@example.com")
        self.mine = make_bookmark(self.user_a, title="a keeps this")
        self.theirs = make_bookmark(self.user_b, title="b keeps this")
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user_a).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def test_check_object_permissions_executes_on_request(self):
        with patch.object(
            BmDetailView, "check_object_permissions", autospec=True
        ) as spy:
            response = self.client.get("/api/bm/%d" % self.mine.pk)

        self.assertEqual(response.status_code, 200)
        spy.assert_called_once()

    def test_denial_comes_from_the_permission_class_for_writes(self):
        # Force the class to deny: even the OWNER must get 403, proving the
        # class result actually gates the response (not decorative).
        with patch.object(
            IsOwnerOrReadOnly, "has_object_permission", return_value=False
        ):
            response = self.client.put(
                "/api/bm/%d" % self.mine.pk,
                {"video_data": {"list_id": None, "list_index": None}},
                format="json",
            )

        self.assertEqual(response.status_code, 403)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.title, "a keeps this")

    def test_reads_stay_owner_scoped_even_if_class_allows(self):
        # Force the class to allow everything: cross-user GET must STILL be
        # denied by the get_object read-gate (foreign bookmarks invisible).
        with patch.object(
            IsOwnerOrReadOnly, "has_object_permission", return_value=True
        ):
            response = self.client.get("/api/bm/%d" % self.theirs.pk)

        self.assertEqual(response.status_code, 403)

    def test_cross_user_write_is_403_and_inert(self):
        response = self.client.put(
            "/api/bm/%d" % self.theirs.pk,
            {"video_data": {"list_id": None, "list_index": None}},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.title, "b keeps this")

    def test_owner_can_still_read_update_delete_own(self):
        self.assertEqual(
            self.client.get("/api/bm/%d" % self.mine.pk).status_code, 200
        )
        from api.serializers import BmSerializer

        payload = dict(BmSerializer(self.mine).data)
        payload["title"] = "renamed by owner"
        updated = self.client.put(
            "/api/bm/%d" % self.mine.pk,
            {"video_data": payload},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        deleted = self.client.delete("/api/bm/%d" % self.mine.pk)
        self.assertEqual(deleted.status_code, 204)

    def test_missing_pk_is_404_via_canonical_lookup(self):
        response = self.client.get("/api/bm/987654321")
        self.assertEqual(response.status_code, 404)
