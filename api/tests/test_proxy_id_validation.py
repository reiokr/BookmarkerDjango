"""Regression tests for audit spec §4.1 -- proxy-view ID validation.

Every YouTube-proxy view must reject non-conforming IDs with 400 BEFORE
reaching googleapiclient. These tests mock every upstream util and assert it
is NEVER called on the invalid path (no doomed quota-burning API call), plus
positive controls proving valid-format IDs still pass through to the mocked
util.
"""

from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser

PASSWORD = "proxy-validation-pass-1"

VIDEO_ID = "dQw4w9WgXcQ"                      # 11 chars [A-Za-z0-9_-]
PLAYLIST_ID = "PLFgquLnL59alW_7ThW"           # 19 chars
CHANNEL_ID = "UC" + "a" * 22                  # canonical UC + 22
COMMENT_ID = "commentid12345"                 # >=10 chars
PAGE_TOKEN = "CAMQAA"

BAD_VIDEO_ID = "short"                        # <11 chars
BAD_PLAYLIST_ID = "shortlist"                 # <12 chars
BAD_CHANNEL_ID = "UCtooshort"                 # not UC + 22
BAD_COMMENT_ID = "abc"                        # <10 chars
BAD_PAGE_TOKEN = "bad token!"                 # space + punctuation


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


class ProxyValidationTestBase(APITestCase):
    def setUp(self):
        # Throttle history lives in the shared LocMemCache; clear it so
        # validation tests never trip the per-minute scopes.
        cache.clear()
        self.user = make_user("proxy-validate@example.com")
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)


