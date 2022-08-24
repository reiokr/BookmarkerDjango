from googleapiclient.discovery import build
import google_auth_oauthlib.flow
import googleapiclient.errors
import os
from django.conf import settings


api_key = settings.YOUTUBE_API_KEY
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

def rate_video(video_id, rating='like'):
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.videos().rate(
        id=video_id,
        rating=rating
    )
    request.execute()
    youtube.close()

