"""Ownership-enforcement regression suite (security roadmap step [0.6]).

Locks in the CURRENT-CORRECT cross-user isolation of:

* ``BmListView``        -- GET queryset filtered by ``owner_id=request.user.id``,
                           POST pins ``owner=request.user`` via perform_create.
* ``BmListSearchView``  -- same manual owner filter applied before the
                           title/description search union; POST pins owner.
* ``BmDetailView``      -- hand-rolled check in get_object:
                           ``request.user.id == bookmark.owner_id`` else
                           PermissionDenied, guarding GET/PUT/DELETE.
* ``UserDetail``        -- hand-rolled check in get_object:
                           ``request.user.id == pk`` else PermissionDenied,
                           guarding GET/PUT/DELETE.
* ``OptionsView``       -- hand-rolled per-user scoping: GET filters
                           ``owner=request.user.id``, PUT gets/creates the row
                           owned by ``request.user.id``.

Deliberately NOT asserted here:

* ``IsOwnerOrReadOnly`` / ``check_object_permissions`` -- fact F7: the class is
  attached to 13 views but never executes (no check_object_permissions call
  anywhere). Ownership is enforced by the manual filters/checks above, so this
  suite asserts those explicitly and gives the permission class no credit.
* ``BmDetailView`` missing-pk behaviour -- step [0.5] is converting the 500 to
  a 404 concurrently; asserting either outcome would fight that lane.
* ``UserDetail`` last_login side effect on GET -- known defect scheduled for
  fix at [1.3]; locking it in would pin the bug.

Targets behaviour, not line numbers (Lane A edits views.py concurrently).
"""

from datetime import datetime, timezone as dt_timezone

from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Bm, CustomUser, UserOptions
from api.serializers import BmSerializer

PASSWORD = "ownership-suite-pass-1"


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


def bm_payload(**overrides):
    payload = {
        "title": "Created bookmark",
        "category": "work",
        "bm_type": "video",
        "description": "created by ownership suite",
        "thumbnails": {"default": {"url": "https://example.com/new.jpg"}},
        "url": "https://example.com/watch?v=new",
        "video_id": "newvideo1",
        "channel_id": "UCnewchannel0000000000000",
        "channel_title": "New Channel",
        "keywords": ["fresh"],
        "length": "1:00",
        "privacy_status": "public",
        "publish_date": "2024-02-02T08:00:00Z",
        "original_category": "work",
    }
    payload.update(overrides)
    return payload


class OwnershipTestBase(APITestCase):
    def setUp(self):
        self.user_a = make_user("owner-a@example.com")
        self.user_b = make_user("owner-b@example.com")
        self.client = APIClient()

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def unauthenticate(self):
        self.client.credentials()


class BmListViewOwnershipTests(OwnershipTestBase):
    """GET /bm/category/<category> and POST to it."""

    def test_get_returns_only_callers_bookmarks_in_category(self):
        mine_1 = make_bookmark(self.user_a, title="mine one")
        mine_2 = make_bookmark(self.user_a, title="mine two")
        theirs_1 = make_bookmark(self.user_b, title="theirs one")
        theirs_2 = make_bookmark(self.user_b, title="theirs two")

        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/category/work")

        self.assertEqual(response.status_code, 200)
        returned_ids = [row["id"] for row in response.data]
        self.assertEqual(sorted(returned_ids), sorted([mine_1.id, mine_2.id]))
        self.assertNotIn(theirs_1.id, returned_ids)
        self.assertNotIn(theirs_2.id, returned_ids)
        for row in response.data:
            self.assertEqual(row["owner"], self.user_a.id)

    def test_get_is_scoped_even_when_other_users_share_the_category(self):
        # Same category name for both users: the owner filter must still win.
        mine = make_bookmark(self.user_a, category="shared-cat")
        theirs = make_bookmark(self.user_b, category="shared-cat")

        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/category/shared-cat")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [mine.id])
        self.assertNotIn(theirs.id, [row["id"] for row in response.data])

    def test_post_pins_owner_to_request_user(self):
        self.authenticate(self.user_a)
        response = self.client.post(
            "/api/bm/category/work", bm_payload(), format="json"
        )

        self.assertEqual(response.status_code, 201)
        created = Bm.objects.get(pk=response.data["id"])
        self.assertEqual(created.owner_id, self.user_a.id)
        self.assertEqual(response.data["owner"], self.user_a.id)
        # Nothing leaked into user B's collection.
        self.assertFalse(Bm.objects.filter(owner=self.user_b).exists())

    def test_unauthenticated_get_is_rejected(self):
        make_bookmark(self.user_a)
        self.unauthenticate()
        response = self.client.get("/api/bm/category/work")
        self.assertEqual(response.status_code, 401)


