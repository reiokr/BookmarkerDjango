from urllib.error import HTTPError

import requests
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from utils import fetch_youtube, find_playlist
from utils.fetch_channel import (
    fetch_channel_next_playlists,
    fetch_channel_playlists,
    search_related_videos,
)
from utils.fetch_video_comments import (
    fetch_next_comments,
    fetch_video_comments,
    get_next_replies,
    get_replies,
)
from utils.find_playlist import get_playlist_item
from utils.rate_video import rate_video
from utils.scraper import ScrapeBlocked, scrape_page_metadata
from utils.urlutils import (
    CHANNEL_ID_RE,
    COMMENT_ID_RE,
    PAGE_TOKEN_RE,
    PLAYLIST_ID_RE,
    VIDEO_ID_RE,
    checkUrlType,
    extractPlaylistId,
    extractVideoId,
    formaturl,
    getStartTime,
    getUrl,
    matches_id,
)

from .models import Bm, Bml, CustomUser, UserOptions
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    BmlSerializer,
    BmSerializer,
    CategorySerializer,
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    UserOptionsSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .tokens import account_activation_token

# Valid values for the commentThreads().list ``order`` enum (audit spec §4.1).
YT_COMMENT_ORDERS = ("time", "relevance")


def _reject_bad_id(value, regex, param):
    """Audit spec §4.1: non-conforming proxy IDs are a 400 client error.

    Applied at the top of every YouTube-proxy handler so garbage never
    reaches googleapiclient (which would otherwise burn quota on a doomed
    upstream call and surface as a 500).
    """
    if not matches_id(value, regex):
        raise ValidationError({param: ["Invalid identifier format."]})


# AnonRateThrottle reads its scope from the CLASS attribute (only
# ScopedRateThrottle consults view.throttle_scope), so per-surface scopes
# are attached via subclasses -- the standard DRF pattern.
class LoginAnonRateThrottle(AnonRateThrottle):
    scope = "login"


class RegisterAnonRateThrottle(AnonRateThrottle):
    scope = "register"


