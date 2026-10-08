"""Integration tests for the background task loops.

The cache-sync loops (Quicket/Wafer) are simple pass-throughs to functions
covered by unit tests; the interesting behavior lives in the announcement
loops and the YouTube channel housekeeping.

These tests enable the sync cogs via the bot's feature flags, so the cogs are
added by `on_ready` exactly like in production. The loop bodies
(`sync_channels`, `announce_*`) are called directly for deterministic
behavior, while `env.advance_time()` tests prove that the loops themselves
are wired up correctly.
"""

import arrow
import discord.utils
import pytest
from ics import Event

import regbot.events as events
import regbot.tasks as tasks
import regbot.wafer as wafer

from .conftest import make_simcord_bot
from .fakes import do_nothing

WAFER_ANNOUNCE_INTERVAL_SECONDS = tasks.WAFER_ANNOUNCE_INTERVAL_SECONDS
YOUTUBE_CREATE_CHANNELS_MINUTES = tasks.YOUTUBE_CREATE_CHANNELS_MINUTES
YOUTUBE_ANNOUNCE_INTERVAL_SECONDS = tasks.YOUTUBE_ANNOUNCE_INTERVAL_SECONDS


def get_talk_channel(simcord_bot, server, name):
    """The real discord channel with the given name in the YouTube category."""
    category = simcord_bot.get_channel(server.youtube_category.id)
    return discord.utils.get(category.channels, name=name)


class TestWaferAnnouncements:
    @pytest.fixture
    def simcord_bot(self, monkeypatch):
        """The bot with the Wafer sync cog on and its cache refreshes faked."""
        monkeypatch.setattr(tasks, "update_speakers_cache", do_nothing)
        monkeypatch.setattr(tasks, "update_calendar_cache", do_nothing)
        return make_simcord_bot(feature_wafer_sync=True)

    async def test_upcoming_events_are_announced_with_their_channel(
        self, simcord_env, server
    ):
        wafer.EVENTS_CACHE.add(
            Event(name="Opening Ceremony", begin=arrow.utcnow().shift(minutes=4))
        )
        channel = server.guild.create_text_channel("opening-ceremony")

        await simcord_env.advance_time(WAFER_ANNOUNCE_INTERVAL_SECONDS + 1)

        announcement = server.announcement_channel.last_message.content
        assert "The event **Opening Ceremony** is happening in 5 minutes!" in (
            announcement
        )
        assert channel.mention in announcement

    async def test_events_are_not_announced_twice(self, simcord_env, server):
        wafer.EVENTS_CACHE.add(
            Event(name="Opening Ceremony", begin=arrow.utcnow().shift(minutes=4))
        )
        await simcord_env.advance_time(WAFER_ANNOUNCE_INTERVAL_SECONDS + 1)
        announced = server.announcement_channel.last_message

        await simcord_env.advance_time(60)  # two more loop iterations

        assert server.announcement_channel.last_message == announced


def youtube_broadcast(video_id, title, **shift):
    """A broadcast dict as produced by youtube.get_all_broadcasts."""
    return {
        "id": video_id,
        "title": title.lower().replace(" ", "-"),
        "original_title": title,
        "description": f"Description of {title}",
        "original_description": f"Description of {title}",
        "start_time": arrow.utcnow().shift(**shift),
        "live_chat_id": f"live-chat-{video_id}",
        "over_hour_old": False,
    }


@pytest.fixture
def broadcasts(monkeypatch):
    """The broadcasts that get_all_broadcasts will report (starts empty)."""
    current = []
    monkeypatch.setattr(tasks, "get_all_broadcasts", lambda: current)
    return current


