"""Unit tests for the SSRF guard in utils/scraper (audit spec §5).

Every network touch is mocked -- socket.getaddrinfo and requests.get are
patched inside the scraper module namespace, so these tests make ZERO real
outbound calls.

Covered: scheme allowlist; the exact blocked-range matrix from spec §5.2
(including IPv4-mapped IPv6 and CGNAT); unresolvable hosts; redirect hops
re-validated per hop (redirect-to-private rejected, hop cap enforced);
1 MiB body cap (over -> rejected, at-cap -> accepted); text/* content gate.
"""

import socket
from unittest.mock import patch

from django.test import SimpleTestCase

from utils.scraper import (
    MAX_BODY_BYTES,
    MAX_REDIRECT_HOPS,
    ScrapeBlocked,
    fetch_html,
)

PUBLIC_V4 = "93.184.216.34"
PUBLIC_V6 = "2606:2800:220:1:248:1893:25c8:1946"


def addrinfo(ip):
    """A getaddrinfo-shaped single result for the given address."""
    if ":" in ip:
        sockaddr = (ip, 0, 0, 0)
        family = socket.AF_INET6
    else:
        sockaddr = (ip, 0)
        family = socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", sockaddr)]


class FakeRaw:
    def __init__(self, payload):
        self._payload = payload

    def read(self, size, decode_content=True):
        return self._payload[:size]


class FakeResponse:
    def __init__(self, body=b"<html></html>", content_type="text/html",
                 headers=None):
        self.raw = FakeRaw(body)
        self.headers = {"Content-Type": content_type}
        if headers:
            self.headers.update(headers)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    @property
    def is_redirect(self):
        return False

    @property
    def is_permanent_redirect(self):
        return False


class RedirectResponse(FakeResponse):
    def __init__(self, location):
        super().__init__()
        self.headers["Location"] = location

    @property
    def is_redirect(self):
        return True


class SchemeAllowlistTests(SimpleTestCase):
    def test_non_http_schemes_are_rejected_before_any_network_io(self):
        for url in (
            "ftp://example.com/file",
            "file:///etc/passwd",
            "gopher://example.invalid/",
            "javascript://example.com/",
        ):
            with self.subTest(url=url), \
                    patch("utils.scraper.socket.getaddrinfo") as resolve, \
                    patch("utils.scraper.requests.get") as get:
                with self.assertRaises(ScrapeBlocked):
                    fetch_html(url)
                resolve.assert_not_called()
                get.assert_not_called()

    def test_http_and_https_pass_the_scheme_gate(self):
        for url in ("https://example.com/page", "http://example.com/page"):
            with self.subTest(url=url), \
                    patch("utils.scraper.socket.getaddrinfo",
                          return_value=addrinfo(PUBLIC_V4)), \
                    patch("utils.scraper.requests.get",
                          return_value=FakeResponse()):
                self.assertEqual(fetch_html(url), b"<html></html>")