class VideoIdFamilyTests(ProxyValidationTestBase):
    """video_id consumers: GetVideoData / comments / rate / related."""

    def test_get_video_data_rejects_bad_video_id(self):
        with patch("api.views.fetch_youtube.fetch_Video") as fetch:
            response = self.client.get("/api/bm/video/%s" % BAD_VIDEO_ID)

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_video_comments_reject_bad_video_id(self):
        with patch("api.views.fetch_video_comments") as fetch:
            response = self.client.get(
                "/api/bm/comments/%s/time" % BAD_VIDEO_ID
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_next_page_comments_reject_bad_video_id(self):
        with patch("api.views.fetch_next_comments") as fetch:
            response = self.client.get(
                "/api/bm/comments/%s/%s/time"
                % (BAD_VIDEO_ID, PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_rate_video_rejects_bad_video_id(self):
        with patch("api.views.rate_video") as rate:
            response = self.client.get("/api/bm/rate/%s" % BAD_VIDEO_ID)

        self.assertEqual(response.status_code, 400)
        rate.assert_not_called()

    def test_related_videos_reject_bad_video_id(self):
        with patch("api.views.search_related_videos") as search:
            response = self.client.get(
                "/api/video/%s/related-videos" % BAD_VIDEO_ID
            )

        self.assertEqual(response.status_code, 400)
        search.assert_not_called()

    def test_get_video_data_accepts_valid_video_id(self):
        payload = {
            "items": [
                {
                    "snippet": {
                        "title": "T",
                        "description": "D",
                        "thumbnails": {
                            "default": {"url": "https://example.com/t.jpg"}
                        },
                        "channelId": CHANNEL_ID,
                        "channelTitle": "C",
                        "tags": ["x"],
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "categoryId": "10",
                    },
                    "contentDetails": {"duration": "PT3M"},
                    "status": {"privacyStatus": "public"},
                    "statistics": {
                        "viewCount": "1", "likeCount": "1",
                        "commentCount": "1",
                    },
                }
            ]
        }
        with patch("api.views.fetch_youtube.fetch_Video",
                   return_value=payload):
            response = self.client.get("/api/bm/video/%s" % VIDEO_ID)

        self.assertEqual(response.status_code, 200)


class PlaylistFamilyTests(ProxyValidationTestBase):
    """playlist id consumers: YouTubeList / AddPlaylistTOBookmarks."""

    def test_youtube_list_rejects_bad_list_id(self):
        with patch("utils.find_playlist.get_playlist_items") as items:
            response = self.client.get("/api/bm/list/%s" % BAD_PLAYLIST_ID)

        self.assertEqual(response.status_code, 400)
        items.assert_not_called()

    def test_add_playlist_to_bookmarks_rejects_bad_pl_id(self):
        with patch("api.views.get_playlist_item") as item:
            response = self.client.get(
                "/api/add-playlist-to-bookmarks/%s" % BAD_PLAYLIST_ID
            )

        self.assertEqual(response.status_code, 400)
        item.assert_not_called()

    def test_youtube_list_accepts_valid_list_id(self):
        playlist_page = {
            "items": [
                {
                    "id": "UExxx_0",
                    "snippet": {
                        "publishedAt": "2024-01-01T00:00:00Z",
                        "title": "Item title",
                        "description": "Item description",
                        "thumbnails": {},
                        "position": 0,
                    },
                    "contentDetails": {"videoId": VIDEO_ID},
                }
            ],
        }
        with patch("utils.find_playlist.get_playlist_items",
                   return_value=playlist_page):
            response = self.client.get("/api/bm/list/%s" % PLAYLIST_ID)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["video_id"], VIDEO_ID)


class ChannelFamilyTests(ProxyValidationTestBase):
    """channel_id consumers: ChannelPlaylists / ChannelNextPlaylists."""

    def test_channel_playlists_reject_bad_channel_id(self):
        with patch("api.views.fetch_channel_playlists") as fetch:
            response = self.client.get(
                "/api/channel/playlists/%s" % BAD_CHANNEL_ID
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_channel_next_playlists_reject_bad_channel_id(self):
        with patch("api.views.fetch_channel_next_playlists") as fetch:
            response = self.client.get(
                "/api/channel/next-playlists/%s/%s"
                % (BAD_CHANNEL_ID, PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_channel_playlists_accept_valid_channel_id(self):
        with patch("api.views.fetch_channel_playlists", return_value=[]):
            response = self.client.get(
                "/api/channel/playlists/%s" % CHANNEL_ID
            )

        self.assertEqual(response.status_code, 200)


class CommentFamilyTests(ProxyValidationTestBase):
    """comment parent_id consumers: Replies / RepliesNextPage."""

    def test_replies_reject_bad_parent_id(self):
        with patch("api.views.get_replies") as replies:
            response = self.client.get(
                "/api/bm/comment/replies/%s" % BAD_COMMENT_ID
            )

        self.assertEqual(response.status_code, 400)
        replies.assert_not_called()

    def test_next_replies_reject_bad_parent_id(self):
        with patch("api.views.get_next_replies") as replies:
            response = self.client.get(
                "/api/bm/comment/nextreplies/%s/%s"
                % (BAD_COMMENT_ID, PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        replies.assert_not_called()

    def test_next_replies_reject_bad_page_token(self):
        with patch("api.views.get_next_replies") as replies:
            response = self.client.get(
                "/api/bm/comment/nextreplies/%s/%s"
                % (COMMENT_ID, BAD_PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        replies.assert_not_called()

    def test_replies_accept_valid_parent_id(self):
        with patch("api.views.get_replies", return_value={"items": []}):
            response = self.client.get(
                "/api/bm/comment/replies/%s" % COMMENT_ID
            )

        self.assertEqual(response.status_code, 200)


class PageTokenAndOrderTests(ProxyValidationTestBase):
    """page_token + order enum consumers."""

    def test_next_page_comments_reject_bad_page_token(self):
        with patch("api.views.fetch_next_comments") as fetch:
            response = self.client.get(
                "/api/bm/comments/%s/%s/time"
                % (VIDEO_ID, BAD_PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_channel_next_playlists_reject_bad_token(self):
        with patch("api.views.fetch_channel_next_playlists") as fetch:
            response = self.client.get(
                "/api/channel/next-playlists/%s/%s"
                % (CHANNEL_ID, BAD_PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_video_comments_reject_unknown_order_enum(self):
        with patch("api.views.fetch_video_comments") as fetch:
            response = self.client.get(
                "/api/bm/comments/%s/newest" % VIDEO_ID
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_next_page_comments_reject_unknown_order_enum(self):
        with patch("api.views.fetch_next_comments") as fetch:
            response = self.client.get(
                "/api/bm/comments/%s/%s/newest"
                % (VIDEO_ID, PAGE_TOKEN)
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_video_comments_accept_known_order_enum(self):
        with patch("api.views.fetch_video_comments",
                   return_value={"items": []}):
            response = self.client.get(
                "/api/bm/comments/%s/relevance" % VIDEO_ID
            )

        self.assertEqual(response.status_code, 200)


class AddBookmarkPostExtractionTests(ProxyValidationTestBase):
    """§4.1 post-extraction asserts inside AddBookmark.post."""

    def _post_url(self, url):
        return self.client.post(
            "/api/bm", {"url": url, "category": "work"}, format="json"
        )

    def test_nonconforming_extracted_video_id_is_400(self):
        # extractVideoId happily captures "short" from watch?v=short;
        # the post-extraction assert must stop it before fetch_Video.
        with patch("utils.fetch_youtube.fetch_Video") as fetch:
            response = self._post_url(
                "https://www.youtube.com/watch?v=%s" % BAD_VIDEO_ID
            )

        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_nonconforming_extracted_list_id_is_400(self):
        # extractPlaylistId captures "shortlist" (9 chars < 12 minimum).
        url = (
            "https://www.youtube.com/watch?v=%s&list=%s"
            % (VIDEO_ID, BAD_PLAYLIST_ID)
        )
        with patch("utils.fetch_youtube.fetch_Video"), \
                patch("utils.find_playlist.get_playlist_items") as items:
            response = self._post_url(url)

        self.assertEqual(response.status_code, 400)
        items.assert_not_called()
