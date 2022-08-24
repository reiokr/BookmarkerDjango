from googleapiclient.discovery import build
from django.conf import settings


api_key = settings.YOUTUBE_API_KEY


def fetch_video_comments(video_id, order='relevance'):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(
        part='snippet,replies',
        videoId=video_id,
        order=order
    )
    response = request.execute()
    youtube.close()
    return response


def fetch_next_comments(video_id,  pageToken, order='relevance'):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.commentThreads().list(
        part='snippet,replies',
        videoId=video_id,
        order=order,
        pageToken=pageToken,
        maxResults=100
    )
    response = request.execute()
    youtube.close()
    return response


def get_replies(top_comment_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.comments().list(
        part='snippet',
        maxResults=100,
        parentId=top_comment_id,

    )
    response = request.execute()
    youtube.close()
    return response


def get_next_replies(top_comment_id, token):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.comments().list(
        part='snippet',
        maxResults=100,
        parentId=top_comment_id,
        pageToken=token,

    )
    response = request.execute()
    return response