class BmListSearchViewOwnershipTests(OwnershipTestBase):
    """GET/POST /bm/category/<category>/<search>."""

    def test_search_returns_only_callers_matches(self):
        mine = make_bookmark(self.user_a, title="django tutorial part one")
        theirs = make_bookmark(self.user_b, title="django tutorial part two")

        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/category/work/django")

        self.assertEqual(response.status_code, 200)
        returned_ids = [row["id"] for row in response.data]
        self.assertIn(mine.id, returned_ids)
        self.assertNotIn(theirs.id, returned_ids)

    def test_search_matching_only_other_users_rows_returns_empty(self):
        # The term matches ONLY user B's bookmark; user A must see nothing.
        make_bookmark(self.user_b, title="secret needle only b has")

        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/category/work/needle")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.data), [])

    def test_description_matches_are_owner_scoped_too(self):
        mine = make_bookmark(self.user_a, title="unrelated title")
        Bm.objects.filter(pk=mine.pk).update(
            description="hidden zebra inside description"
        )
        theirs = make_bookmark(self.user_b, title="another unrelated title")
        Bm.objects.filter(pk=theirs.pk).update(
            description="also mentions zebra inside description"
        )

        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/category/work/zebra")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [mine.id])

    def test_post_pins_owner_to_request_user(self):
        self.authenticate(self.user_a)
        response = self.client.post(
            "/api/bm/category/work/django", bm_payload(), format="json"
        )

        self.assertEqual(response.status_code, 201)
        created = Bm.objects.get(pk=response.data["id"])
        self.assertEqual(created.owner_id, self.user_a.id)

    def test_unauthenticated_get_is_rejected(self):
        make_bookmark(self.user_a, title="searchable")
        self.unauthenticate()
        response = self.client.get("/api/bm/category/work/searchable")
        self.assertEqual(response.status_code, 401)


class BmDetailViewOwnershipTests(OwnershipTestBase):
    """GET/PUT/DELETE /bm/<pk> guarded by the manual owner comparison."""

    def setUp(self):
        super().setUp()
        self.mine = make_bookmark(self.user_a, title="a keeps this")
        self.theirs = make_bookmark(self.user_b, title="b keeps this")

    def test_owner_can_read_own_bookmark(self):
        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/%d" % self.mine.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.mine.pk)
        self.assertEqual(response.data["title"], "a keeps this")

    def test_other_user_cannot_read_foreign_bookmark(self):
        self.authenticate(self.user_a)
        response = self.client.get("/api/bm/%d" % self.theirs.pk)

        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_update_foreign_bookmark(self):
        self.authenticate(self.user_a)
        response = self.client.put(
            "/api/bm/%d" % self.theirs.pk,
            {"video_data": {"list_id": None, "list_index": None}},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.title, "b keeps this")

    def test_other_user_cannot_delete_foreign_bookmark(self):
        self.authenticate(self.user_a)
        response = self.client.delete("/api/bm/%d" % self.theirs.pk)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Bm.objects.filter(pk=self.theirs.pk).exists())

    def test_owner_can_update_own_bookmark(self):
        payload = dict(BmSerializer(self.mine).data)
        payload["title"] = "renamed by owner"

        self.authenticate(self.user_a)
        response = self.client.put(
            "/api/bm/%d" % self.mine.pk,
            {"video_data": payload},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.title, "renamed by owner")

    def test_owner_can_delete_own_bookmark(self):
        self.authenticate(self.user_a)
        response = self.client.delete("/api/bm/%d" % self.mine.pk)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Bm.objects.filter(pk=self.mine.pk).exists())

    def test_unauthenticated_get_is_rejected(self):
        self.unauthenticate()
        response = self.client.get("/api/bm/%d" % self.mine.pk)
        self.assertEqual(response.status_code, 401)


