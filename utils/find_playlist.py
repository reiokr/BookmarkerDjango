from django.conf import settings
from googleapiclient.discovery import build

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
  




def findPlaylistId(video_id, max_playlists=None):
    if not video_id:
        return None
    if max_playlists is None:
        max_playlists = getattr(settings, 'YT_PLAYLIST_AUTO_DETECT_MAX', 5)
    videoId = getVideoId(video_id)
    channelId = videoId['items'][0]['snippet']['channelId']
    playlists = getPlaylists(channelId)
    for i, pl in enumerate(playlists['items']):
        if max_playlists and i >= max_playlists:
            break
        playlist_id = pl['id']
        page_token = ""
        while page_token is not None:
            listitems = get_playlist_items(playlist_id, page_token)
            for item in listitems['items']:
                if item['contentDetails']['videoId'] == video_id:
                    return {
                        "playlist_id": playlist_id,
                        "position": item['snippet']['position'],
                        "publishedAt": item['snippet']['publishedAt'],
                        "channelId": item['snippet']['channelId'],
                        "title": item['snippet']['title'],
                        "description": item['snippet']['description'],
                        "thumbnails": item['snippet']['thumbnails'],
                        "channelTitle": item['snippet']['channelTitle'],
                        "videoOwnerChannelId": item['snippet'].get('videoOwnerChannelId'),
                        "videoOwnerChannelTitle": item['snippet'].get('videoOwnerChannelTitle'),
                    }
            page_token = listitems.get('nextPageToken')
    return None
