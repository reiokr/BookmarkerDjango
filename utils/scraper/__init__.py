"""Scrape metadata from target URL -- SSRF-hardened (audit spec §5).

Guard stack, in order:

1. Scheme allowlist: http/https only.
2. Resolve-and-block: every address the host resolves to must be public;
   IPv4-mapped IPv6 is unwrapped first; the blocked set covers private,
   loopback, link-local, multicast, unspecified and reserved ranges plus
   CGNAT 100.64.0.0/10 (not flagged ``is_private`` on current Pythons).
3. Redirects are NOT followed blindly: ``allow_redirects=False`` and each
   3xx Location is absolutized and re-validated per hop, max 3 hops.
4. Timeouts (3.05s connect / 10s read) and a 1 MiB body cap via
   ``stream=True`` + bounded ``raw.read``.
5. Content-Type gate: text/* only.

Every violation raises the typed :class:`ScrapeBlocked`; callers map it to
a client-facing JSON error -- never a 500, never internal diagnostics.
"""
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from .scrape import (get_description,  # get_favicon,; get_theme_color
                     get_image, get_site_name, get_title)

ALLOWED_SCHEMES = frozenset({"http", "https"})
MAX_REDIRECT_HOPS = 3
MAX_BODY_BYTES = 1_048_576  # 1 MiB -- HTML metadata never needs more
CONNECT_TIMEOUT_SECONDS = 3.05
READ_TIMEOUT_SECONDS = 10

# 100.64.0.0/10 (CGNAT) is part of the audit-spec blocked matrix but is not
# covered by ipaddress.is_private on all Python versions.
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")

_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}


class ScrapeBlocked(Exception):
    """Scrape target violates the SSRF guard (scheme/host/size/type)."""


def _assert_public_address(addr_text):
    try:
        addr = ipaddress.ip_address(addr_text)
    except ValueError as exc:
        raise ScrapeBlocked("resolved an unparseable address") from exc
    # IPv4-mapped IPv6 (::ffff:10.0.0.1) must be judged by its v4 form.
    mapped = getattr(addr, "ipv4_mapped", None)
    if mapped is not None:
        addr = mapped
    if (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
        or addr.is_reserved
        or addr in _CGNAT_NETWORK
    ):
        raise ScrapeBlocked("target resolves to a blocked address")


def _assert_public_host(hostname):
    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ScrapeBlocked("host does not resolve") from exc
    for info in addrinfos:
        _assert_public_address(info[4][0])


def _assert_safe_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise ScrapeBlocked("unsupported URL scheme")
    hostname = parts.hostname
    if not hostname:
        raise ScrapeBlocked("URL has no resolvable host")
    _assert_public_host(hostname)


def fetch_html(url):
    """Fetch ``url`` under the full SSRF guard; return raw HTML bytes."""
    current_url = url
    for _hop in range(MAX_REDIRECT_HOPS + 1):
        # Re-validate scheme AND resolved host on EVERY hop -- redirects
        # must never smuggle us onto an internal network.
        _assert_safe_url(current_url)
        with requests.get(
            current_url,
            headers=_HEADERS,
            allow_redirects=False,
            stream=True,
            timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
        ) as response:
            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location", "")
                if not location:
                    raise ScrapeBlocked("redirect without Location header")
                current_url = urljoin(current_url, location)
                continue
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("text/"):
                raise ScrapeBlocked("non-text content type")
            body = response.raw.read(MAX_BODY_BYTES + 1, decode_content=True)
            break
    else:
        raise ScrapeBlocked("too many redirects")

    if len(body) > MAX_BODY_BYTES:
        raise ScrapeBlocked("response body exceeds size cap")
    return body


def scrape_page_metadata(url):
    """Scrape target URL for metadata (SSRF-guarded)."""
    html = BeautifulSoup(fetch_html(url), 'html.parser')
    metadata = {
        'title': get_title(html),
        'description': get_description(html),
        'image_url': get_image(html),
        'sitename': get_site_name(html, url),
        'url': url
        # 'favicon': get_favicon(html, url),
        # 'color': get_theme_color(html),
    }
    return metadata
