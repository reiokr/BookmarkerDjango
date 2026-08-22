"""Tests for bookmarker.csp -- roadmap step [2.1].

Asserts the CSP delivery contract on every Django-served response:

* header NAME follows CSP_MODE (enforce -> Content-Security-Policy,
  report -> Content-Security-Policy-Report-Only, off -> nothing);
* the mandatory ``frame-ancestors 'none'`` directive is always present;
* ``script-src`` carries a per-response nonce and NEVER contains
  'unsafe-inline' (the built index.html has no inline scripts);
* nonces are unique across responses;
* the documented style-src deviation ('unsafe-inline' for Emotion/MUI
  runtime styles, plan risk R6) is locked in by test;
* a bogus CSP_MODE fails loudly instead of silently emitting nothing.
"""

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from bookmarker.csp import build_csp_policy, resolve_mode

ENFORCE = "Content-Security-Policy"
REPORT_ONLY = "Content-Security-Policy-Report-Only"


class CspHeaderModeTests(TestCase):
    """The response must carry exactly one CSP header, named per mode."""

    def _get(self):
        return self.client.get("/api/")

    def test_enforce_mode_sets_enforce_header(self):
        with override_settings(CSP_MODE="enforce"):
            res = self._get()
        self.assertIn(ENFORCE, res)
        self.assertNotIn(REPORT_ONLY, res)

    def test_report_mode_sets_report_only_header(self):
        with override_settings(CSP_MODE="report"):
            res = self._get()
        self.assertIn(REPORT_ONLY, res)
        self.assertNotIn(ENFORCE, res)

    def test_off_mode_emits_nothing(self):
        with override_settings(CSP_MODE="off"):
            res = self._get()
        self.assertNotIn(ENFORCE, res)
        self.assertNotIn(REPORT_ONLY, res)

    def test_default_mode_is_enforce(self):
        # settings.py defaults CSP_MODE to 'enforce'; the acceptance gate
        # requires an enforced policy out of the box.
        from django.conf import settings

        self.assertEqual(settings.CSP_MODE, "enforce")
        res = self._get()
        self.assertIn(ENFORCE, res)


class CspPolicyDirectiveTests(TestCase):
    """Directive-level contract of the emitted policy."""

    def setUp(self):
        self.res = self.client.get("/api/")
        self.policy = self.res[ENFORCE]

    def _directive(self, name):
        for part in self.policy.split(";"):
            if part.strip().startswith(name):
                return part.strip()
        return ""

    def test_frame_ancestors_none_is_present(self):
        # Mandatory: kills the legacy extensionLogin framing vector (F4).
        self.assertEqual(self._directive("frame-ancestors"), "frame-ancestors 'none'")

    def test_script_src_has_nonce_and_no_unsafe_inline(self):
        script_src = self._directive("script-src")
        self.assertIn("'self'", script_src)
        self.assertTrue(script_src.startswith("script-src 'self' 'nonce-"))
        self.assertNotIn("'unsafe-inline'", script_src)

    def test_style_src_documents_the_r6_deviation(self):
        # Emotion/MUI inject runtime <style> tags; blocking inline styles
        # breaks all component styling. This deviation is deliberate and
        # recorded in docs/plans/p2-token-storage-decision.md.
        self.assertIn("'unsafe-inline'", self._directive("style-src"))

    def test_baseline_directives_present(self):
        self.assertEqual(self._directive("object-src"), "object-src 'none'")
        self.assertEqual(self._directive("base-uri"), "base-uri 'self'")
        self.assertEqual(self._directive("default-src"), "default-src 'self'")
        self.assertEqual(self._directive("connect-src"), "connect-src 'self'")

    def test_img_src_allows_remote_bookmark_previews(self):
        # og:image previews live on arbitrary scraped hosts; i.ytimg.com
        # thumbnails are included. data: covers inline placeholders.
        img_src = self._directive("img-src")
        for token in ("'self'", "data:", "https:"):
            self.assertIn(token, img_src)


class CspNonceTests(TestCase):
    """Every response gets its own nonce."""

    def test_nonce_unique_across_responses(self):
        first = self.client.get("/api/")
        second = self.client.get("/api/")
        n1 = first[ENFORCE].split("'nonce-")[1].split("'")[0]
        n2 = second[ENFORCE].split("'nonce-")[1].split("'")[0]
        self.assertNotEqual(n1, n2)

    def test_request_nonce_matches_response_header(self):
        handler = self.client.get("/api/")
        # The middleware exposes request.csp_nonce for template use; the
        # stamped policy must be built from that same value.
        request = handler.wsgi_request
        self.assertIn(
            "'nonce-%s'" % request.csp_nonce, handler[ENFORCE]
        )


class CspPolicyBuilderUnitTests(TestCase):
    """Direct unit coverage of build_csp_policy / resolve_mode."""

    def test_builder_contains_nonce_verbatim(self):
        policy = build_csp_policy("abc123")
        self.assertIn("'nonce-abc123'", policy)

    def test_resolve_mode_rejects_unknown_values(self):
        with override_settings(CSP_MODE="bogus"):
            with self.assertRaises(ImproperlyConfigured):
                resolve_mode()

    def test_resolve_mode_defaults_to_enforce_without_setting(self):
        from django.conf import settings

        del settings.CSP_MODE
        try:
            self.assertEqual(resolve_mode(), "enforce")
        finally:
            settings.CSP_MODE = "enforce"
