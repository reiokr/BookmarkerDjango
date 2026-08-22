# P1 Audit Spec — Full Queryset/Authz Audit of api/views.py (Lane [0.10])

> **Status:** Final · **Produced:** 2026-08-22 · **Feeds:** Phase 1 steps [1.1]–[1.4]
> **Source plan:** docs/plans/bookmarker-security-roadmap-rev2.md (Verified Facts F1–F14)
> **Scope:** READ-ONLY audit of every view in `api/views.py` (21 CBVs + 4 FBVs = 25 total), plus `api/permissions.py`, `utils/urlutils.py`, `utils/fetch_youtube.py`, `utils/fetch_channel.py`, `utils/fetch_video_comments.py`, `utils/find_playlist.py`, `utils/rate_video.py`, `utils/scraper/`, `api/serializers.py`, `api/models.py`, `api/urls.py`, `bookmarker/settings.py`.
> **Line-anchor policy:** verdicts are anchored to VIEW NAMES first (Lane A is concurrently editing views.py); current-rev line numbers are secondary.

---

## 1. Executive Summary

- **25 views audited** (21 CBVs + 4 FBVs). Primary-verdict distribution: **6 safe / 7 fix / 2 throttle / 10 validate** (secondary tags tracked separately in §3).
- **🚨 NEW CRITICAL FINDING (not in F1–F14): `UserDetail.put` is a self-service privilege-escalation vector.** `UserSerializer` (serializers.py:41–42) exposes `is_staff`, `is_active`, `is_superuser` as **writable** fields (no `read_only` kwargs; DRF renders editable model booleans as writable), and `UserDetail.put` (views.py:162–168) feeds `request.data` straight in. `PUT /api/users/<own-pk>` with `{"is_superuser": true}` promotes the caller to superuser. Target is self-only (get_object pins pk at :148), but that is full privilege escalation. **Recommend escalating into Phase 0 Lane A as step [0.6]** (it is a views.py edit; Lane A owns that file serially). Blast radius contained: no in-repo frontend caller sends privileged fields (`updateUserData` is exported at authActions.js:187/:231 with **zero callers**); browser-extension consumption unknown (same caveat class as R7).
- **F6 confirmed:** exactly 12 YouTube-proxy views pass raw user-supplied IDs into `googleapiclient`. §4 maps each to an existing `utils/urlutils.py` pattern; only 3 ID types have zero existing coverage (channelId, comment parentId, page tokens) and need three narrowly-scoped constants added to the *same module* using its existing charset convention.
- **F14/SSRF confirmed and worse than noted:** `scrape_page_metadata` (utils/scraper/__init__.py:11–33) does `requests.get(url)` with **no scheme check, no timeout, no size cap, redirects followed by default**, reachable by any authenticated user via `AddBookmark.post` (views.py:339). Disposition: **fix now** ([1.2]). Concrete guard in §5.
- **F14/last_login confirmed and trivially fixable:** views.py:158 mutates the in-memory instance **without ever calling `.save()`** — the DB is never written; only the serialized response lies. Delete the line. Nothing depends on it (§6).
- **F7 confirmed but undercounted:** `IsOwnerOrReadOnly` is attached to **15** views (roadmap said 13) and executes nowhere (repo-wide grep: zero `check_object_permissions` calls). Worse: naively wiring it would **500** on 14 of the 15 (objects are `CustomUser` instances, raw API dicts/lists — none have `.owner`). Per-view dispositions in §7: wire it in exactly **one** place (`BmDetailView`), strip the other 14 attachments.
- **Bonus findings for Phase 1:** `RateVideoView` can only ever 500 (broken OAuth util + global `OAUTHLIB_INSECURE_TRANSPORT=1` side effect, §8.1); `YouTubeList` has an unbounded server-side pagination loop (quota amplification, §8.2); login/register endpoints have **zero** anonymous throttling today (§4.3); several guaranteed-500 error paths in `AddBookmark.post` (§8.3).

---

## 2. Methodology

1. Read `api/views.py` in full (681 lines) and built the complete inventory with permission classes, queryset/filtering, authz mechanism, side effects, and external calls per view.
2. Traced every external-call surface: `googleapiclient` entry points in all five util modules; `requests.get` in `utils/scraper/__init__.py`; SMTP in `RegisterView`.
3. Cross-checked routing in `api/urls.py` (all 25 routes; param converters are `<str:…>` for every proxy ID — i.e., **Django URL routing performs no format constraint whatsoever**) and `bookmarker/urls.py`.
4. Verified F1–F14 claims against source; corrected two counts (IOOR attachments 15 ≠ 13; see §7).
5. Grepped repo-wide for `check_object_permissions` (zero hits — F7 holds), `last_login` (views.py:158 sole mutation site; admin.py display-only; serializer read-only exposure; **zero frontend references**), and frontend consumers of `/api/users/<pk>` PUT (none in-repo).
6. Confirmed DRF baseline: `REST_FRAMEWORK` (settings.py:67–76) defines **no throttle classes and no rates** — the deployment ships with throttling fully disabled; `DEFAULT_PERMISSION_CLASSES = IsAuthenticated` (so undecorated `@api_view` FBVs inherit auth; plain-Django FBVs bypass DRF entirely).

