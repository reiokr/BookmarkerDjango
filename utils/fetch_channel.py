from googleapiclient.discovery import build
from django.conf import settings


api_key = settings.YOUTUBE_API_KEY


def search_related_videos(video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part='snippet',
        relatedToVideoId=video_id,
        maxResults=50,
        type="video, playlist"
    )
    response = request.execute()
    youtube.close()
    return response


def fetch_channel_playlists(channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.playlists().list(
        part='contentDetails, id, localizations, snippet, status,player',
        channelId=channel_id,
        maxResults=50
    )
    response = request.execute()
    youtube.close()
    return response


def fetch_channel_next_playlists(channel_id, token):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.playlists().list(
        part='contentDetails, id, localizations, snippet, status,player',
        channelId=channel_id,
        maxResults=50,
        pageToken=token
    )
    response = request.execute()
    youtube.close()
    return response
