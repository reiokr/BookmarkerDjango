# P2 Decision Memo — Refresh-Token Storage Migration

> **Roadmap:** docs/plans/bookmarker-security-roadmap-rev2.md · Step [2.2] (Token-storage decision gate) + [2.1] CSP notes
> **Date:** 2026-08-22 · **Status:** Implemented (option a) · **Baseline:** master @ 014a9c0

---

## 1. Decision

**Option (a) chosen** — move the refresh JWT out of `localStorage` into an
HttpOnly SameSite=Lax cookie; keep the short-lived access token client-side
exactly as today. This follows the plan's explicit recommendation ("90-day
refresh in localStorage is the dominant exposure") and Open Decision #3.
Option (b) (accepted-risk memo only) was not taken because the migration was
achievable without breaking any in-repo consumer.

## 2. What moved where

| Item | Before | After |
|---|---|---|
| Refresh token (web flow) | JSON body of `/api/login/` → persisted whole under localStorage key `token` | **HttpOnly cookie** `refresh_token`; body carries access only |
| Cookie flags | — | `HttpOnly; SameSite=Lax; Path=/api/login/; Secure` unless `DEBUG`; `Max-Age` = `REFRESH_TOKEN_LIFETIME` (14 d, step [2.3]) |
| Cookie path scope | — | `/api/login/` — spans **both** consumers: `/api/login/refresh/` and `/api/login/logout/`. Logout must READ the cookie to blacklist the token before deleting it, so the path cannot be narrower than the consumer set. Nothing else ever receives it. |
| Access token | localStorage key `token` (payload `.access`) | unchanged |
| Rotation/blacklist | on | on — every successful refresh blacklists the presented token and **replaces** the cookie |

Backend pieces: `api/auth_cookies.py` (cookie contract + origin check),
`MyObtainTokenPairView.post` (pop `refresh`, set cookie),
`CookieTokenRefreshView` (cookie-only refresh; body tokens rejected 400;
missing cookie 401), `LogoutView` at `/api/login/logout/` (blacklist +
clear). Routes: `api/urls.py`.

Frontend pieces: `frontend/src/index.js` sets `axios.defaults.withCredentials
= true` once, centrally (the shared client); `authActions.js` loadUser no
longer reads or persists any refresh token — it POSTs an empty body to
`/api/login/refresh/` and stores only the returned access token; logout calls
the backend logout endpoint fire-and-forget; `authReducer.js` purges any
legacy stored payload that still contains a `refresh` key on first load
(migration hygiene).

### Deliberate non-change: `/api/extension-login/`

The browser-extension endpoint (rewritten by step [0.4], contract v2) still
returns `refresh` in its JSON body and is pinned by P0 tests
(`test_extension_login.py`). It has no cookie semantics: the extension owns
its own storage across origins where cookies would not be shared anyway.
Changing it again would re-trigger risk R7 for an external consumer for zero
in-browser gain. Recorded here as an accepted exception to "no refresh in
response bodies".

## 3. CSRF analysis outcome

Threat: a malicious site makes the victim's browser POST to the
cookie-consuming endpoints (`/api/login/refresh/`, `/api/login/logout/`).

1. **SameSite=Lax (primary control):** modern browsers do not attach a Lax
   cookie to cross-site POSTs at all, so the attacker's request arrives
   credential-less. This alone defeats the vector in all evergreen browsers.
2. **Origin allowlist (defense-in-depth, implemented):** both cookie-consuming
   POSTs reject requests whose `Origin` header names an origin outside
   `{FRONTEND_URL, BACKEND_URL}` (403). Requests without an `Origin` header
   (curl, server-to-server) are allowed — non-browser clients cannot be
   CSRFed. Impact even if both controls failed: forced rotation (harmless —
   old token blacklisted) or forced logout (nuisance).
3. **Full Django CSRF-token wiring — evaluated, NOT implemented.** It would
   require the SPA to obtain a `csrftoken` cookie and echo `X-CSRFToken` on
   every refresh/logout, plus handling for stale-token 403 loops after long
   sessions. Clean to describe, but it adds cross-cutting failure modes for a
   marginal gain over controls 1+2. Accepted tradeoff, recorded here per the
   task instruction ("implement if clean, else document").

Dev topology note: in development the CRA dev server proxies `/api/*`
(`"proxy": "http://127.0.0.1:8000/"`), so browser→API traffic is same-origin
and cookies flow without CORS involvement; `withCredentials` additionally
covers cross-origin deployments.

## 4. Residual risks

* **XSS can still use the in-memory/localStorage ACCESS token until it
  expires (≤ 24 h).** Moving the refresh token caps the blast radius from
  *14–90 days of silent session renewal* to *one access-token lifetime*, but
  does not eliminate client-side token theft. **Compensating control: the
  enforced CSP (step [2.1])** — `script-src 'self' 'nonce-…'` with no
  `unsafe-inline`, `connect-src 'self'`, `frame-ancestors 'none'`,
  `object-src 'none'` — bounds what injected script may run, load, or talk
  to (plan F14).
* **style-src retains `'unsafe-inline'`** (documented deviation, risk R6):
  MUI/Emotion inject runtime `<style>` tags; blocking them breaks all
  component styling. Style injection is not a script-execution vector.
* **img-src allows `https:`** — bookmark preview images come from arbitrary
  scraped `og:image` hosts (core feature); pixel-beacon tracking remains
  theoretically possible within that allowance.
* **CSP currently covers Django-served responses only.** Verified during
  rollout: the built SPA (`frontend/build/index.html`) is NOT served through
  Django today — `frontend/views.py::index` returns JSON and dev traffic runs
  on the CRA server (:3000). When the build is ever served via Django
  templates, headers are already correct; until then the production host of
  the static bundle must mirror the policy.
* **Cookie replay before first rotation:** a stolen cookie works until its
  next legitimate refresh blacklists it (same window as the old localStorage
  threat, but the token is now unreadable to JS).

## 5. Rollback plan

Single revert of the P2 changeset restores the previous behavior end-to-end:
routes point back at the body-token `ThrottledTokenRefreshView`, login bodies
carry `refresh` again, and the frontend resumes reading/persisting it
(`authReducer.js` legacy-purge is additive and harmless against old data).
No migrations, no data backfills, no external-consumer coordination needed —
the extension contract never changed. Stale `refresh_token` cookies left in
browsers simply expire (Max-Age ≤ 14 d) or are cleared by the next logout.

## 6. Verification summary

* Backend suite: `python manage.py test` green (see gate output; baseline 114,
  new suites `test_csp.py` +14, `test_token_cookie.py` +16).
* Cookie flags asserted exactly (HttpOnly, SameSite=Lax, Path, Secure under
  DEBUG=False, absent under DEBUG=True, Max-Age = 14 d).
* Round-trip: login → cookie refresh → rotated cookie; pre-rotation replay →
  401; body token → 400; missing cookie → 401; logout clears cookie and
  blacklists.
* Login response body contains no `refresh` substring (asserted).
* Frontend grep proof: no refresh-token write to localStorage remains in
  `frontend/src`.
