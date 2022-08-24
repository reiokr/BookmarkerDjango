from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from .views import MyObtainTokenPairView, RegisterView, UserDetail, UpdateUserCategories, BmListView, BmDetailView, BmListSearchView, AddBookmark, YouTubeList, GetVideoData, OptionsView, VideoCommentsView, RateVideoView, NextPageCommentsView, getRoutes,  RepliesView, RepliesNextPageView,  activate, ChannelPlaylistsView, AddPlaylistTOBookmarksView, LoadRelatedVideosView, ChannelNextPlaylistsView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView


urlpatterns = [
    path('', getRoutes),
    # path('token', TokenObtainPairView. as_view(), name='token_obtain_pair'),
    # path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/',  MyObtainTokenPairView.as_view(), name='my_token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('users/<int:pk>', UserDetail.as_view(), name='user_detail'),
    path('user/options', OptionsView.as_view(), name='options'),
    path('users/categories/<int:pk>',
         UpdateUserCategories.as_view(), name='user_categories'),
    path('bm', AddBookmark.as_view(), name='add_bookmark'),
    path('bm/video/<str:video_id>', GetVideoData.as_view()),
    path('bm/list/<str:list_id>', YouTubeList.as_view(), name='youtube_list'),
    path('bm/<int:pk>', BmDetailView.as_view(), name='bm_detail'),
    path('bm/comments/<str:video_id>/<str:order>',
         VideoCommentsView.as_view(), name='video_comments'),
    path('bm/comments/<str:video_id>/<str:page_token>/<str:order>',
         NextPageCommentsView.as_view()),
    path('bm/comment/replies/<str:parent_id>', RepliesView.as_view()),
    path('bm/comment/nextreplies/<str:parent_id>/<str:page_token>',
         RepliesNextPageView.as_view()),
    path('bm/rate/<str:video_id>', RateVideoView.as_view()),
    path('bm/<str:category>', BmListView.as_view(), name='bm_list'),
    path('bm/<str:category>/<search>',
         BmListSearchView.as_view(), name='bm_listsearch'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('channel/playlists/<str:channel_id>',
         ChannelPlaylistsView.as_view(), name='channel_playlists'),
    path('add-playlist-to-bookmarks/<str:pl_id>',
         AddPlaylistTOBookmarksView.as_view(), name='get_first_playlist_item'),
    path('channel/next-playlists/<str:channel_id>/<str:token>',
         ChannelNextPlaylistsView.as_view()),
    path('video/<str:video_id>/related-videos', LoadRelatedVideosView.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
