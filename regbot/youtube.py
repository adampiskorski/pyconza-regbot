from typing import Dict, List, Optional, Set

import arrow
import googleapiclient.discovery
from discord.channel import TextChannel

from regbot.google import get_client_credentials
from regbot.helpers import get_str_env, to_discord_description_safe, to_discord_title_safe

YOUTUBE_PLAYLIST = get_str_env("YOUTUBE_PLAYLIST")
CHANNEL_BROADCAST_MAP_TYPE = Dict[TextChannel, dict]
BROADCAST_CHANNELS: CHANNEL_BROADCAST_MAP_TYPE = {}
ANNOUNCED_BROADCASTS = set()


def get_youtube():
    """Returns an authenticated YouTube resource"""
    credentials = get_client_credentials()
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)


def save_channel_broadcast_map(channel_broadcast_map: CHANNEL_BROADCAST_MAP_TYPE):
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
    video_ids = []

    request = youtube.playlistItems().list(
        part="contentDetails", playlistId=YOUTUBE_PLAYLIST, maxResults=50
    )
    response = request.execute()
    video_ids = [item["contentDetails"]["videoId"] for item in response["items"]]

    request = youtube.liveBroadcasts().list(
        part="snippet", id=",".join(video_ids), maxResults=50
    )
    response = request.execute()
    broadcasts = []
    for item in response["items"]:
        start_time = arrow.get(item["snippet"]["scheduledStartTime"])
        broadcasts.append(
            {
                "id": item["id"],
                "title": to_discord_title_safe(item["snippet"]["title"]),
                "original_title": item["snippet"]["title"],
                "description": to_discord_description_safe(
                    item["snippet"]["description"]
                ),
                "original_description": item["snippet"]["description"],
                "start_time": start_time,
                "live_chat_id": item["snippet"]["liveChatId"],
                "over_hour_old": start_time.shift(hours=1) < arrow.utcnow(),
            }
        )

    broadcasts.sort(key=lambda broadcast: broadcast["start_time"])
    return broadcasts


def get_broadcast_channels() -> CHANNEL_BROADCAST_MAP_TYPE:
    """Get a dictionary mapping all broadcast channels to YouTube Broadcast information"""
    return BROADCAST_CHANNELS


def get_youtube_link(_id: str) -> str:
    """Get a YouTube link to the video with the given YouTube ID"""
    return f"https://youtu.be/{_id}"


def mark_broadcast_as_announced(channel: TextChannel) -> None:
    """Cache the channel, in order to mark it as announced."""
    global ANNOUNCED_BROADCASTS
    ANNOUNCED_BROADCASTS.add(channel)


async def all_upcoming_broadcasts(
    seconds: Optional[int] = None,
) -> Set[TextChannel]:
    """All upcoming broadcast channels that have yet to be announced. If minutes are
    given, then it will only mention the events comming up in the given number of minutes.
    """
    channels = set()
    now = arrow.utcnow()
    for channel, broadcast in BROADCAST_CHANNELS.items():
        diff = (broadcast["start_time"] - now).total_seconds()
        if (
            channel not in ANNOUNCED_BROADCASTS
            and diff > 0
            and (seconds and diff <= seconds or not seconds)
        ):
            channels.add(channel)
    return channels