---

## 3. Per-View Verdict Table

Verdict vocabulary: **safe** · **fix** · **throttle** · **validate**. A view may carry a primary verdict plus secondary tags (shown in parentheses). "IOOR" = inert `IsOwnerOrReadOnly` attachment (see §7).

| # | View (kind) | Route | Lines† | Permissions | Primary verdict | Notes |
|---|---|---|---|---|---|---|
| 1 | `getRoutes` (FBV) | `api/` | :57–60 | inherited IsAuthenticated | **safe** | Undecorated `@api_view` inherits default perms — document, don't change. |
| 2 | `getCurrentUser` (FBV) | `api/user/me` | :63–67 | IsAuthenticated | **safe** | Self-serialization only. |
| 3 | `MyObtainTokenPairView` (CBV) | `api/login/` | :70–72 | AllowAny | **throttle** (+fix-P2 note) | No anon throttle today → credential stuffing. Add `login` scope (§4.3). Serializer `validate()` returns success-shaped dicts for unknown/inactive emails → enumeration oracle (serializers.py:59–68) — P2 candidate, cross-ref only. |
| 4 | `RegisterView` (CBV) | `api/register/` | :75–116 | AllowAny | **throttle** | Add `register` scope (§4.3). Sync activation email in-request (latency, not security). `UniqueValidator` email enumeration = accepted tradeoff, note only. |
| 5 | `activate` (FBV, plain Django) | `api/activate/<uidb64>/<token>/` | :119–132 | none (token-gated) | **safe** | Outside DRF by design; single-use token check correct. |
| 6 | `UserList` (CBV) | *(unrouted)* | :135–137 | inherited IsAuthenticated | **fix** | Dead code, F5 — Lane A [0.3] deletes it. Cross-ref only. |
| 7 | `UserDetail` (CBV) | `api/users/<int:pk>` | :140–173 | IsAuthenticated | **fix** 🔴 | **(a) CRITICAL priv-esc via `put`** — writable `is_staff/is_active/is_superuser` (serializers.py:41–42) bound from `request.data` (:164). Escalate to Lane A [0.6]; remediation §8.4. **(b)** Phantom `last_login` mutation :158 — remove line (§6). Ownership hand-roll :148–154 correct (F1 subject). Nested `options` key on PUT → DRF nested-writable `AssertionError` → 500 (fold into serializer lockdown). |
| 8 | `UpdateUserCategories` (CBV) | `api/user/categories/<int:pk>` | :176–205 | IsAuth + IOOR | **fix** | Global category oracle + inverted logic :198 — Lane A [0.2]. Strip IOOR attachment (§7). |
| 9 | `OptionsView` (CBV) | `api/user/options` | :208–231 | IsAuth + IOOR | **safe** | Hand-rolled owner scoping :215/:221 correct (F1 subject). Strip IOOR (§7). Note: `settings` JSONField stored free-form — frontend rendering sink, out of backend scope. |
| 10 | `AddBookmark` (CBV) | `api/bm` | :234–367 | IsAuth + IOOR | **fix** (+validate, +throttle) | GET leak F2 → Lane A [0.1]. POST: SSRF :339 → [1.2]/§5; ID extraction already uses urlutils helpers but extracted values go to googleapiclient **unvalidated** → post-extraction asserts (§4.1); multi-call amplification via `findPlaylistId` walk → `bm_create` throttle; error-path 500s (§8.3). Strip IOOR (§7). |
| 11 | `YouTubeList` (CBV) | `api/bm/list/<str:list_id>` | :370–411 | IsAuth + IOOR | **validate** (+throttle, +fix-lite) | Raw `list_id` → `playlistItems().list`. Validate (§4.1). **Unbounded pagination loop :381–390** — cap pages (§8.2). Throttle `youtube_list`. Strip IOOR. |
| 12 | `VideoCommentsView` (CBV) | `api/bm/comments/<str:video_id>/<str:order>` | :414–427 | IsAuth + IOOR | **validate** (+throttle) | Raw `video_id`; **`order` is an API enum** (`time`/`relevance`) passed through verbatim — validate both (§4.1). Throttle `youtube_proxy`. Strip IOOR. |
| 13 | `RepliesView` (CBV) | `api/bm/comment/replies/<str:parent_id>` | :430–439 | IsAuth + IOOR | **validate** (+throttle) | Raw comment `parent_id` → `comments().list(parentId=…)`. COMMENT_ID_RE (§4.1). Throttle `youtube_proxy`. Strip IOOR. |
| 14 | `RepliesNextPageView` (CBV) | `api/bm/comment/nextreplies/<str:parent_id>/<str:page_token>` | :442–453 | IsAuth + IOOR | **validate** (+throttle) | parent_id + opaque page_token. PAGE_TOKEN_RE (§4.1). Throttle `youtube_proxy`. Strip IOOR. |
| 15 | `NextPageCommentsView` (CBV) | `api/bm/comments/<str:video_id>/<str:page_token>/<str:order>` | :456–468 | IsAuth + IOOR | **validate** (+throttle) | video_id + page_token + order enum. Throttle `youtube_proxy`. Strip IOOR. |
| 16 | `RateVideoView` (CBV) | `api/bm/rate/<str:video_id>` | :471–476 | IsAuth + IOOR | **fix** (+validate) | Guaranteed 500: `rate_video()` reads placeholder secrets file and calls removed `run_console()` (§8.1). Default disposition: remove route+view+util pending product decision. Strip IOOR. |
| 17 | `BmListView` (CBV) | `api/bm/category/<category>` | :479–496 | IsAuthenticated | **safe** | Owner-scoped :490 ✓ (F1 regression subject). Class-level `queryset` attr shadowed by `get_queryset` — harmless. `perform_create` pins owner ✓. |
| 18 | `BmListSearchView` (CBV) | `api/bm/category/<category>/<search>` | :499–519 | IsAuthenticated | **safe** | Owner-scoped :509–510 ✓ (F1 subject). Dead branch :506–507 assigns unused `user` — cosmetic cleanup only. |
| 19 | `BmDetailView` (CBV) | `api/bm/<int:pk>` | :522–557 | IsAuth + IOOR | **fix** | Missing-pk 500 :526 → Lane A [0.5]. **The one view where IOOR should be WIRED** — canonical `get_object_or_404` + `check_object_permissions` replaces the hand-roll and kills the None-deref bug class (§7.2). PUT `request.data["video_data"]` KeyError → 500 (fold into [0.5] neighborhood). |
| 20 | `GetVideoData` (CBV) | `api/bm/video/<str:video_id>` | :560–608 | IsAuth + IOOR | **validate** (+throttle) | Raw `video_id` → `videos().list`. VIDEO_ID_RE (§4.1). Throttle `youtube_proxy`. Strip IOOR. Hardcoded `"category": "default"` — cosmetic. |
| 21 | `ChannelPlaylistsView` (CBV) | `api/channel/playlists/<str:channel_id>` | :611–619 | IsAuth + IOOR | **validate** (+throttle) | Raw `channel_id` → `playlists().list(channelId=…)`. CHANNEL_ID_RE (§4.1). Throttle `youtube_proxy`. Strip IOOR. |
| 22 | `ChannelNextPlaylistsView` (CBV) | `api/channel/next-playlists/<str:channel_id>/<str:token>` | :622–628 | IsAuth + IOOR | **validate** (+throttle) | channel_id + page token. Throttle `youtube_proxy`. Strip IOOR. |
| 23 | `AddPlaylistTOBookmarksView` (CBV) | `api/add-playlist-to-bookmarks/<str:pl_id>` | :631–639 | IsAuth + IOOR | **validate** (+throttle) | Raw `pl_id` → `playlistItems().list(playlistId=…)`. PLAYLIST_ID_RE (§4.1). Throttle `youtube_proxy`. Strip IOOR. |
| 24 | `LoadRelatedVideosView` (CBV) | `api/video/<str:video_id>/related-videos` | :642–650 | IsAuth + IOOR | **validate** (+throttle) | Raw `video_id` → `search().list(relatedToVideoId=…)` — **search.list costs 100 quota units vs 1 for everything else** → tightest scope `youtube_search` (§4.3). Strip IOOR. |
| 25 | `extensionLogin` (FBV, plain Django) | `api/extension-login/` | :653–681 | none (bypasses DRF) | **fix** | F4 — Lane A [0.4] rewrite. Cross-ref only. Note: plain-Django FBV is invisible to DRF throttles; if kept during compat window, guard with `django-ratelimit` or return 410 early. |

