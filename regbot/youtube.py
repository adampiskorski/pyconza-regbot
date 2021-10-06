from typing import List
import arrow

import googleapiclient.discovery

from regbot.google import get_client_credentials
from regbot.helpers import get_str_env, to_discord_title_safe

YOUTUBE_PLAYLIST = get_str_env("YOUTUBE_PLAYLIST")
BROADCAST_CHANNELS: dict = {}


def get_youtube():
    """Returns an authenticated YouTube resource"""
    credentials = get_client_credentials()
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def save_channel_broadcast_map(channel_broadcast_map: dict):
    """Save a map of channels to broadcasts dictionaries to the in memory cache
    (BROADCAST_CHANNELS).
    """
    global BROADCAST_CHANNELS
    BROADCAST_CHANNELS = channel_broadcast_map


def get_all_broadcasts() -> List[dict]:
    """Get all the broadcasts for the playlist in the defined environment and return
    a list of ordered dictionaries defining them with the following keys:
        "id": Can be used to generate a link to the YouTube video
        "title"
        "description"
        "start_time": This is what the list is sorted by.
        "live_chat_id": For the Q&A command to use.
    """
    youtube = get_youtube()

    request = youtube.playlistItems().list(
        part="contentDetails", playlistId=YOUTUBE_PLAYLIST
    )
    response = request.execute()
    video_ids = [item["contentDetails"]["videoId"] for item in response["items"]]

    request = youtube.liveBroadcasts().list(part="snippet", id=",".join(video_ids))
    response = request.execute()
    broadcasts = []
    for item in response["items"]:
        start_time = arrow.get(item["snippet"]["scheduledStartTime"])
        broadcasts.append(
            {
                "id": item["id"],
                "title": to_discord_title_safe(item["snippet"]["title"]),
                "original_title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "start_time": start_time,
                "live_chat_id": item["snippet"]["liveChatId"],
                "over_hour_old": start_time < arrow.utcnow().shift(hours=1),
            }
        )

    broadcasts.sort(key=lambda broadcast: broadcast["start_time"])
    return broadcasts


def get_youtube_link(_id: str) -> str:
    """Get a YouTube link to the video with the given YouTube ID"""
    return f"https://youtu.be/{_id}"