@api_view(["GET"])
def getRoutes(request):
    routes = ["/main/login", "/main/login/refresh"]
    return Response(routes)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getCurrentUser(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class MyObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = MyTokenObtainPairSerializer
    # Audit spec §4.3: AllowAny surfaces have no user identity, so the
    # anonymous scope keys by IP -- the correct credential-stuffing dampener.
    throttle_classes = [LoginAnonRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    """TokenRefreshView with the shared anonymous ``login`` throttle."""

    throttle_classes = [LoginAnonRateThrottle]


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterAnonRateThrottle]

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = RegisterSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            user = CustomUser.objects.get(email=request.data["email"])
            # to get the domain of the current site
            if user:
                current_site = get_current_site(request)
                mail_subject = "Activation link has been sent to your email id"
                msg = render_to_string(
                    "api/acc_active_email.html",
                    {
                        "user": f"{user.first_name} {user.last_name}",
                        "domain": current_site.domain,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": account_activation_token.make_token(user),
                    },
                )
                to_email = [user.email]

                send_mail(
                    subject=mail_subject,
                    message=msg,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=to_email,
                )

                return Response(
                    {"msg": "Verification link sent to your email"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse(
            "Thank you for your email confirmation. Now you can login your account."
        )
    else:
        return HttpResponse("Activation link is invalid!")


class UserDetail(APIView):
    """
    Retrieve, update or delete a user instance.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        if self.request.user.id == pk:
            try:
                return CustomUser.objects.get(pk=pk)
            except CustomUser.DoesNotExist:
                raise Http404
        else:
            raise PermissionDenied()

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        # Audit spec §8.4: UserSerializer renders is_staff/is_active/
        # is_superuser writable, so binding request.data into it let any
        # user promote themselves (PUT {"is_superuser": true}). Writes go
        # through UserUpdateSerializer -- first_name/last_name ONLY;
        # privilege fields are not accepted and never reach the model.
        user = self.get_object(pk)
        serializer = UserUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        # Partial self-service profile update; same lockdown as put().
        user = self.get_object(pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateUserCategories(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        if self.request.user.id == pk:
            try:
                return CustomUser.objects.get(pk=pk)
            except CustomUser.DoesNotExist:
                raise Http404
        else:
            raise PermissionDenied()

    def get(self, request, pk, format=None):
        user = self.get_object(pk)
        serializer = CategorySerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        user = self.get_object(self.request.user.id)
        serializer = CategorySerializer(user, data=request.data)
        category = request.data.get("category", "")
        if category and category != "category":
            # Roadmap fact F3 fix: only the CALLER'S OWN bookmarks may
            # influence this decision. The old query ran unscoped across all
            # users' bookmarks, making every user's data a category-existence
            # oracle for everyone else, and the old nested
            # ``if serializer.is_valid(): return serializer.errors`` block was
            # inverted -- it only rejected *valid* payloads and answered 403
            # with an empty error body.
            already_backed = Bm.objects.filter(
                owner=request.user, category__iexact=category
            ).exists()
            if already_backed:
                return Response(
                    {"detail": "Category already exists."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get(self, request, format=None):
        options = UserOptions.objects.filter(owner=request.user.id)
        serializer = UserOptionsSerializer(options, many=True)
        return Response(serializer.data)

    def put(self, request, format=None):
        try:
            options = UserOptions.objects.get(owner=request.user.id)
            serializer = UserOptionsSerializer(options, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        except UserOptions.DoesNotExist:
            serializer = UserOptionsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(owner=self.request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddBookmark(APIView):
    permission_classes = [IsAuthenticated]
    # POST cost is multi-call (findPlaylistId walks playlists server-side),
    # hence the tightest create scope; GET is gone by design (see below).
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "bm_create"

    # NOTE: no GET handler on purpose. The former GET returned
    # Bm.objects.all() -- every user's bookmarks -- to any authenticated
    # caller (roadmap fact F2); it was an unrouted-in-practice debug
    # leftover with no frontend consumer (R1 grep: bmActions.js only POSTs).
    # Listing lives in BmListView (owner-scoped). Unsupported methods now
    # get DRF's standard 405.

    def post(self, request, format=None):
        # Audit spec §8.3: malformed bodies are client errors (400), never
        # KeyError -> 500.
        raw_url = request.data.get("url")
        category = request.data.get("category")
        if not raw_url or not category:
            return Response(
                {"detail": "url and category are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # validate url
        format_url = formaturl(raw_url)
        # check the url type
        url_type = checkUrlType(format_url)
        # if youtube video url, get video id
        video_id = extractVideoId(format_url)
        # Audit spec §4.1: extracted IDs are asserted against the charset
        # the extractor already accepts -- truthy-but-nonconforming -> 400.
        if video_id:
            _reject_bad_id(video_id, VIDEO_ID_RE, "video_id")
        # if youtube video url with time indicator, get time
        startAt = getStartTime(format_url)

        if format_url and url_type == "yt":
            if not video_id:
                # §8.3: a yt-classified URL without an extractable video id
                # used to blow up on unbound snip/statistics below.
                return Response(
                    {"detail": "Could not extract a YouTube video id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            video_data = fetch_youtube.fetch_Video(video_id)
            items = video_data.get("items") or []
            if not items:
                # §8.3: deleted/private videos come back with zero items --
                # a client-input problem, not an IndexError 500.
                return Response(
                    {"detail": "Video not found on YouTube."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            snip = items[0]["snippet"]
            detail = items[0]["contentDetails"]
            bm_status = items[0]["status"]
            statistics = items[0]["statistics"]
            # if no tags attribute set tags []
            if "tags" in snip:
                tags = snip["tags"]
            else:
                tags = []
            try:
                dislikeCount = statistics["dislikeCount"]
            except KeyError:
                dislikeCount = 0
            try:
                commentCount = statistics["commentCount"]
            except KeyError:
                commentCount = 0
            try:
                viewCount = statistics["viewCount"]
            except KeyError:
                viewCount = 0

            # find list id from url
            list_id = extractPlaylistId(format_url)
            if list_id:
                _reject_bad_id(list_id, PLAYLIST_ID_RE, "list_id")
            # §8.3: initialise so a playlist without this video cannot leave
            # them unbound.
            list_index = None
            list_items_count = 0
            # if list id exists fetch playlist items from youtube API
            if list_id:
                playlist = find_playlist.get_playlist_items(list_id, "")
                # find list item playlist index
                list_items_count = playlist["pageInfo"]["totalResults"]
                for item in playlist["items"]:
                    if item["contentDetails"]["videoId"] == video_id:
                        list_index = item["snippet"]["position"]
            else:
                found = find_playlist.findPlaylistId(video_id)
                if found:
                    list_id = found["playlist_id"]
                    list_index = found["position"]
                    pl_items = find_playlist.get_playlist_items(list_id, "")
                    list_items_count = pl_items["pageInfo"]["totalResults"]

            # create youtube video bookmark object
            data = {
                "title": snip["title"],
                "description": snip["description"],
                "category": category,
                "bm_type": "yt",
                "thumbnails": snip["thumbnails"],
                "url": getUrl(raw_url),
                "video_id": video_id,
                "list_id": list_id,
                "list_index": list_index,
                "list_items_count": list_items_count,
                "channel_id": snip["channelId"],
                "channel_title": snip["channelTitle"],
                "start_at": startAt,
                "keywords": tags,
                "length": detail["duration"],
                "view_count": viewCount,
                "like_count": statistics["likeCount"],
                "comment_count": commentCount,
                "privacy_status": bm_status["privacyStatus"],
                "publish_date": snip["publishedAt"],
                "original_category": snip["categoryId"],
            }

            serializer = BmSerializer(data=data)
            if serializer.is_valid():
                cat = category.strip()
                if cat and cat.lower() not in [c.lower() for c in request.user.categories]:
                    request.user.categories.append(cat)
                    request.user.save(update_fields=["categories"])
                serializer.save(owner=self.request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if format_url and url_type == "bm":
            try:
                # Scrape bookmark data from html (SSRF-guarded, audit §5)
                bookmark_meta = scrape_page_metadata(format_url)
            except ScrapeBlocked as exc:
                # §5.6: guard violations surface as client-facing JSON --
                # never a 500, never internal diagnostics.
                return Response(
                    {"detail": "Bookmark fetch blocked: %s" % exc},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except requests.Timeout:
                return Response(
                    {"detail": "Bookmark site timed out."},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )
            except requests.ConnectionError:
                return Response(
                    {"detail": "Could not reach the bookmark site."},
                    status=status.HTTP_504_GATEWAY_TIMEOUT,
                )
            except requests.RequestException:
                return Response(
                    {"detail": "Failed to fetch the bookmark page."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            data = {
                "title": bookmark_meta["title"],
                "description": bookmark_meta["description"],
                "category": category,
                "bm_type": "bm",
                "image_url": bookmark_meta["image_url"],
                "url": bookmark_meta["url"],
            }
            if not bookmark_meta["title"]:
                data["title"] = bookmark_meta["sitename"]

            serializer = BmlSerializer(data=data)
            if serializer.is_valid():
                cat = category.strip()
                if cat and cat.lower() not in [c.lower() for c in request.user.categories]:
                    request.user.categories.append(cat)
                    request.user.save(update_fields=["categories"])
                serializer.save(owner=self.request.user)
                return Response(status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": "Unsupported URL."}, status=status.HTTP_400_BAD_REQUEST
        )


class YouTubeList(APIView):
    permission_classes = [IsAuthenticated]
    # Server-side pagination amplifier: one request used to walk EVERY page
    # of the playlist upstream (audit spec §8.2). Throttled + page-capped.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_list"

    def get_object(self, list_id):
        _reject_bad_id(list_id, PLAYLIST_ID_RE, "list_id")

        data = find_playlist.get_playlist_items(list_id, "")

        # Audit spec §8.2: walk at most YT_PLAYLIST_MAX_PAGES pages
        # (default 10 => <=500 items) instead of every page of the playlist.
        pageToken = data.get("nextPageToken")
        items = list(data["items"])
        max_pages = getattr(settings, "YT_PLAYLIST_MAX_PAGES", 10)
        pages_fetched = 1
        while pageToken and pages_fetched < max_pages:
            newdata = find_playlist.get_playlist_items(list_id, pageToken)
            pages_fetched += 1
            items.extend(newdata["items"])
            pageToken = newdata.get("nextPageToken")
        playlist = []
        for item in items:
            # duration = fetch_youtube.get_video_duration(item["contentDetails"]['videoId'])

            playlist.append(
                {
                    "list_item_id": item["id"],
                    "published_at": item["snippet"]["publishedAt"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "thumbnails": item["snippet"]["thumbnails"],
                    "list_id": list_id,
                    "list_index": item["snippet"]["position"],
                    "video_id": item["contentDetails"]["videoId"],
                }
            )
        return playlist

    def get(self, request, list_id, format=None):
        playlist_data = self.get_object(list_id)
        return JsonResponse(playlist_data, safe=False)


class VideoCommentsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get_object(self, video_id):
        order = self.kwargs.get("order")
        data = fetch_video_comments(video_id, order)
        return data

    def get(self, request, *args, **kwargs):
        _reject_bad_id(kwargs.get("video_id"), VIDEO_ID_RE, "video_id")
        # ``order`` is an upstream API enum, not free text (audit spec §4.1).
        if kwargs.get("order") not in YT_COMMENT_ORDERS:
            raise ValidationError(
                {"order": ["Must be one of: %s" % ", ".join(YT_COMMENT_ORDERS)]}
            )
        try:
            comments = self.get_object(kwargs.get("video_id"))
            return JsonResponse(comments, safe=False)
        except PermissionDenied:
            raise Http404


class RepliesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get_object(self, parent_id):
        data = get_replies(parent_id)
        return data

    def get(self, request, *args, **kwargs):
        _reject_bad_id(kwargs.get("parent_id"), COMMENT_ID_RE, "parent_id")
        comments = self.get_object(kwargs.get("parent_id"))
        return JsonResponse(comments, safe=False)


class RepliesNextPageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get_object(self, parent_id):
        page_token = self.kwargs.get("page_token")
        data = get_next_replies(parent_id, page_token)

        return data

    def get(self, request, *args, **kwargs):
        _reject_bad_id(kwargs.get("parent_id"), COMMENT_ID_RE, "parent_id")
        _reject_bad_id(
            kwargs.get("page_token"), PAGE_TOKEN_RE, "page_token"
        )
        comments = self.get_object(kwargs.get("parent_id"))
        return JsonResponse(comments, safe=False)


class NextPageCommentsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get_object(self, video_id):
        order = self.kwargs.get("order")
        page_token = self.kwargs.get("page_token")
        data = fetch_next_comments(video_id, page_token, order)

        return data

    def get(self, request, *args, **kwargs):
        _reject_bad_id(kwargs.get("video_id"), VIDEO_ID_RE, "video_id")
        _reject_bad_id(
            kwargs.get("page_token"), PAGE_TOKEN_RE, "page_token"
        )
        if kwargs.get("order") not in YT_COMMENT_ORDERS:
            raise ValidationError(
                {"order": ["Must be one of: %s" % ", ".join(YT_COMMENT_ORDERS)]}
            )
        comments = self.get_object(kwargs.get("video_id"))
        return JsonResponse(comments, safe=False)


class RateVideoView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get(self, request, video_id):
        _reject_bad_id(video_id, VIDEO_ID_RE, "video_id")
        response = rate_video(video_id)
        return JsonResponse(response)


class BmListView(generics.ListCreateAPIView):
    queryset = Bm.objects.filter()
    serializer_class = BmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category = self.kwargs.get("category")
        if not category:
            return Bm.objects.none()
        queryset = (
            Bm.objects.filter(category__iexact=category)
            .filter(owner_id=self.request.user.id)
            .order_by("updated_at")
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BmListSearchView(generics.ListCreateAPIView):
    queryset = Bm.objects.filter()
    serializer_class = BmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category = self.kwargs["category"]
        if not category:
            user = CustomUser.objects.get(pk=self.request.user.id)
        search = self.kwargs["search"]
        queryset = Bm.objects.filter(category__iexact=category).filter(
            owner_id=self.request.user.id
        )

        qs = queryset.filter(title__icontains=search) | queryset.filter(
            description__icontains=search
        )
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BmDetailView(APIView):
    # Audit spec §7: the ONE view where IsOwnerOrReadOnly is wired and
    # load-bearing -- get_object() calls check_object_permissions on every
    # request, so the attachment is never inert.
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, pk):
        # Canonical object fetch (audit spec §7.2): 404 for a missing pk,
        # then object-level permission enforcement.
        bm = get_object_or_404(Bm.objects.select_related("owner"), pk=pk)
        # IsOwnerOrReadOnly executes here: unsafe methods require
        # obj.owner == request.user or DRF raises PermissionDenied (403).
        self.check_object_permissions(self.request, bm)
        # Reads are owner-scoped as well: a foreign bookmark is invisible
        # even to GET -- the contract pinned by api/tests/test_ownership.py
        # (cross-user GET/PUT/DELETE -> 403).
        if bm.owner_id != self.request.user.id:
            raise PermissionDenied()
        return bm

    def get(self, request, pk, format=None):
        bm = self.get_object(pk)
        serializer = BmSerializer(bm)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        data = request.data["video_data"]
        # data['start_at'] = request.data['start_at']
        if not data["list_id"]:
            data["list_id"] = None
        if not data["list_index"]:
            data["list_index"] = None
        bm = self.get_object(pk)
        serializer = BmSerializer(bm, data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        bm = self.get_object(pk)
        bm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetVideoData(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get_object(self, video_id):
        return fetch_youtube.fetch_Video(video_id)

    def get(self, request, video_id, format=None):
        _reject_bad_id(video_id, VIDEO_ID_RE, "video_id")
        video_data = self.get_object(video_id)
        snip = video_data["items"][0]["snippet"]
        detail = video_data["items"][0]["contentDetails"]
        bm_status = video_data["items"][0]["status"]
        statistics = video_data["items"][0]["statistics"]
        # print(video_data)

        if "tags" in snip:
            tags = snip["tags"]
        else:
            tags = []
        try:
            commentCount = statistics["commentCount"]
        except KeyError:
            commentCount = 0

        data = {
            "title": snip["title"],
            "description": snip["description"],
            "category": "default",
            "bm_type": "yt",
            "thumbnails": snip["thumbnails"],
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "video_id": video_id,
            "list_id": "",
            "list_index": 0,
            "channel_id": snip["channelId"],
            "channel_title": snip["channelTitle"],
            "start_at": 0,
            "keywords": tags,
            "length": detail["duration"],
            "view_count": statistics["viewCount"],
            "like_count": statistics["likeCount"],
            "comment_count": commentCount,
            "privacy_status": bm_status["privacyStatus"],
            "publish_date": snip["publishedAt"],
            "original_category": snip["categoryId"],
        }
        serializer = BmSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChannelPlaylistsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get(self, request, channel_id, *args, **kwargs):
        _reject_bad_id(channel_id, CHANNEL_ID_RE, "channel_id")
        try:
            playlists = fetch_channel_playlists(channel_id)
            return JsonResponse(playlists, safe=False)
        except PermissionDenied:
            raise Http404


class ChannelNextPlaylistsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get(self, request, channel_id, *args, **kwargs):
        _reject_bad_id(channel_id, CHANNEL_ID_RE, "channel_id")
        _reject_bad_id(kwargs.get("token"), PAGE_TOKEN_RE, "token")
        token = kwargs.get("token")
        next_playlists = fetch_channel_next_playlists(channel_id, token)
        return JsonResponse(next_playlists, safe=False)


class AddPlaylistTOBookmarksView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_proxy"

    def get(self, request, pl_id, *args, **kwargs):
        _reject_bad_id(pl_id, PLAYLIST_ID_RE, "pl_id")
        try:
            bookmark = get_playlist_item(pl_id)
            return JsonResponse(bookmark, safe=False)
        except PermissionDenied:
            raise Http404


class LoadRelatedVideosView(APIView):
    permission_classes = [IsAuthenticated]
    # search.list costs 100 quota units vs 1 for every other proxy call --
    # the only view on the tightest scope (audit spec §4.3).
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "youtube_search"

    def get(self, request, video_id, *args, **kwargs):
        _reject_bad_id(video_id, VIDEO_ID_RE, "video_id")
        try:
            relatedVideos = search_related_videos(video_id)
            return JsonResponse(relatedVideos, safe=False)
        except PermissionDenied:
            raise Http404


@api_view(["POST"])
@permission_classes([AllowAny])
def extensionLogin(request):
    """Browser-extension login endpoint -- rewritten by roadmap step [0.4].

    Contract (v2, BREAKING vs the legacy GET+HTML flow):

    * Method: POST only. Any other method (including the legacy GET) is
      rejected by DRF with 405. Credentials are never accepted via query
      string.
    * Request body: JSON ``{"email": str, "password": str}``.
    * Responses are application/json ONLY -- no HTML, no inline JavaScript,
      no template rendering, hence zero credential-interpolation surface:

      - 200 ``{"ok": true, "access": <jwt>, "refresh": <jwt>,
        "first_name": str, "categories": [str]}``
      - 400 ``{"ok": false, "error": "email and password are required"}``
        when either field is missing or blank
      - 401 ``{"ok": false, "error": ...}`` for unknown email / wrong
        password / unverified account (mirrors /api/login/ semantics)

    * The submitted email/password are NEVER echoed back in any response
      body. The user's email is deliberately omitted from the success
      payload as well; consumers needing it can call GET /api/user/me with
      the returned access token.

    * No postMessage: this endpoint no longer renders a framed page at all.
      The extension performs its own fetch() against this endpoint and owns
      its own messaging; the legacy ``postMessage(result, '*')`` JWT leak is
      gone entirely.

    Migration note (risk R7): repo-wide grep found no in-repo consumer of
    the legacy flow; any external browser-extension consumer must switch
    from GET-with-query-params to POST JSON per this contract.
    """
    email = request.data.get("email", "")
    password = request.data.get("password", "")
    if not email or not password:
        return Response(
            {"ok": False, "error": "email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token_serializer = MyTokenObtainPairSerializer(
        data={"email": email, "password": password}
    )
    try:
        token_serializer.is_valid(raise_exception=False)
    except AuthenticationFailed:
        # Wrong password for an existing, active account.
        token_serializer = None

    validated = getattr(token_serializer, "validated_data", None)
    if not isinstance(validated, dict) or "access" not in validated:
        # MyTokenObtainPairSerializer signals not-registered / not-verified
        # accounts by returning a status-carrying dict instead of raising.
        detail = "Invalid credentials"
        if isinstance(validated, dict) and validated.get("msg"):
            detail = str(validated["msg"])
        return Response(
            {"ok": False, "error": detail},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user = token_serializer.user
    return Response(
        {
            "ok": True,
            "access": validated["access"],
            "refresh": validated["refresh"],
            "first_name": user.first_name or "",
            "categories": list(user.categories or []),
        }
    )