class UserDetailOwnershipTests(OwnershipTestBase):
    """GET/PUT/DELETE /users/<pk> guarded by request.user.id == pk."""

    def test_owner_can_read_own_profile(self):
        self.authenticate(self.user_a)
        response = self.client.get("/api/users/%d" % self.user_a.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], self.user_a.email)

    def test_other_user_cannot_read_foreign_profile(self):
        self.authenticate(self.user_a)
        response = self.client.get("/api/users/%d" % self.user_b.pk)

        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_update_foreign_profile(self):
        self.authenticate(self.user_a)
        response = self.client.put(
            "/api/users/%d" % self.user_b.pk,
            {"first_name": "hijacked"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.user_b.refresh_from_db()
        self.assertNotEqual(self.user_b.first_name, "hijacked")

    def test_other_user_cannot_delete_foreign_account(self):
        self.authenticate(self.user_a)
        response = self.client.delete("/api/users/%d" % self.user_b.pk)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(CustomUser.objects.filter(pk=self.user_b.pk).exists())

    def test_unauthenticated_get_is_rejected(self):
        self.unauthenticate()
        response = self.client.get("/api/users/%d" % self.user_a.pk)
        self.assertEqual(response.status_code, 401)


class OptionsViewOwnershipTests(OwnershipTestBase):
    """GET/PUT /user/options scoped manually to request.user."""

    def setUp(self):
        super().setUp()
        self.options_a = UserOptions.objects.create(
            theme=0, localization="en", settings={"lang": "en"},
            owner=self.user_a,
        )
        self.options_b = UserOptions.objects.create(
            theme=1, localization="fi", settings={"lang": "fi"},
            owner=self.user_b,
        )

    def test_get_returns_only_callers_options(self):
        self.authenticate(self.user_a)
        response = self.client.get("/api/user/options")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["owner"], self.user_a.id)
        self.assertEqual(response.data[0]["theme"], 0)
        self.assertNotEqual(response.data[0]["theme"], self.options_b.theme)

    def test_put_updates_only_callers_row(self):
        self.authenticate(self.user_a)
        response = self.client.put(
            "/api/user/options",
            {"theme": 5, "localization": "de", "settings": {"lang": "de"}},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.options_a.refresh_from_db()
        self.options_b.refresh_from_db()
        self.assertEqual(self.options_a.theme, 5)
        self.assertEqual(self.options_a.localization, "de")
        # User B's row is untouched by A's write.
        self.assertEqual(self.options_b.theme, 1)
        self.assertEqual(self.options_b.localization, "fi")
        self.assertEqual(UserOptions.objects.count(), 2)

    def test_put_creates_row_owned_by_caller_when_absent(self):
        user_c = make_user("owner-c@example.com")
        self.authenticate(user_c)
        response = self.client.put(
            "/api/user/options",
            {"theme": 2, "localization": "sv", "settings": {}},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created = UserOptions.objects.get(owner=user_c)
        self.assertEqual(created.owner_id, user_c.id)
        self.assertEqual(created.theme, 2)
        # Pre-existing rows for A and B are unaffected.
        self.assertEqual(UserOptions.objects.count(), 3)

    def test_unauthenticated_get_is_rejected(self):
        self.unauthenticate()
        response = self.client.get("/api/user/options")
        self.assertEqual(response.status_code, 401)
