"""Unit tests for the YouTube broadcasts cache and helpers."""

import arrow

import regbot.youtube as youtube
from regbot.youtube import (
    all_upcoming_broadcasts,
    get_all_broadcasts,
    get_youtube_link,
    save_channel_broadcast_map,
)


class FakeYouTubeResource:
    """Serves canned playlist and broadcast responses to get_all_broadcasts."""

    def __init__(self, video_ids, broadcasts):
        self._video_ids = video_ids
        self._broadcasts = broadcasts
        self._mode = None

    def playlistItems(self):
        self._mode = "playlist"
        return self

    def liveBroadcasts(self):
        self._mode = "broadcasts"
        return self

    def list(self, **kwargs):
        fake = self

        class Request:
            def execute(self):
                if fake._mode == "playlist":
                    return {
                        "items": [
                            {"contentDetails": {"videoId": video_id}}
                            for video_id in fake._video_ids
                        ]
                    }
                return {"items": fake._broadcasts}

        return Request()


def broadcast(video_id, title, start_time, description="A great talk."):
    """A liveBroadcasts API item."""
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "description": description,
            "scheduledStartTime": start_time.isoformat(),
            "liveChatId": f"live-chat-{video_id}",
        },
    }


def serve_broadcasts(monkeypatch, broadcasts):
    """Fake the YouTube API to serve the given broadcasts."""
    video_ids = [item["id"] for item in broadcasts]
    resource = FakeYouTubeResource(video_ids, broadcasts)
    monkeypatch.setattr(youtube, "get_youtube", lambda: resource)


class TestGetAllBroadcasts:
    async def test_broadcasts_become_channel_ready_descriptions(self, monkeypatch):
        start = arrow.utcnow().shift(days=1)
        serve_broadcasts(
            monkeypatch,
            [broadcast("vid1", "What's new in Python 3.14?", start)],
        )

        (result,) = get_all_broadcasts()

        assert result["id"] == "vid1"
        assert result["title"] == "whats-new-in-python-314"  # discord-safe
        assert result["original_title"] == "What's new in Python 3.14?"
        assert result["live_chat_id"] == "live-chat-vid1"
        assert result["start_time"] == start

    async def test_broadcasts_are_sorted_by_start_time(self, monkeypatch):
        later = arrow.utcnow().shift(hours=3)
        sooner = arrow.utcnow().shift(hours=1)
        serve_broadcasts(
            monkeypatch,
            [
                broadcast("later", "Later Talk", later),
                broadcast("sooner", "Sooner Talk", sooner),
            ],
        )

        assert [b["id"] for b in get_all_broadcasts()] == ["sooner", "later"]

    async def test_broadcasts_that_started_over_an_hour_ago_are_flagged(
        self, monkeypatch
    ):
        serve_broadcasts(
            monkeypatch,
            [
                broadcast("old", "Old Talk", arrow.utcnow().shift(hours=-2)),
                broadcast("new", "New Talk", arrow.utcnow().shift(hours=1)),
            ],
        )

        results = {b["id"]: b for b in get_all_broadcasts()}

        assert results["old"]["over_hour_old"] is True
        assert results["new"]["over_hour_old"] is False


class TestGetYouTubeLink:
    def test_link_contains_the_video_id(self):
        assert get_youtube_link("vid1") == "https://youtu.be/vid1"


class FakeChannel:
    """Broadcast channels are only used as dictionary keys in these tests."""


class TestUpcomingBroadcasts:
    @staticmethod
    def broadcast_starting(**shift):
        return {
            "id": "vid1",
            "start_time": arrow.utcnow().shift(**shift),
            "live_chat_id": "lc",
        }

    async def test_channels_with_broadcasts_starting_soon_are_upcoming(self, monkeypatch):
        channel = FakeChannel()
        soon = self.broadcast_starting(seconds=15)
        monkeypatch.setattr(youtube, "BROADCAST_CHANNELS", {channel: soon})

        assert await all_upcoming_broadcasts(seconds=20) == {channel}

    async def test_channels_beyond_the_boundary_are_not_upcoming(self, monkeypatch):
        channel = FakeChannel()
        monkeypatch.setattr(
            youtube, "BROADCAST_CHANNELS", {channel: self.broadcast_starting(minutes=5)}
        )

        assert await all_upcoming_broadcasts(seconds=20) == set()

    async def test_announced_channels_are_not_announced_again(self, monkeypatch):
        channel = FakeChannel()
        monkeypatch.setattr(
            youtube, "BROADCAST_CHANNELS", {channel: self.broadcast_starting(seconds=15)}
        )
        youtube.ANNOUNCED_BROADCASTS.add(channel)

        assert await all_upcoming_broadcasts(seconds=20) == set()

    async def test_started_broadcasts_are_not_upcoming(self, monkeypatch):
        channel = FakeChannel()
        monkeypatch.setattr(
            youtube, "BROADCAST_CHANNELS", {channel: self.broadcast_starting(minutes=-5)}
        )

        assert await all_upcoming_broadcasts(seconds=20) == set()


class TestChannelBroadcastMap:
    def test_the_saved_map_is_what_get_broadcast_channels_returns(self):
        channel = FakeChannel()
        broadcast_map = {channel: {"id": "vid1"}}
        save_channel_broadcast_map(broadcast_map)

        assert youtube.get_broadcast_channels() == broadcast_map