† Line numbers are current-rev anchors; Lane A drifts them. Names govern.

**Distribution (primary):** safe 6 (#1,2,5,9,17,18) · fix 7 (#6,7,8,10,16,19,25) · throttle 2 (#3,4) · validate 10 (#11,12,13,14,15,20,21,22,23,24).

---

## 4. Deep-Dive A — The 12 YouTube-Proxy Views (F6)

**The 12 views:** `AddBookmark.post`, `YouTubeList`, `VideoCommentsView`, `RepliesView`, `RepliesNextPageView`, `NextPageCommentsView`, `RateVideoView`, `GetVideoData`, `ChannelPlaylistsView`, `ChannelNextPlaylistsView`, `AddPlaylistTOBookmarksView`, `LoadRelatedVideosView`.

**Risk model (per F6):** not injection — `googleapiclient` parameterizes correctly. The risks are (i) **quota abuse** (any authenticated user can burn the project-wide 10,000 units/day default), (ii) garbage IDs producing 500s (`googleapiclient.errors.HttpError` uncaught in every util), (iii) log noise. Every route uses `<str:…>` converters, so Django applies **zero** format constraints today.

### 4.1 ID-validation mapping — REUSE `utils/urlutils.py` first

Existing assets (cite these, do not duplicate):

| Existing helper | Location | Captures | Reuse as |
|---|---|---|---|
| `extractVideoId(url)` | urlutils.py:11–17 (pattern :12) | video id from any YouTube URL shape | Already used in `AddBookmark.post` :248 — **keep**; add post-extraction assert below |
| `extractPlaylistId(url)` | urlutils.py:32–38 (pattern :33) | `([a-zA-Z0-9\-_]+)` after `list=` | Already used in `AddBookmark.post` :281 — **keep**; add post-extraction assert below |
| `checkUrlType(url)` | urlutils.py:20–29 | yt-vs-bm host gate | Already used :246 — keep |

Post-extraction asserts (anchored to the **character classes those existing patterns already accept**, so no new convention is introduced):

```python
# utils/urlutils.py — validators wrapping EXISTING charsets
VIDEO_ID_RE    = re.compile(r"^[A-Za-z0-9_\-]{11}$")        # capture domain of :12 group 1
PLAYLIST_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{12,64}$")     # anchored :33 group 2, length-capped
```

Coverage gaps — three ID types have **zero** existing coverage anywhere in `urlutils.py`. Add exactly three constants to the same module, same charset convention (this is gap-filling in the designated module, not inventing parallel patterns):

```python
CHANNEL_ID_RE  = re.compile(r"^UC[A-Za-z0-9_\-]{22}$")      # YouTube channel-id canonical form
COMMENT_ID_RE  = re.compile(r"^[A-Za-z0-9_\-]{10,100}$")    # comments().list(parentId=…) — opaque
PAGE_TOKEN_RE  = re.compile(r"^[A-Za-z0-9_=\-]{1,512}$")    # opaque Google continuation tokens
```

Per-view wiring:

| View | Param(s) | Validator(s) | Feeds |
|---|---|---|---|
| `AddBookmark.post` | extracted `video_id`, `list_id` | `VIDEO_ID_RE` / `PLAYLIST_ID_RE` **after** existing `extractVideoId`/`extractPlaylistId` (:248/:281); reject request with 400 if truthy-but-nonconforming | `fetch_Video(id=)`, `get_playlist_items(playlistId=)` |
| `YouTubeList` | path `list_id` | `PLAYLIST_ID_RE` | `get_playlist_items(playlistId=)` |
| `GetVideoData` | path `video_id` | `VIDEO_ID_RE` | `fetch_Video(id=)` |
| `VideoCommentsView` | `video_id`, `order` | `VIDEO_ID_RE`; `order in {"time","relevance"}` else 400 | `commentThreads().list(videoId=, order=)` |
| `NextPageCommentsView` | `video_id`, `page_token`, `order` | `VIDEO_ID_RE`, `PAGE_TOKEN_RE`, order enum | `commentThreads().list(..., pageToken=)` |
| `RepliesView` | `parent_id` | `COMMENT_ID_RE` | `comments().list(parentId=)` |
| `RepliesNextPageView` | `parent_id`, `page_token` | `COMMENT_ID_RE`, `PAGE_TOKEN_RE` | `comments().list(parentId=, pageToken=)` |
| `RateVideoView` | `video_id` | `VIDEO_ID_RE` | `videos().rate(id=)` (view itself broken — §8.1) |
| `ChannelPlaylistsView` | `channel_id` | `CHANNEL_ID_RE` | `playlists().list(channelId=)` |
| `ChannelNextPlaylistsView` | `channel_id`, `token` | `CHANNEL_ID_RE`, `PAGE_TOKEN_RE` | `playlists().list(channelId=, pageToken=)` |
| `AddPlaylistTOBookmarksView` | `pl_id` | `PLAYLIST_ID_RE` | `get_playlist_item(playlistId=)` |
| `LoadRelatedVideosView` | `video_id` | `VIDEO_ID_RE` | `search().list(relatedToVideoId=)` |

Implementation shape: one tiny mixin or helper `def _reject_bad_id(value, regex): … raise ValidationError(400)` applied at the top of each handler. Non-conforming input returns **400** (client error), never reaches googleapiclient.

### 4.2 Why these bounds (quota math)

Default YouTube Data API quota = **10,000 units/day/project**. Costs: `videos.list`, `playlistItems.list`, `commentThreads.list`, `comments.list`, `playlists.list` ≈ **1 unit**; `search.list` = **100 units**. Unvalidated, a single authenticated user can sustain enough calls to exhaust the shared daily quota in minutes-to-hours, taking bookmarking down for everyone. Validation stops garbage (which still costs a failed-call round trip and produces 500s); throttling stops volume.

### 4.3 Exact throttle recommendation

Current state: `REST_FRAMEWORK` (settings.py:67–76) has **no throttling at all**. Placement: per-view `throttle_classes`/`throttle_scope` (NOT global defaults — keeps R8 blast radius small and makes each rate reviewable at its view):

```python
# bookmarker/settings.py → REST_FRAMEWORK
'DEFAULT_THROTTLE_RATES': {
    'youtube_proxy':  '30/min',   # 11 cheap proxy views (≈1 unit/call)
    'youtube_search': '6/min',    # LoadRelatedVideosView only (100 units/call)
    'youtube_list':   '10/min',   # YouTubeList (server-side pagination amplifier)
    'bm_create':      '10/min',   # AddBookmark.post (findPlaylistId walks ≤5 playlists × pages)
    'login':          '10/min',   # MyObtainTokenPairView + TokenRefreshView (AnonRateThrottle)
    'register':       '5/min',    # RegisterView (AnonRateThrottle)
},
```

```python
# per view, e.g. VideoCommentsView
from rest_framework.throttling import ScopedRateThrottle, AnonRateThrottle
class VideoCommentsView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'youtube_proxy'
```

- `LoadRelatedVideosView`: `throttle_scope = 'youtube_search'` (overrides the generic scope — it is the only 100-unit endpoint).
- `YouTubeList`: `throttle_scope = 'youtube_list'`; `AddBookmark`: `throttle_scope = 'bm_create'` (POST cost is multi-call; GET dies in [0.1] anyway).
- `MyObtainTokenPairView` and `RegisterView`: `throttle_classes = [AnonRateThrottle]` with scopes `login`/`register` (AllowAny surfaces have no user identity — anon-scope identity is by IP, which is the correct dampener here).
- **Justification vs R8 (conservative):** a normal "open a video page" flow fires ~3 proxy calls (video data + comments + related) — 30/min leaves 10× headroom; 6/min on related-videos still allows rapid browsing of distinct videos while capping worst-case burn at 600 units/min instead of unlimited. Rates are per-user (authenticated identity), so NAT offices don't collide. Ship with 429 monitoring for week one; tighten only on evidence.

---

## 5. Deep-Dive B — SSRF in `scrape_page_metadata` (F14, views.py:339)

**Surface:** `AddBookmark.post` → `scrape_page_metadata(format_url)` (utils/scraper/__init__.py:11–33) → bare `requests.get(url, headers=headers)`. Any authenticated user supplies any URL; `checkUrlType` returns `'bm'` for every non-YouTube URL, so internal hosts sail straight through. Server fetches it, parses HTML with BeautifulSoup, returns title/description/images into the user's bookmark.

**Defects stacked:** no scheme restriction; no timeout (**worker hang DoS**); no response-size cap (memory DoS); `allow_redirects=True` default (redirect-based bypass of any future host check); resolves-and-connects blindly (cloud metadata `169.254.169.254`, localhost services, RFC1918 probing all reachable).

**Disposition: FIX NOW in [1.2].** Rationale: authenticated-only lowers severity but every registered account gets an internal-network probe; the metadata-endpoint class alone justifies it; the fix is small and unit-testable (acceptance criteria already demand "blocks private-range targets, unit-tested").

**Concrete guard design** (implement in `utils/scraper/__init__.py`; `ipaddress`/`socket` are stdlib; `requests==2.34.2` supports everything used):

1. **Scheme allowlist:** `urlsplit(url).scheme in {"http", "https"}` else reject. (Note: `formaturl` coerces schemeless input to `http://`, so exotic schemes like `file:`/`gopher:` arrive mangled — the explicit check closes the residual.)
2. **Resolve-and-block:** `socket.getaddrinfo(hostname, None)`; for **every** returned address run `ipaddress.ip_address(...)`, unwrap IPv4-mapped IPv6 (`addr.ipv4_mapped` — e.g. `::ffff:127.0.0.1` MUST be caught), and reject if any of: `is_private, is_loopback, is_link_local, is_multicast, is_unspecified, is_reserved`.
   **Exact blocked set to enumerate in tests:** `0.0.0.0/8`, `10.0.0.0/8`, `127.0.0.0/8`, `169.254.0.0/16` (incl. `169.254.169.254`), `172.16.0.0/12`, `192.0.0.0/24`, `192.168.0.0/16`, `198.18.0.0/15`, `100.64.0.0/10` (CGNAT), `224.0.0.0/4`, `240.0.0.0/4`, `::1`, `::` (unspecified), `fc00::/7`, `fe80::/10`, `::ffff:0:0/96` (mapped form of all of the above).
3. **DNS-rebinding posture:** resolve once, validate, then connect **to the validated address** with the original `Host` header preserved. Pragmatic minimum for this endpoint: validate → `allow_redirects=False` → handle 3xx manually by absolutizing `Location`, re-running step 2 per hop, max **3** hops. This shrinks the TOCTOU window to the sub-second resolve→connect gap; document as residual risk. Optional hardening (flagged, not required): pin the connection to the first validated IP via a custom `HTTPAdapter`/urllib3 `assert_hostname=False`-style transport — defer unless threat model grows.
4. **Response-size cap: 1 MiB (`1_048_576` bytes).** Fetch with `stream=True`, `timeout=(3.05, 10)` (connect, read), then `r.raw.read(CAP + 1, decode_content=True)` and reject if longer. HTML metadata never needs more; images are NOT fetched server-side (only their URLs are harvested), so 1 MiB is generous.
5. **Content-Type gate:** proceed only if `Content-Type` starts with `text/html` or `text/*` — rejects binary payloads early and caps abuse.
6. **Error normalization (required companion):** today `ConnectionError` is caught at views.py:362 but references a possibly-unbound `serializer` (NameError → 500), and `requests.Timeout`/`SSLError`/`TooManyRedirects` are uncaught (500). The guard should raise one typed exception (e.g. `ScrapeBlocked`) that `AddBookmark.post` maps to **502/400 with a JSON body** — never a 500, never leaking internal diagnostics.

---

## 6. Deep-Dive C — `last_login` Side Effect in `UserDetail.get` (F14, views.py:158)

**What the code actually does:** `user.last_login = timezone.now()` assigns to the **in-memory instance only — there is no `user.save()`**. The database is never written. The only observable effect is that the serialized response reports `last_login = now`, i.e., the API lies to the client on every GET.

**Fix disposition: delete line :158 outright.** Nothing needs replacing — there is no real side effect to preserve.

**Dependency check (grep-verified):**
- `api/admin.py:10,:26` — displays the field in admin (read-only concern; unaffected).
- `api/serializers.py:41` — exposes it in `UserSerializer` output (read; unaffected).
- `frontend/src/**` — **zero references** to `last_login`. Nothing in the UI consumes it.
- `SIMPLE_JWT['UPDATE_LAST_LOGIN'] = False` (settings.py:84) — JWT logins deliberately don't touch it either. After removal, `last_login` reflects Django admin/session logins only, which is coherent and honest.
- Migration 0001 defines the column; no data migration implications.

Risk: **LOW**. One-line deletion; covered by asserting `GET /users/<pk>` twice returns identical `last_login`.

---

## 7. Deep-Dive D — `IsOwnerOrReadOnly` Resolution (F7) — PER-VIEW

**Correction to F7:** the class is attached to **15** views, not 13 (full list below; roadmap undercounted — likely omitted two of the five comment/reply views). Conclusion unchanged: **zero** `check_object_permissions` calls exist repo-wide, so it never executes.

**Critical wiring hazard:** `has_object_permission` evaluates `obj.owner == request.user` (permissions.py:16). Wiring `check_object_permissions` naively into views whose "object" is a `CustomUser` (no `.owner` attribute) or a raw dict/list from googleapiclient raises `AttributeError` → **500**. So "just wire it everywhere" is actively harmful. Per-view disposition:

| View (attachment line†) | Object type if wired | Verdict |
|---|---|---|
| `BmDetailView` (:523) | `Bm` — has `.owner` FK | **WIRE.** Rewrite `get_object` canonically: `bm = get_object_or_404(Bm, pk=pk)` then `self.check_object_permissions(request, bm)`. Replaces the hand-roll at :526–533 AND eliminates the missing-pk None-deref bug class ([0.5]) in the same stroke. The one genuine enforcement win. |
| `UpdateUserCategories` (:177) | `CustomUser` — **no `.owner`** → AttributeError | **REMOVE attachment.** Hand-rolled pk-pin at :180–186 is correct (F1). |
| `OptionsView` (:209) | `UserOptions` — has `.owner` | **REMOVE attachment.** Hand-rolled scoping :215/:221 correct (F1, Lane-B regression-locked). Wiring would be redundant churn. |
| `AddBookmark` (:235) | n/a — no object lookup; ownership enforced at creation (`serializer.save(owner=request.user)` :333/:358) | **REMOVE attachment.** |
| `YouTubeList` (:371), `VideoCommentsView` (:415), `RepliesView` (:431), `RepliesNextPageView` (:443), `NextPageCommentsView` (:457), `RateVideoView` (:472), `GetVideoData` (:561), `ChannelPlaylistsView` (:612), `ChannelNextPlaylistsView` (:623), `AddPlaylistTOBookmarksView` (:632), `LoadRelatedVideosView` (:643) | raw dicts/lists from googleapiclient — public YouTube data, no ownership concept; wiring → AttributeError 500 | **REMOVE attachment (all 11).** |

**Net:** 14 attachments stripped, 1 wired (`BmDetailView`). **Keep the class** in `api/permissions.py` — it becomes live and load-bearing via `BmDetailView`. End state satisfies "never attached-but-inert". Update Lane B's [0.6] note accordingly: after [1.4], `BmDetailView` ownership is enforced by the permission class (test via the standard mechanism), while :148/:180/:215/:490/:510 remain hand-rolled assertions.

---

## 8. Additional Findings for Phase 1 (item 6 of brief)

### 8.1 `RateVideoView` is dead-on-arrival AND globally toxic — `utils/rate_video.py`
- :13 `client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"` — placeholder, file doesn't exist.
- :19 `flow.run_console()` — **removed from google-auth-oauthlib ≥1.0** (installed: 1.4.0) → `AttributeError` on every call → guaranteed 500.
- :10 `os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"` — **process-wide** side effect at import time; disables OAuth transport security for anything else using oauthlib in-process.
- **Disposition:** default **remove** route (`api/urls.py:39`) + view + util (feature cannot work; nobody can be relying on a constant 500). If product wants video-rating later, rebuild on a proper web/device OAuth flow. Either way the `OAUTHLIB_INSECURE_TRANSPORT` global goes.

### 8.2 `YouTubeList` unbounded pagination loop — views.py:381–390
`while True` walks **every** page (50 items/page) of the playlist server-side: a 10k-item playlist = ~200 upstream API calls for ONE user request — a quota-amplification primitive. Fix: `max_pages = getattr(settings, 'YT_PLAYLIST_MAX_PAGES', 10)` (≤500 items) and stop; pair with the `youtube_list` throttle. (Same pattern exists inside `findPlaylistId`, find_playlist.py:73, but is bounded by `YT_PLAYLIST_AUTO_DETECT_MAX=5` playlists — acceptable.)

### 8.3 `AddBookmark.post` guaranteed-500 error paths (hygiene bundle for [1.1]/[1.2] implementer)
- `request.data["url"]` / `["category"]` direct indexing (:244, :306, :343) → KeyError 500 on malformed body → wrap → 400.
- `video_data["items"][0]` (:259–262) → IndexError 500 when the API returns zero items (deleted/private video) → 400.
- `snip`/`statistics` referenced when `url_type == 'yt'` but `video_id` falsy (:303ff) → UnboundLocalError 500.
- `list_index` possibly never assigned when playlist lacks the video (:288–290) → UnboundLocalError 500.
- `serializer` unbound at :364/:367 when `ConnectionError` fires before :352 (see §5.6) → NameError 500.
All normalize to 400-class responses; none are authorization issues.

### 8.4 🚨 `UserDetail.put` privilege escalation — ESCALATE TO LANE A AS [0.6]
Evidence chain: serializers.py:41–42 (`fields` include `is_staff, is_active, is_superuser`, no `read_only` kwargs → DRF ModelSerializer renders them **writable**) × views.py:162–168 (`UserSerializer(user, data=request.data)` then `save()`). Exploit: `PUT /api/users/<own-pk>` body `{"is_superuser": true}` → superuser. Self-target only (:148 pins pk) but full escalation.
Remediation: introduce `UserUpdateSerializer` limited to `('first_name', 'last_name')` (optionally `categories`) and use it in `put`; leave `UserSerializer` read-facing. Also fixes the nested-`options` PUT 500 (DRF refuses nested writes). Regression tests: (a) `PUT {"is_superuser": true}` → field ignored/rejected; (b) name update still works; (c) response contains no `is_staff` mutation.
Blast radius: `updateUserData` (authActions.js:187) has **zero in-repo callers**; extension usage unknown — apply the R7-style consumer check before shipping.

### 8.5 Minor / cross-reference only
- `MyTokenObtainPairSerializer.validate` (serializers.py:59–68) returns success-shaped payloads distinguishing registered/inactive emails → enumeration oracle + broken client contract. P2 candidate; not Phase 1.
- `BmListSearchView` :506–507 dead branch (unused `user`) — cosmetic.
- `OptionsView.settings` JSONField accepts arbitrary JSON — stored-data sink; frontend rendering responsibility; note only.
- `BmDetailView.put` `request.data["video_data"]` KeyError → 500 — fold into [0.5]'s error normalization.
- `extensionLogin` sits outside DRF → DRF throttles can't reach it; if it survives [0.4]'s compat window, use `django-ratelimit` or early-410 (noted in §3 row 25).

---

## 9. Phase-1 Implementation Checklist (dependency-ordered)

Owners per roadmap conventions; Phase 1 is fundamentally **serial on `api/views.py`** (matches [1.1]→[1.4] chaining). Parallelizable islands called out.

- **[P1.0] ⚠️ ESCALATION — `UserDetail.put` serializer lockdown** — owner: build (Lane A, insert as [0.6]) — parallel: no (views.py serial chain) — deps: Lane A [0.5] — files: api/views.py, api/serializers.py — risk: MED (consumer check per §8.4). *If not absorbed into Phase 0, this is the first Phase-1 commit.*
- **[P1.1-pre] Add validators to `utils/urlutils.py`** — owner: build — **parallel: YES** (pure additive module edit; zero overlap with views.py work) — deps: none — files: utils/urlutils.py — risk: LOW. Deliver `VIDEO_ID_RE`, `PLAYLIST_ID_RE` (wrapping existing charsets) + `CHANNEL_ID_RE`, `COMMENT_ID_RE`, `PAGE_TOKEN_RE` (gap-fills) + a `validate_or_400` helper.
- **[P1.1a] Wire ID/order validation into the 12 proxy views** — owner: build — parallel: no (views.py) — deps: P1.0 resolved, P1.1-pre, Lane A complete — files: api/views.py — risk: MED (R8 UX check on strictness).
- **[P1.1b] Throttles** — owner: build — parallel: no (same-file sequence; settings.py edit is disjoint but ship together) — deps: P1.1a — files: bookmarker/settings.py, api/views.py — risk: MED (monitor 429s week one).
- **[P1.1c] Cap `YouTubeList` pagination** — owner: build — parallel: no — deps: P1.1b — files: api/views.py, bookmarker/settings.py (`YT_PLAYLIST_MAX_PAGES`) — risk: LOW.
- **[P1.2] SSRF guard + scrape error normalization** — owner: build — parallel: no (touches AddBookmark again) — deps: P1.1c — files: utils/scraper/__init__.py, api/views.py — risk: MED. Unit-test matrix: every range in §5.2 blocked; public URL passes; redirect-to-private rejected; >1 MiB rejected; timeout → 502.
- **[P1.3] Delete `last_login` line** — owner: general — parallel: no (views.py) — deps: P1.2 — files: api/views.py — risk: LOW. Test: two consecutive GETs return identical `last_login`.
- **[P1.4] Resolve IOOR** — owner: build — parallel: no — deps: P1.3 — files: api/permissions.py (keep class), api/views.py (strip 14, wire 1) — risk: MED. Verify: `BmDetailView` cross-user GET/PUT/DELETE → 403/404; all other views behaviorally unchanged (Lane B suite green).
- **[P1.5] `RateVideoView` disposition** — owner: build (default: remove route+view+util) — parallel: no — deps: P1.4 — files: api/urls.py, api/views.py, utils/rate_video.py — risk: LOW (endpoint already 100% broken; confirm no consumer first).
- **[P1.6] Verification sweep** — owner: critic (review) + build (tests) — parallel: critic runs after tests — deps: P1.5 — files: api/tests/* — Gate: full suite green; acceptance criteria P1 bullet satisfied verbatim ("all 12 proxy views enforce ID format + return 429 under burst; SSRF guard blocks private-range targets (unit-tested); GET /users/<pk> no longer mutates last_login; IsOwnerOrReadOnly either enforced or deleted").

**Regression-suite coordination (Lane B [0.6]):** unaffected — its named subjects (:148, :180, :215/:221, :490, :510 hand-rolls) survive intact; only `BmDetailView`'s mechanism changes from hand-roll to permission-class, which [0.6] should assert *behaviorally* (cross-user denial), not mechanically.

---

## 10. Acceptance Checklist for the Spec Consumer (engineer sign-off)

- [ ] Every one of the 25 views appears in §3 with a verdict and an implementable action.
- [ ] All 12 proxy views have a named validator from §4.1 (existing urlutils assets reused; only 3 gap-fill constants added, in urlutils.py itself).
- [ ] Throttle scopes/rates copied verbatim from §4.3 into settings + views.
- [ ] SSRF guard implements §5 items 1–6 including the exact blocked-range test matrix.
- [ ] `last_login` fix is the one-line deletion per §6 (no replacement logic invented).
- [ ] IOOR end-state matches §7 exactly: 14 stripped, 1 wired, class retained.
- [ ] §8.4 escalation surfaced to Bob/Lane A before Phase 1 begins.
