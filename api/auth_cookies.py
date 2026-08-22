"""HttpOnly refresh-token cookie plumbing -- roadmap step [2.2], option (a).

The refresh JWT moves out of localStorage into an HttpOnly SameSite=Lax
cookie scoped to the auth-token endpoints; the short-lived access token
stays client-side exactly as before.

Cookie contract:

* name      ``refresh_token``
* path      ``/api/login/`` -- covers ``/api/login/refresh/`` AND
            ``/api/login/logout/`` (logout must READ the cookie to
            blacklist the token before deleting it, so the path has to
            span both consumers; nothing else ever receives it)
* flags     HttpOnly; SameSite=Lax; Secure unless DEBUG;
            Max-Age mirrors REFRESH_TOKEN_LIFETIME so the cookie cannot
            outlive the token it carries

CSRF posture: SameSite=Lax already blocks cross-site POSTs carrying the
cookie in all modern browsers. As defense-in-depth the cookie-consuming
POSTs additionally reject requests whose ``Origin`` header names an
origin outside {FRONTEND_URL, BACKEND_URL} -- each configured loopback
URL also accepts its localhost <-> 127.0.0.1 alias, because CRA's dev
proxy rewrites proxied requests' Origin to the proxy target -- see
docs/plans/p2-token-storage-decision.md for the full analysis.
"""

from urllib.parse import urlsplit

from django.conf import settings

REFRESH_COOKIE_NAME = "refresh_token"
#: Covers /api/login/refresh/ and /api/login/logout/.
REFRESH_COOKIE_PATH = "/api/login/"

#: The two spellings of "this same machine" in dev; either may arrive at
#: Django because react-dev-utils' onProxyReq rewrites Origin to the
#: proxy target (frontend/package.json ``proxy``).
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1"}


def _origin_forms(url):
    """Configured origin plus its loopback alias, slash-normalised.

    Non-loopback hosts gain no aliases: production must match its
    configured URL exactly.
    """
    parts = urlsplit(url)
    if parts.hostname not in _LOOPBACK_HOSTS:
        return {url.rstrip("/")}
    port = f":{parts.port}" if parts.port else ""
    return {f"{parts.scheme}://{host}{port}" for host in _LOOPBACK_HOSTS}


def _allowed_origins():
    origins = set()
    for url in (settings.FRONTEND_URL, settings.BACKEND_URL):
        origins |= _origin_forms(url)
    return origins


def origin_allowed(request):
    """True unless a browser sent a cross-site Origin we do not serve."""
    origin = request.headers.get("Origin")
    if not origin:
        # No Origin header -> not a browser-driven cross-site request.
        return True
    return origin.rstrip("/") in _allowed_origins()


def set_refresh_cookie(response, token_str):
    """Attach the rotated/current refresh token as Set-Cookie."""
    max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token_str,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=not settings.DEBUG,
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response):
    """Expire the refresh cookie (logout / invalid session)."""
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        samesite="Lax",
    )