class TestYouTubeChannelSync:
    @pytest.fixture
    def simcord_bot(self, monkeypatch, broadcasts):
        """The bot with the YouTube sync cog on and its data sources faked."""
        # The oAuth flow is out of scope: pretend we already have credentials.
        monkeypatch.setattr(events, "get_client_credentials", lambda: None)
        return make_simcord_bot(feature_youtube_sync=True)

    async def test_a_channel_is_created_per_broadcast_with_pinned_details(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk"))

        await simcord_bot.get_cog("YouTubeVideoSync").sync_channels()

        channel = get_talk_channel(simcord_bot, server, "opening-talk")
        assert channel is not None
        assert channel.topic == "Description of Opening Talk"
        pinned = [message.content for message in await channel.pins()]
        assert "__**Talk title**__: Opening Talk" in pinned
        assert "__**Talk link**__: https://youtu.be/vid1" in pinned
        assert "__**Talk description**__:\nDescription of Opening Talk" in pinned

    async def test_existing_channels_are_updated_not_duplicated(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk"))
        cog = simcord_bot.get_cog("YouTubeVideoSync")
        await cog.sync_channels()

        broadcasts[0] = youtube_broadcast("vid1", "Opening Talk")
        broadcasts[0]["description"] = "Updated description"
        await cog.sync_channels()

        category = simcord_bot.get_channel(server.youtube_category.id)
        channels = [c for c in category.channels if c.name == "opening-talk"]
        assert len(channels) == 1
        assert channels[0].topic == "Updated description"

    async def test_channels_without_a_broadcast_are_deleted(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.extend(
            [
                youtube_broadcast("vid1", "Opening Talk"),
                youtube_broadcast("vid2", "Cancelled Talk"),
            ]
        )
        cog = simcord_bot.get_cog("YouTubeVideoSync")
        await cog.sync_channels()

        del broadcasts[1]
        await cog.sync_channels()

        assert get_talk_channel(simcord_bot, server, "opening-talk") is not None
        assert get_talk_channel(simcord_bot, server, "cancelled-talk") is None

    async def test_duplicate_channels_are_purged(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        server.guild.create_text_channel("opening-talk", category=server.youtube_category)
        server.guild.create_text_channel("opening-talk", category=server.youtube_category)
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk"))

        await simcord_bot.get_cog("YouTubeVideoSync").sync_channels()

        category = simcord_bot.get_channel(server.youtube_category.id)
        channels = [c for c in category.channels if c.name == "opening-talk"]
        assert len(channels) == 1

    async def test_the_loop_drives_the_channel_sync(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk"))

        await simcord_env.advance_time(60 * YOUTUBE_CREATE_CHANNELS_MINUTES)

        assert get_talk_channel(simcord_bot, server, "opening-talk") is not None


class TestYouTubeAnnouncements:
    @pytest.fixture
    def simcord_bot(self, monkeypatch, broadcasts):
        """The bot with the YouTube sync cog on and its data sources faked."""
        monkeypatch.setattr(events, "get_client_credentials", lambda: None)
        return make_simcord_bot(feature_youtube_sync=True)

    async def test_broadcasts_starting_now_are_announced_in_their_channel(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk", seconds=15))
        cog = simcord_bot.get_cog("YouTubeVideoSync")
        await cog.sync_channels()  # creates the channel and links the broadcast
        channel = get_talk_channel(simcord_bot, server, "opening-talk")

        await cog.announce_starting_broadcasts()

        messages = [m.content async for m in channel.history(limit=None)]
        assert any("This talk is starting now!" in content for content in messages)
        assert any("https://youtu.be/vid1" in content for content in messages)
        assert any("!question your question text here" in c for c in messages)

    async def test_broadcasts_are_not_announced_twice(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk", seconds=15))
        cog = simcord_bot.get_cog("YouTubeVideoSync")
        await cog.sync_channels()
        await cog.announce_starting_broadcasts()
        channel = get_talk_channel(simcord_bot, server, "opening-talk")
        announced = [message async for message in channel.history(limit=None)]

        await cog.announce_starting_broadcasts()

        assert [message async for message in channel.history(limit=None)] == announced

    async def test_the_loop_drives_the_announcements(
        self, simcord_env, simcord_bot, server, broadcasts
    ):
        broadcasts.append(youtube_broadcast("vid1", "Opening Talk", seconds=15))
        cog = simcord_bot.get_cog("YouTubeVideoSync")
        await cog.sync_channels()
        channel = get_talk_channel(simcord_bot, server, "opening-talk")

        await simcord_env.advance_time(YOUTUBE_ANNOUNCE_INTERVAL_SECONDS)

        messages = [m.content async for m in channel.history(limit=None)]
        assert any("This talk is starting now!" in content for content in messages)
