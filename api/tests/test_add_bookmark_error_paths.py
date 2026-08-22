"""View-level regression tests for audit spec §5.6 / §8.3 -- AddBookmark.post
error normalization.

Pins that every failure mode of the scrape path surfaces as a client-facing
JSON response -- never a 500, never internal diagnostics:

* missing url/category -> 400 (was KeyError -> 500)
* guard violation (ScrapeBlocked) -> 400 with a reason string
* upstream timeout / connection failure -> 504
* other requests errors -> 502
* zero-item YouTube responses -> 400 (was IndexError -> 500)

All network is mocked; no real outbound calls.
"""

from unittest.mock import patch

import requests
from django.core.cache import cache
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import CustomUser
from utils.scraper import ScrapeBlocked

PASSWORD = "bm-error-paths-pass-1"

BM_URL = "https://example.com/article"


def make_user(email):
    return CustomUser.objects.create_user(
        email=email, password=PASSWORD, is_active=True
    )


class AddBookmarkErrorPathTests(APITestCase):
    def setUp(self):
        # bm_create throttle bucket lives in the shared LocMemCache.
        cache.clear()
        self.user = make_user("bm-errors@example.com")
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % token)

    def _post(self, payload):
        return self.client.post("/api/bm", payload, format="json")

    def test_missing_url_is_400_not_500(self):
        response = self._post({"category": "work"})
        self.assertEqual(response.status_code, 400)

    def test_missing_category_is_400_not_500(self):
        response = self._post({"url": BM_URL})
        self.assertEqual(response.status_code, 400)

    def test_scrape_guard_violation_maps_to_400_json(self):
        with patch(
            "api.views.scrape_page_metadata",
            side_effect=ScrapeBlocked(
                "target resolves to a blocked address"
            ),
        ):
            response = self._post({"url": BM_URL, "category": "work"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)
        self.assertIn("blocked", str(response.data["detail"]))

    def test_upstream_timeout_maps_to_504(self):
        with patch(
            "api.views.scrape_page_metadata",
            side_effect=requests.exceptions.Timeout,
        ):
            response = self._post({"url": BM_URL, "category": "work"})

        self.assertEqual(response.status_code, 504)

    def test_connection_failure_maps_to_504(self):
        with patch(
            "api.views.scrape_page_metadata",
            side_effect=requests.exceptions.ConnectionError,
        ):
            response = self._post({"url": BM_URL, "category": "work"})

        self.assertEqual(response.status_code, 504)

    def test_other_request_errors_map_to_502(self):
        with patch(
            "api.views.scrape_page_metadata",
            side_effect=requests.exceptions.TooManyRedirects,
        ):
            response = self._post({"url": BM_URL, "category": "work"})

        self.assertEqual(response.status_code, 502)

    def test_zero_item_youtube_response_is_400_not_500(self):
        # Deleted/private videos come back with an empty items list.
        with patch(
            "utils.fetch_youtube.fetch_Video", return_value={"items": []}
        ):
            response = self._post(
                {
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "category": "work",
                }
            )

        self.assertEqual(response.status_code, 400)

    def test_happy_path_still_creates_bm_bookmark(self):
        metadata = {
            "title": "An Example Article",
            "description": "Some description",
            "image_url": {"default": "https://example.com/img.jpg"},
            "sitename": "example.com",
            "url": BM_URL,
        }
        with patch(
            "api.views.scrape_page_metadata", return_value=metadata
        ):
            response = self._post({"url": BM_URL, "category": "work"})

        self.assertEqual(response.status_code, 201)
