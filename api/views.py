from urllib.error import HTTPError

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import Http404, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

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
from utils.scraper import scrape_page_metadata
from utils.urlutils import (
    checkUrlType,
    extractPlaylistId,
    extractVideoId,
    formaturl,
    getStartTime,
    getUrl,
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
)
from .tokens import account_activation_token


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


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

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
        user.last_login = timezone.now()
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, format=None):
        user = self.get_object(pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        user = self.get_object(pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateUserCategories(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    # NOTE: no GET handler on purpose. The former GET returned
    # Bm.objects.all() -- every user's bookmarks -- to any authenticated
    # caller (roadmap fact F2); it was an unrouted-in-practice debug
    # leftover with no frontend consumer (R1 grep: bmActions.js only POSTs).
    # Listing lives in BmListView (owner-scoped). Unsupported methods now
    # get DRF's standard 405.

    def post(self, request, format=None):
        # validate url
        format_url = formaturl(request.data["url"])
        # check the url type
        url_type = checkUrlType(format_url)
        # if youtube video url, get video id
        video_id = extractVideoId(format_url)
        # if youtube video url with time indicator, get time
        startAt = getStartTime(format_url)
        # if bookmark type is 'yt' fetch video data from youtube API
        # if format_url and url_type == "bm":
        #     return

        if format_url and url_type == "yt":
            if video_id:
                video_data = fetch_youtube.fetch_Video(video_id)
                # pprint(video_data)
                snip = video_data["items"][0]["snippet"]
                detail = video_data["items"][0]["contentDetails"]
                bm_status = video_data["items"][0]["status"]
                statistics = video_data["items"][0]["statistics"]
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
            # if list id exists fetch playlist items from youtube API
            # print(list_id)
            if list_id:
                playlist = find_playlist.get_playlist_items(list_id, "")
                # find list item playlist index
                list_items_count = playlist["pageInfo"]["totalResults"]
                for item in playlist["items"]:
                    if item["contentDetails"]["videoId"] == video_id:
                        list_index = item["snippet"]["position"]
            else:
                found = find_playlist.findPlaylistId(video_id) if video_id else None
                if found:
                    list_id = found["playlist_id"]
                    list_index = found["position"]
                    pl_items = find_playlist.get_playlist_items(list_id, "")
                    list_items_count = pl_items["pageInfo"]["totalResults"]
                else:
                    list_index = None
                    list_id = None
                    list_items_count = 0
            # create youtube video bookmark object
            data = {
                "title": snip["title"],
                "description": snip["description"],
                "category": request.data["category"],
                "bm_type": "yt",
                "thumbnails": snip["thumbnails"],
                "url": getUrl(request.data["url"]),
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
                cat = request.data.get("category", "").strip()
                if cat and cat.lower() not in [c.lower() for c in request.user.categories]:
                    request.user.categories.append(cat)
                    request.user.save(update_fields=["categories"])
                serializer.save(owner=self.request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        if format_url and url_type == "bm":
            try:
                # Scrape bookmark data from html
                bookmark_meta = scrape_page_metadata(format_url)
                data = {
                    "title": bookmark_meta["title"],
                    "description": bookmark_meta["description"],
                    "category": request.data["category"],
                    "bm_type": "bm",
                    "image_url": bookmark_meta["image_url"],
                    "url": bookmark_meta["url"],
                }
                if not bookmark_meta["title"]:
                    data["title"] = bookmark_meta["sitename"]

                if url_type == "bm":
                    serializer = BmlSerializer(data=data)
                    if serializer.is_valid():
                        cat = request.data.get("category", "").strip()
                        if cat and cat.lower() not in [c.lower() for c in request.user.categories]:
                            request.user.categories.append(cat)
                            request.user.save(update_fields=["categories"])
                        serializer.save(owner=self.request.user)
                        return Response(status=status.HTTP_201_CREATED)

            # if connection with provided url filed, raise connection error
            except ConnectionError:
                return Response(
                    serializer.errors, status=status.HTTP_504_GATEWAY_TIMEOUT
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class YouTubeList(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, list_id):
        data = find_playlist.get_playlist_items(list_id, "")

        try:
            pageToken = data["nextPageToken"]
        except:
            pageToken = None
            items = data["items"]
        while True:
            if not pageToken:
                break
            newdata = find_playlist.get_playlist_items(list_id, pageToken)
            items = data["items"]
            items.extend(newdata["items"])
            try:
                pageToken = newdata["nextPageToken"]
            except:
                pageToken = None
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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, video_id):
        order = self.kwargs.get("order")
        data = fetch_video_comments(video_id, order)
        return data

    def get(self, request, *args, **kwargs):
        try:
            comments = self.get_object(kwargs.get("video_id"))
            return JsonResponse(comments, safe=False)
        except PermissionDenied:
            raise Http404


class RepliesView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, parent_id):
        data = get_replies(parent_id)
        return data

    def get(self, request, *args, **kwargs):
        comments = self.get_object(kwargs.get("parent_id"))
        return JsonResponse(comments, safe=False)


class RepliesNextPageView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, parent_id):
        page_token = self.kwargs.get("page_token")
        data = get_next_replies(parent_id, page_token)

        return data

    def get(self, request, *args, **kwargs):
        comments = self.get_object(kwargs.get("parent_id"))
        return JsonResponse(comments, safe=False)


class NextPageCommentsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, video_id):
        order = self.kwargs.get("order")
        page_token = self.kwargs.get("page_token")
        data = fetch_next_comments(video_id, page_token, order)

        return data

    def get(self, request, *args, **kwargs):
        comments = self.get_object(kwargs.get("video_id"))
        return JsonResponse(comments, safe=False)


class RateVideoView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, video_id):
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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, pk):
        bookmark = Bm.objects.filter(pk=pk).first()
        # Roadmap fact F14 bonus defect: a missing pk used to dereference
        # None here and blow up as a 500. Missing bookmarks are a 404.
        if bookmark is None:
            raise Http404
        if self.request.user.id == bookmark.owner_id:
            try:
                return Bm.objects.get(pk=pk)
            except Bm.DoesNotExist:
                raise Http404
        else:
            raise PermissionDenied()

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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, video_id):
        return fetch_youtube.fetch_Video(video_id)

    def get(self, request, video_id, format=None):
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
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, channel_id, *args, **kwargs):
        try:
            playlists = fetch_channel_playlists(channel_id)
            return JsonResponse(playlists, safe=False)
        except PermissionDenied:
            raise Http404


class ChannelNextPlaylistsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, channel_id, *args, **kwargs):
        token = kwargs.get("token")
        next_playlists = fetch_channel_next_playlists(channel_id, token)
        return JsonResponse(next_playlists, safe=False)


class AddPlaylistTOBookmarksView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, pl_id, *args, **kwargs):
        try:
            bookmark = get_playlist_item(pl_id)
            return JsonResponse(bookmark, safe=False)
        except PermissionDenied:
            raise Http404


class LoadRelatedVideosView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, video_id, *args, **kwargs):
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
