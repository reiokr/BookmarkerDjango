"""Content-Security-Policy delivery -- roadmap step [2.1].

Emits a per-response CSP header on every Django-served response. The SPA
itself is currently served by the CRA dev server / static build host, but
the header must already be correct for every response Django serves
(API JSON, admin, DRF browsable API, and any future template that serves
``frontend/build/index.html``).

Role (plan F14): compensating control for JWT-in-localStorage. If XSS
lands despite everything else, CSP bounds which scripts may run, what
they may load, and where they may send data.

Modes (settings.CSP_MODE, read via django-environ):

* ``enforce``  -> ``Content-Security-Policy`` (default; acceptance gate)
* ``report``   -> ``Content-Security-Policy-Report-Only`` (tuning phase)
* ``off``      -> no CSP header at all

Directive decisions are evidence-based (see docs/plans/p2-token-storage-decision.md):

* ``frame-ancestors 'none'`` -- mandatory; permanently kills the legacy
  extensionLogin framing vector (F4).
* ``script-src 'self' 'nonce-...'``, NO ``unsafe-inline`` -- verified:
  ``frontend/build/index.html`` contains no inline scripts (deferred
  external bundle only). The nonce keeps nonce-ready plumbing in place
  for any future inline bootstrap script.
* ``style-src 'self' 'unsafe-inline'`` -- DOCUMENTED DEVIATION (risk R6):
  MUI/Emotion inject runtime ``<style>`` tags via JS; blocking inline
  styles breaks all component styling.
* ``img-src 'self' data: https:`` -- bookmark preview images come from
  arbitrary scraped ``og:image`` origins (core feature), YouTube
  thumbnails (i.ytimg.com) included; data: covers inline placeholders.
"""

import secrets

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

#: Header names, keyed by CSP_MODE value.
CSP_HEADERS = {
    "enforce": "Content-Security-Policy",
    "report": "Content-Security-Policy-Report-Only",
}

VALID_MODES = tuple(CSP_HEADERS) + ("off",)


def resolve_mode():
    """Return the configured mode, failing loudly on a typo."""
    mode = getattr(settings, "CSP_MODE", "enforce")
    if mode not in VALID_MODES:
        raise ImproperlyConfigured(
            "CSP_MODE must be one of %r, got %r" % (VALID_MODES, mode)
        )
    return mode


def build_csp_policy(nonce):
    """Build the policy string for one response.

    Kept separate from the middleware so tests can assert directives
    without going through the request cycle.
    """
    return "; ".join(
        [
            "default-src 'self'",
            # No 'unsafe-inline': the built index.html has no inline
            # scripts; the nonce is plumbing for future inline bootstraps.
            "script-src 'self' 'nonce-%s'" % nonce,
            # Documented deviation (R6): Emotion/MUI inject runtime styles.
            "style-src 'self' 'unsafe-inline'",
            # og:image previews of user bookmarks live on arbitrary hosts.
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            # Mandatory: no site may frame this app (extensionLogin F4).
            "frame-ancestors 'none'",
            "form-action 'self'",
        ]
    )


class CspMiddleware:
    """Stamp a CSP header with a fresh per-response nonce."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        nonce = secrets.token_urlsafe(16)
        # Templates can reference {{ request.csp_nonce }} if an inline
        # script ever becomes necessary.
        request.csp_nonce = nonce

        response = self.get_response(request)

        mode = resolve_mode()
        if mode == "off":
            return response
        response[CSP_HEADERS[mode]] = build_csp_policy(nonce)
        return response
