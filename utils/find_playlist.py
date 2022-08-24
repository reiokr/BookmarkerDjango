from googleapiclient.discovery import build
from django.conf import settings


api_key = settings.YOUTUBE_API_KEY


def getVideoId(video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.videos().list(
        part='snippet',
        id=video_id,
    )
    response = request.execute()
    youtube.close()
    return response


def getPlaylists(channelId):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.playlists().list(
        part='contentDetails',
        channelId=channelId,
        maxResults=50,

    )
    response = request.execute()
    youtube.close()
    return response


def get_playlist_items(id, pageToken):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.playlistItems().list(
        part='contentDetails,snippet',
        playlistId=id,
        maxResults=50,
        pageToken=pageToken

    )
    response = request.execute()
    youtube.close()
    return response


def get_playlist_item(id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=id,
        maxResults=1,
    )
    response = request.execute()
    youtube.close()
    return response
  




def findPlaylistId(video_id):
    videoId = getVideoId(video_id)
    channelId = videoId['items'][0]['snippet']['channelId']
    playlists = getPlaylists(channelId)
    for l in playlists['items']:
        listitems = get_playlist_items(l['id'])
        for item in listitems['items']:
            if item['contentDetails']['videoId'] == video_id:
                return item['snippet']
            else:
                return None