class BlockedAddressMatrixTests(SimpleTestCase):
    """Spec §5.2: every listed range must be rejected."""

    BLOCKED_TARGETS = [
        # IPv4
        "0.0.0.0",          # unspecified / 0.0.0.0/8
        "10.0.0.1",         # RFC1918
        "127.0.0.1",        # loopback
        "169.254.169.254",  # link-local + cloud metadata endpoint
        "172.16.0.1",       # RFC1918
        "192.0.0.1",        # 192.0.0.0/24
        "192.168.0.1",      # RFC1918
        "198.18.0.1",       # benchmark range
        "100.64.0.1",       # CGNAT (not is_private on all Pythons)
        "224.0.0.1",        # multicast
        "240.0.0.1",        # reserved
        # IPv6
        "::1",              # loopback
        "::",               # unspecified
        "fc00::1",          # unique-local
        "fe80::1",          # link-local
        # IPv4-mapped IPv6 forms of the above
        "::ffff:10.0.0.1",
        "::ffff:127.0.0.1",
        "::ffff:169.254.169.254",
    ]

    def test_every_blocked_target_is_rejected_without_connecting(self):
        for ip in self.BLOCKED_TARGETS:
            with self.subTest(ip=ip), \
                    patch("utils.scraper.socket.getaddrinfo",
                          return_value=addrinfo(ip)), \
                    patch("utils.scraper.requests.get") as get:
                with self.assertRaises(ScrapeBlocked):
                    fetch_html("http://internal.example/")
                get.assert_not_called()

    def test_public_addresses_are_allowed(self):
        for ip in (PUBLIC_V4, PUBLIC_V6):
            with self.subTest(ip=ip), \
                    patch("utils.scraper.socket.getaddrinfo",
                          return_value=addrinfo(ip)), \
                    patch("utils.scraper.requests.get",
                          return_value=FakeResponse()):
                self.assertEqual(
                    fetch_html("https://example.com/"), b"<html></html>"
                )


class ResolutionAndRedirectTests(SimpleTestCase):
    def test_unresolvable_host_is_rejected(self):
        with patch("utils.scraper.socket.getaddrinfo",
                   side_effect=socket.gaierror(1, "Name or service not known")), \
                patch("utils.scraper.requests.get") as get:
            with self.assertRaises(ScrapeBlocked):
                fetch_html("http://does-not-exist.example/")
            get.assert_not_called()

    def test_redirect_to_private_host_is_blocked(self):
        responses = [RedirectResponse("http://internal.example/admin")]
        with patch("utils.scraper.socket.getaddrinfo",
                   side_effect=[addrinfo(PUBLIC_V4),
                                addrinfo("10.9.9.9")]), \
                patch("utils.scraper.requests.get",
                      side_effect=responses) as get:
            with self.assertRaises(ScrapeBlocked):
                fetch_html("https://example.com/start")

        # Only the FIRST (public) hop was ever fetched; the private target
        # was resolved-and-rejected before any connection attempt.
        self.assertEqual(get.call_count, 1)

    def test_more_than_max_hops_is_rejected(self):
        chain = [
            RedirectResponse("https://example.com/hop%d" % n)
            for n in range(MAX_REDIRECT_HOPS + 2)
        ]
        with patch("utils.scraper.socket.getaddrinfo",
                   return_value=addrinfo(PUBLIC_V4)), \
                patch("utils.scraper.requests.get",
                      side_effect=chain) as get:
            with self.assertRaises(ScrapeBlocked):
                fetch_html("https://example.com/start")
        self.assertEqual(get.call_count, MAX_REDIRECT_HOPS + 1)


class BodyCapAndContentTypeTests(SimpleTestCase):
    def _fetch_with_body(self, payload, **kwargs):
        with patch("utils.scraper.socket.getaddrinfo",
                   return_value=addrinfo(PUBLIC_V4)), \
                patch("utils.scraper.requests.get",
                      return_value=FakeResponse(payload, **kwargs)):
            return fetch_html("https://example.com/")

    def test_oversized_response_is_rejected(self):
        oversized = b"x" * (MAX_BODY_BYTES + 2)
        with self.assertRaises(ScrapeBlocked):
            self._fetch_with_body(oversized)

    def test_body_at_the_cap_is_accepted(self):
        at_cap = b"x" * MAX_BODY_BYTES
        self.assertEqual(len(self._fetch_with_body(at_cap)), MAX_BODY_BYTES)

    def test_non_text_content_type_is_rejected(self):
        with self.assertRaises(ScrapeBlocked):
            self._fetch_with_body(b"\x00\x01binary", content_type="application/octet-stream")

    def test_text_html_content_type_is_accepted(self):
        self.assertEqual(
            self._fetch_with_body(b"<html></html>",
                                  content_type="text/html; charset=utf-8"),
            b"<html></html>",
        )
