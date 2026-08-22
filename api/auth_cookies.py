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
origin outside {FRONTEND_URL, BACKEND_URL} -- see
docs/plans/p2-token-storage-decision.md for the full analysis.
"""

from django.conf import settings

REFRESH_COOKIE_NAME = "refresh_token"
#: Covers /api/login/refresh/ and /api/login/logout/.
REFRESH_COOKIE_PATH = "/api/login/"


def _allowed_origins():
    origins = {settings.FRONTEND_URL, settings.BACKEND_URL}
    return {o.rstrip("/") for o in origins}


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
