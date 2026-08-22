# BookmarkerDjango Security & Quality Roadmap — Rev 2 (Post-Critic)

> **Status:** Approved plan (critic-corrected Rev 2) · **Created:** 2026-08-22
> **Origin:** Produced by planning agent, rejected once by critic review (5 corrections), revised and re-verified against line-level code evidence.
> **Total estimate:** ~4–4.5 wk · **Phases:** P0→P4 · Manager groups: max 5 workers each

**Objective:** Remediate verified authorization/injection defects, remove the abandoned auth stack, restore frontend style-source integrity, and harden token handling — in five dispatchable phases with an explicit parallelization graph.

---

## Verified Facts Baseline (all confirmed by direct file reads)

| # | Fact | Evidence |
|---|------|----------|
| F1 | `BmListView` / `BmListSearchView` / `BmDetailView` **already enforce ownership** → regression-test subjects, NOT fix targets | views.py:490, :510, :527 |
| F2 | `AddBookmark.get()` returns `Bm.objects.all()` to any authenticated user — full cross-user bookmark dump | views.py:238 |
| F3 | `UpdateUserCategories.put()` write path is safe (:194 pins caller), but :198 queries **all users'** bookmarks → global category-existence oracle; logic also inverted (blocks categories that already have bookmarks anywhere) | views.py:198 |
| F4 | `extensionLogin` is AllowAny FBV via GET (creds in query string), interpolates email+password into inline JS with quote-strip-only sanitization (backslash & `</script>` breakouts), and `postMessage(result, '*')` leaks the JWT to any framing parent | views.py:653–681, :678; api/urls.py:19 |
| F5 | `UserList` exposes unfiltered `CustomUser.objects.all()` (serializer leaks email/is_staff/is_superuser/PK lists) and is **dead code** — no route in any of the repo's three urls.py files | views.py:135–137; api/urls.py:6–51; bookmarker/urls.py:7–14; frontend/urls.py:5–7 |
| F6 | 12 YouTube-proxy views pass raw user-supplied IDs straight into `googleapiclient`; zero view-layer validation (regexes exist only in utils/urlutils.py, applied only inside AddBookmark.post helpers). Risk = API-quota abuse, not injection | views.py:242–367, 370–453, 456–476, 560–650; utils/fetch_youtube.py:6–14 |
| F7 | `IsOwnerOrReadOnly` is attached to 13 views but **never executes** (no `check_object_permissions` call anywhere) — decorative; ownership is hand-rolled at :148, :180, :215/:221, :490, :510, :527 | api/permissions.py:4–16 |
| F8 | `rest_auth` sits in INSTALLED_APPS at settings.py:65 (`rest_framework.authtoken` at :64); repo-wide grep finds **zero** references elsewhere; requirements.txt has no rest-auth (SimpleJWT 5.5.1 is the real stack). Stray **unpinned** rest_auth 0.9.5 + django-utils-six sit in venv site-packages anyway | settings.py:51–68; requirements.txt:6–9,23 |
| F9 | Runtime Python is **3.14.7** (pyvenv.cfg's "3.13.7" is stale metadata from an unpinned `python3` symlink after a system upgrade; dual site-packages trees exist) | .venv/pyvenv.cfg:3–5 vs `.venv/bin/python --version` |
| F10 | DEBUG is correctly read via django-environ (settings.py:16–27, :41); **the stale artifact is `.env.example`** (and `.env`) — both omit `DEBUG`, so it silently falls back to False | settings.py:41; .env.example |
| F11 | `Bm.url` (models.py:46) and `Bml.url` (**models.py:77**) are both CharField(255); created in 0001, never altered since; pending drift (0007) touches only count/settings fields | api/models.py:46,:77; api/migrations/0001_initial.py:65,:83 |
| F12 | Root cause of missing style source: `.gitignore:19` excludes `frontend/src/scss/` while **nothing generates it** (no sass in devDependencies — only react-icons; CRA5 bundles sass-loader internally but it's inert without `sass`). Compiled `.css`+`.css.map` are git-tracked instead — inverted source/output tracking | .gitignore:19; frontend/package.json:40–46, 65–67 |
| F13 | **Aggravation:** only 14 of 18 scss files are tracked. `Landing.scss`, `Logout.scss`, `NotFound.scss`, `_themes.scss` exist **only on this machine** (untracked + ignored) — a clone ships CSS compiled from a `_themes.scss` it doesn't have; any `git clean` destroys them | git ls-files vs ls frontend/src/scss |
| F14 | Both access AND refresh JWTs live in `localStorage` (authReducer.js:17, :63–66; authActions.js:59–66); refresh lifetime is 90 days; SimpleJWT rotation+blacklist enabled. Bonus defects: `UserDetail` GET mutates `last_login` (:158); `AddBookmark.post` fetches arbitrary user URLs server-side → SSRF surface (:339); `BmDetailView` 500s on missing pk (:526) | settings.py:82–112; frontend/src/reducers/authReducer.js |

---

## Pre-flight — execute BEFORE anything else

- **[0.0] Rescue untracked scss source** — owner: general — parallel: yes (touches only .gitignore + 4 untracked files; zero overlap with any other lane) — deps: none — files: `.gitignore`, `frontend/src/scss/{Landing,Logout,NotFound,_themes}.scss` — risk: LOW, but skipping it risks permanent loss (F13). Action: remove/amend the `.gitignore:19` rule, `git add -f` the four files, commit. ~15 min. **This is the single most time-sensitive item in the plan.**
  > ⚠️ **PARTIALLY DONE 2026-08-22:** morning commits `7139fa6` + `6d5836b` back-ported CSS edits into the 12 tracked scss sources and committed compiled css artifacts (incl. new Landing.css/Logout.css/NotFound.css), but the four scss files remain UNTRACKED and `.gitignore:19` still blocks them. Remaining: amend ignore rule → `git add -f` the 4 files → commit → push.

---

## Phase 0 — Critical Security Remediation (recalibrated: **1–1.5 wk**)

*(Fan-out: five lanes. Lane A is a strict serial chain on `api/views.py`; Lanes B–E are fully disjoint from A and from each other.)*

### Lane A — views.py fix chain *(owner: build — SERIAL: every step writes `api/views.py`)*
- **[0.1] Fix `AddBookmark.get()` leak** — owner: build — parallel: no (Lane A chain) — deps: 0.0 — files: api/views.py — risk: MED. First grep frontend/ + any extension code for callers of the GET endpoint (R1); then either delete the handler (405) or scope to `owner_id=self.request.user.id`. Recommended: delete — evidence says debug leftover.
- **[0.2] Fix `UpdateUserCategories` oracle** — owner: build — parallel: no — deps: 0.1 — files: api/views.py — risk: MED. Scope :198 to `Bm.objects.filter(owner=request.user, category__iexact=...)`; correct the inverted block/save logic; add test proving a cross-user category no longer influences the response.
- **[0.3] Delete dead `UserList`** — owner: build — parallel: no — deps: 0.2 — files: api/views.py — risk: LOW. Confirmed unrouted (F5); removing eliminates the landmine. Verify import list in api/urls.py stays clean.
- **[0.4] Rewrite `extensionLogin` GET→POST** — owner: build — parallel: no — deps: 0.3 — files: api/views.py, api/urls.py — risk: HIGH (external consumer — see R7). Contract: POST + JSON body only (GET → 405); **zero credential interpolation into any template** (return plain JSON; let the client perform its own fetch); pin `postMessage` targetOrigin to the extension's origin (or drop postMessage entirely); kills the query-string-credential leak, both injection vectors, and the `'*'` token leak (F4). **Explicit + tested:** tests assert (a) no email/password substrings appear in any response body, (b) GET is rejected, (c) postMessage origin is pinned.
- **[0.5] `BmDetailView` missing-pk 500 → 404** — owner: build — parallel: no — deps: 0.4 — files: api/views.py — risk: LOW (:526 `.first()` → None deref).

### Lane B — regression suite for surviving enforcement *(owner: build #2 — parallel: YES — writes only new files under `api/tests/`; disjoint from Lane A)*
- **[0.6] Ownership regression tests** — deps: none — files: api/tests/test_ownership.py — risk: LOW. Lock in current-correct behavior at :490, :510, :527, plus hand-rolled checks at :148 (UserDetail) and :215/:221 (OptionsView). Target behavior, not line numbers (Lane A shifts lines). Explicitly do NOT credit `IsOwnerOrReadOnly` (F7) — assert the manual filters.

### Lane C — auth-stack removal *(owner: general — parallel: YES — touches settings.py/venv only)*
- **[0.7] Remove `rest_auth` + `rest_framework.authtoken` from INSTALLED_APPS** — deps: none — files: bookmarker/settings.py:64–65 — risk: MED. **INVERTED remediation per critic: do NOT add anything to requirements.txt** (F8: zero references outside settings.py; abandoned upstream, incompatible with Django 6). Additionally purge the stray unpinned venv installs (`pip uninstall rest_auth django_rest_auth django-utils-six`) and inventory `django-extensions` 4.1 (also ad-hoc/unpinned — pin in requirements.txt if actually used, else remove). Verify with `manage.py check` + boot smoke test.

### Lane D — model/migration batch *(owner: general — parallel: YES — touches models.py + new migration only)*
- **[0.8] Lengthen `Bm.url` AND `Bml.url`** — deps: none — files: api/models.py:46 & :77, new migration 0007/0008 — risk: MED (prod data — R2). Both fields in ONE migration batch (critic item 4c). Recommend `URLField(max_length=2048)` or `TextField`. Fold in the already-pending 0007 drift (count/settings fields) so migration state ends clean. Run on a DB copy first; backup before apply.

### Lane E — config hygiene *(owner: general — parallel: YES — touches .env.example only)*
- **[0.9] Refresh `.env.example`** — deps: none — files: .env.example — risk: LOW. **Precise phrasing per critic: the example file is stale; settings.py is correct** (reads DEBUG via django-environ, F10). Do NOT touch settings.py. Add `DEBUG=True` (with a "never in prod" comment), document every key settings.py actually reads, add a warning that `.env` currently holds live secrets and must stay out of VCS.

### Analysis lane *(runs concurrently, read-only)*
- **[0.10] Full queryset/authz audit of all ~21 CBVs + 4 FBVs** — owner: plan — parallel: YES (read-only) — deps: none — files: none (spec output to `docs/plans/p1-audit-spec.md`) — risk: LOW. Deliverable: per-view verdict (safe / fix / throttle / validate) covering the 12 YouTube-proxy views (F6): ID-format regex (reuse utils/urlutils.py patterns), DRF throttle classes for quota abuse, disposition for the SSRF surface (:339) and `last_login` side effect (:158). Feeds Phase 1 directly.

**Manager batching:** MG-1 = {Lane A, Lane B, Lane C} · MG-2 = {Lane D, Lane E, audit 0.10}. Pre-flight 0.0 precedes all batches.

---

## Phase 1 — Attack-Surface Hardening (~1 wk) *(serial on views.py/utils.py unless noted)*

- **[1.1] Proxy-view validation + throttling** — owner: build — parallel: no (writes api/views.py + settings.py throttle config) — deps: 0.10 spec, Phase 0 Lane A complete — files: api/views.py, utils/, bookmarker/settings.py — risk: MED (R8). Apply ID regex to all 12 proxy views; DRF scoped throttles (e.g., per-user burst on comments/replies/search endpoints).
- **[1.2] SSRF guard for `scrape_page_metadata`** — owner: build — parallel: no (same files as 1.1) — deps: 1.1 — files: utils/, api/views.py — risk: MED. Scheme allowlist (http/https), resolve-and-block private/link-local IPs, response-size cap.
- **[1.3] `UserDetail` last_login side-effect** — owner: general — parallel: no (views.py overlap) — deps: 1.2 — files: api/views.py:158 — risk: LOW.
- **[1.4] Resolve decorative `IsOwnerOrReadOnly`** — owner: build — parallel: no — deps: 1.3 — files: api/permissions.py, api/views.py — risk: MED. Either wire `check_object_permissions` into detail paths or delete the class; per 0.10 verdict. Never leave it attached-but-inert (false security).

---

## Phase 2 — Token Handling & CSP — **CSP is an EXPLICIT deliverable** (~1 wk)

- **[2.1] CSP rollout** — owner: build — parallel: YES vs 2.3 (disjoint files) — deps: Phase 1 — files: bookmarker/settings.py, new middleware, templates — risk: MED (R6). Staged: `Content-Security-Policy-Report-Only` → tune → enforce. Directives: `frame-ancestors 'none'` (kills the extensionLogin framing vector permanently), `script-src 'self' 'nonce-…'` (no unsafe-inline), `object-src 'none'`. **Role: compensating control for JWT-in-localStorage (F14)** — stated explicitly in the deliverable, not implicit.
- **[2.2] Token-storage decision gate** — owner: plan (decision doc) → build (implementation) — parallel: no with 2.1 implementation — deps: 2.1 report-only results — files: frontend/src/reducers/authReducer.js, frontend/src/actions/authActions.js, backend cookie endpoints — risk: HIGH scope. Options: (a) move refresh token to httpOnly SameSite cookie, keep short-lived access in memory/localStorage; (b) accept documented residual risk behind enforced CSP. **Recommendation: (a)** — 90-day refresh in localStorage is the dominant exposure. If deferred, record the accepted-risk memo.
- **[2.3] Tighten `REFRESH_TOKEN_LIFETIME` 90d → 14d** — owner: general — parallel: YES vs 2.1 — deps: none beyond Phase 0 — files: bookmarker/settings.py:82–112 — risk: LOW (users re-login biweekly; rotation+blacklist already on).

---

## Phase 3 — Frontend Style-Source Integrity (~0.5 wk) *(root cause explicit per critic item 5)*

**Root cause statement:** `.gitignore:19` excludes `frontend/src/scss/` while NOTHING generates it — there is no `sass` in devDependencies (only react-icons; CRA5's bundled sass-loader is inert without it) — so cloned checkouts ship without style source, only stale compiled CSS (F12/F13).

- **[3.1]** *partially completed 2026-08-22* — tracked-source back-port done (`7139fa6`); 4-file rescue still open (see Pre-flight).
- **[3.2] Toolchain decision** — owner: designer (direction) → build (implementation) — parallel: n/a (single lane) — deps: 0.0 — files: frontend/package.json, ~22 component imports, .gitignore — risk: MED.
  - **Option A (minimal):** commit scss as canonical source, keep committed CSS as refreshed artifacts. No dependency change.
  - **Option B (recommended):** add `sass` devDependency (this alone activates CRA5's bundled sass-loader ^12.3.0), change ~22 `import './css/X.css'` → `import './scss/X.scss'`, stop committing generated css/css.map. Single source of truth, no drift.
- **[3.3] Dead-artifact cleanup** — owner: general — parallel: YES vs 3.2 implementation — deps: 3.2 decision — files: frontend/package.json (`serve` script references nonexistent `src/index.html`), vestigial webpack.config.js, stale .css.map files — risk: LOW.

---

## Phase 4 — Verification & Critic Gate (~0.5 wk)

- **[4.1] Full test suite + coverage report** — owner: build — parallel: no — deps: Phases 0–3 — files: (all tests) — risk: LOW. Gate: zero failures; new suites present for every P0 fix.
- **[4.2] Critic review of entire changeset** — owner: critic — parallel: no — deps: 4.1 — binary APPROVED/REJECTED.
- **[4.3] Vision browser pass** — owner: vision — parallel: YES with 4.2 — deps: 4.1 — **REQUIRED (UI touched: scss pipeline, CSP, extensionLogin rewrite)**. Verify via agent-browser: styled pages render identically post-scss-change; login + rewritten extension-login POST flow works; CSP headers present and no console violations; no credentials in any URL/response.

---

## First Sprint (Week 1 of P0) — concrete dispatch

| Day | Work |
|---|---|
| 1 AM | **0.0 scss rescue (blocking, 15 min)** → commit. Then MG-1/MG-2 launch: Lanes A–E + audit 0.10 all start. |
| 1 PM–2 | Lane A: 0.1, 0.2. Lane B: regression suite drafted. Lane C: rest_auth removal + venv purge + smoke test. |
| 3 | Lane A: 0.3, 0.4 (extensionLogin rewrite — coordinate with extension consumer, R7). Lane D: migration authored, rehearsed on DB copy. |
| 4 | Lane A: 0.4 tests, 0.5. Lane E: .env.example. Audit 0.10 spec circulated. |
| 5 | Integration: full suite green, `manage.py check`, migration applied to staging, sprint demo. Buffer absorbs slip into early Week 2 (hence 1–1.5 wk band). |

---

## Acceptance Criteria

- **P0:** regression suite green (:490/:510/:527/:148/:215 behaviors locked); GET add-bookmark rejected or owner-scoped (tested); cross-user category provably cannot influence `UpdateUserCategories` responses; `UserList` absent from codebase and all urlconfs; extensionLogin: POST-only, zero credential substrings in responses (asserted by test), postMessage origin pinned; INSTALLED_APPS free of rest_auth/authtoken, app boots clean; single migration alters both url fields and applies on a prod-data copy; `.env.example` documents DEBUG while settings.py untouched.
- **P1:** all 12 proxy views enforce ID format + return 429 under burst; SSRF guard blocks private-range targets (unit-tested); GET `/users/<pk>` no longer mutates last_login; IsOwnerOrReadOnly either enforced or deleted.
- **P2:** CSP enforced with zero violations on core flows; token-storage decision recorded (implemented or accepted-risk memo); refresh lifetime ≤ 14d.
- **P3:** fresh clone renders fully styled app; `git status` clean after clone+build; no committed generated-CSS drift (Option B) or documented refresh procedure (Option A).
- **P4:** critic APPROVED; vision pass artifacts archived.

---

## Risks

| # | Risk | L×I | Mitigation |
|---|---|---|---|
| R1 | Unknown consumer of `AddBookmark.get` breaks | M×M | Grep frontend + extension before deletion; owner-scoped fallback if a caller exists |
| R2 | url-field migration on prod data | M×H | Backup; rehearse on DB copy; batch both fields in one reviewed migration |
| R3 | Hidden rest_auth import surfaces after removal | L×M | Repo-wide grep already clean (F8); `manage.py check` + boot gate |
| R4 | Venv recreation loses ad-hoc packages | M×L | Inventory first (django-extensions!), pin what's used; pin Python 3.14.7 explicitly (F9) |
| R5 | Untracked scss lost before rescue | L×H | **0.0 executes first, before any other command** |
| R6 | CSP breaks MUI/Emotion injected styles or inline scripts | M×M | Report-only phase; nonce strategy; per-directive tuning |
| R7 | Browser extension breaks on extensionLogin rewrite | M×H | Locate extension consumer first; versioned endpoint or compat window |
| R8 | Throttling degrades legitimate UX | M×L | Conservative rates; monitor 429s; per-endpoint scopes |
| R9 | Python 3.14.7 edge-case incompatibilities | L×M | Pin interpreter at venv recreation; CI runs on same version |

---

## Open Decisions (recommendations embedded; flag disagreement before dispatch)

1. `AddBookmark.get` → **delete** (vs owner-scope) — default delete unless R1 grep finds a caller.
2. scss → **Option B** (sass toolchain) over Option A.
3. Refresh-token httpOnly migration → **in scope for P2**; deferral requires an explicit accepted-risk memo.

---

## Progress Log

- **2026-08-22:** Plan created (Rev 1) → critic REJECTED (5 corrections) → Rev 2 produced incorporating all corrections. Saved to `docs/plans/bookmarker-security-roadmap-rev2.md`.
- **2026-08-22:** Pre-flight [0.0] PARTIALLY executed by user (commits `7139fa6`, `6d5836b`): tracked-scss back-port done; compiled-css artifacts committed; **remaining:** 4 untracked scss files + `.gitignore:19`.
