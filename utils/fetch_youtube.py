from googleapiclient.discovery import build
from django.conf import settings

api_key = settings.YOUTUBE_API_KEY

def fetch_Video(video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.videos().list(
        part='contentDetails,snippet,status,statistics, player, liveStreamingDetails,localizations',
        id=video_id,
    )
    response = request.execute()
    youtube.close()
    return response

