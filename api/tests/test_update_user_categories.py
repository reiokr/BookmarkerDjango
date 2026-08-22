"""Regression tests for roadmap step [0.2] -- UpdateUserCategories oracle fix.

Fact F3: ``UpdateUserCategories.put()`` write path was safe (it pins the
caller via ``get_object(self.request.user.id)``), but the duplicate-category
guard queried ``Bm.objects.filter(category__iexact=...)`` across ALL users'
bookmarks -- a global category-existence oracle -- and its nested
``if serializer.is_valid(): return serializer.errors`` logic was inverted
(it only rejected valid payloads and answered 403 with an empty body).

The guard is now scoped to ``owner=request.user`` and runs as a
deterministic pre-check. These tests prove:

* a category that exists ONLY in another user's bookmarks can never cause a
  403 for the caller (the cross-user oracle is dead);
* the caller's OWN bookmark-backed categories are still blocked (403), now
  with a meaningful body;
* case-insensitive matching applies to the caller's own data only;
* writing to another user's pk stays PermissionDenied.
"""

from datetime import datetime, timezone as dt_timezone

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Bm, CustomUser

PASSWORD = "categories-oracle-pass"


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


class UpdateUserCategoriesOracleTests(APITestCase):
    def setUp(self):
        self.user_a = make_user("cats-a@example.com")
        self.user_b = make_user("cats-b@example.com")
        self.client = APIClient()

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def put_categories(self, pk, categories, category):
        return self.client.put(
            "/api/user/categories/%d" % pk,
            {"categories": categories, "category": category},
            format="json",
        )

    def test_cross_user_category_cannot_influence_response(self):
        """THE core P0 assertion: user_b's bookmarks must be invisible to
        user_a's PUT decision. 'shared-cat' exists only under user_b; user_a
        adding it must succeed."""
        make_bookmark(self.user_b, title="b-only", category="shared-cat")
        self.authenticate(self.user_a)

        response = self.put_categories(
            self.user_a.id, ["shared-cat"], "shared-cat"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("shared-cat", response.data["categories"])
        self.user_a.refresh_from_db()
        self.assertIn("shared-cat", self.user_a.categories)

    def test_cross_user_category_case_insensitive_still_allowed(self):
        """iexact matching must apply within the caller's own rows only:
        user_b has 'Work', user_a adds lowercase 'work' -> allowed."""
        make_bookmark(self.user_b, title="b-upper", category="Work")
        self.authenticate(self.user_a)

        response = self.put_categories(self.user_a.id, ["work"], "work")

        self.assertEqual(response.status_code, 200)
        self.assertIn("work", response.data["categories"])

    def test_own_bookmarked_category_is_blocked_with_meaningful_body(self):
        """Duplicate prevention still works against the caller's own data --
        and the 403 now carries a real detail instead of empty errors."""
        make_bookmark(self.user_a, title="a-mine", category="mine")
        self.authenticate(self.user_a)

        response = self.put_categories(self.user_a.id, ["mine"], "mine")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(str(response.data.get("detail", "")).strip())
        self.user_a.refresh_from_db()
        self.assertNotIn("mine", self.user_a.categories or [])

    def test_own_bookmarked_category_case_insensitive_blocked(self):
        """'Mine' bookmarked; adding 'MINE' is still a duplicate."""
        make_bookmark(self.user_a, title="a-case", category="Mine")
        self.authenticate(self.user_a)

        response = self.put_categories(self.user_a.id, ["MINE"], "MINE")

        self.assertEqual(response.status_code, 403)

    def test_put_to_another_users_pk_never_touches_that_user(self):
        """Write path keeps pinning the caller (F3): the URL pk is ignored
        and the update lands on request.user -- so user_b's data can never
        be modified through user_a's session."""
        self.authenticate(self.user_a)

        response = self.put_categories(self.user_b.id, ["x"], "x")

        self.assertEqual(response.status_code, 200)
        self.user_b.refresh_from_db()
        self.assertNotIn("x", self.user_b.categories or [])
        self.user_a.refresh_from_db()
        self.assertIn("x", self.user_a.categories or [])

    def test_get_returns_callers_own_categories(self):
        self.authenticate(self.user_a)
        self.user_a.categories = ["alpha", "beta"]
        self.user_a.save(update_fields=["categories"])

        response = self.client.get("/api/user/categories/%d" % self.user_a.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(response.data["categories"]), ["alpha", "beta"])
