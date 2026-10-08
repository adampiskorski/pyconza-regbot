"""Shared test configuration.

The regbot modules read environmental variables at import time, so the
deterministic test values below are set before anything imports regbot.
"""

import os

# The environmental variables that regbot reads at import time. The channel
# IDs are placeholders: SimCord generates its own IDs, and the `server`
# fixture points regbot at the real generated ones via monkeypatching.
TEST_ENV = {
    "EVENT_NAME": "PyConZA Test",
    "DISCORD_TOKEN": "test-token",
    "DISCORD_GUILD_ID": "1111111111111111111",
    "DISCORD_LOG_CHANNEL_ID": "1",
    "DISCORD_HELPDESK_CHANNEL_ID": "2",
    "DISCORD_WELCOME_CHANNEL_ID": "3",
    "DISCORD_ANNOUNCEMENT_CHANNEL_ID": "4",
    "DISCORD_ANNOUNCEMENT_STAGING_CHANNEL_ID": "5",
    "DISCORD_YOUTUBE_CATEGORY": "6",
    "DISCORD_REGISTERED_ROLE_NAME": "Attendee",
    "DISCORD_REGISTRATION_ROLE": "Registration",
    "DISCORD_ORGANIZER_ROLE": "Organizer",
    "DISCORD_SPEAKER_ROLE": "Speaker",
    "DISCORD_SPONSOR_PATRON_ROLE": "Patron Sponsor",
    "DISCORD_SPONSOR_SILVER_ROLE": "Silver Sponsor",
    "DISCORD_SPONSOR_GOLD_ROLE": "Gold Sponsor",
    # Quicket (tests fake the HTTP layer)
    "QUICKET_USER_TOKEN": "test-user-token",
    "QUICKET_API_KEY": "test-api-key",
    "QUICKET_CACHE_EXPIRE_MINUTES": "60",
    "QUICKET_EVENT_ID": "12345",
    # Google (tests fake the worksheet layer, so these are never really used)
    "GOOGLE_SHEET_ID": "test-registration-sheet",
    "GOOGLE_SHEET_WORKSHEET_NAME": "Registrations",
    "QUIZ_GOOGLE_SHEET_ID": "test-quiz-sheet",
    "QUIZ_GOOGLE_SHEET_WORKSHEET_NAME": "Quiz",
    "GOOGLE_PROJECT_ID": "test-project",
    "GOOGLE_PRIVATE_KEY_ID": "test-key-id",
    "GOOGLE_PRIVATE_KEY": "test-private-key",
    "GOOGLE_CLIENT_EMAIL": "test@example.com",
    "GOOGLE_CLIENT_ID": "1234567890",
    "GOOGLE_CLIENT_X509_CERT_URL": "https://example.com/cert",
    "GOOGLE_OAUTH_CLIENT_ID": "test-oauth-client-id",
    "GOOGLE_OAUTH_CLIENT_SECRET": "test-oauth-secret",
    # YouTube (tests fake the API resource)
    "YOUTUBE_PLAYLIST": "test-playlist",
    # Wafer (tests fake the HTTP layer)
    "WAFER_USERNAME": "test-user",
    "WAFER_PASSWORD": "test-password",
    "WAFER_BASE_URL": "https://wafer.example.com",
    "WAFER_TICKETS_ENDPOINT": "api/tickets/",
    "WAFER_TALKS_ENDPOINT": "api/talks/",
    "WAFER_ICS_ENDPOINT": "schedule.ics",
    "WAFER_CACHE_EXPIRE_MINUTES": "60",
    # Feature flags (SimCord tests override these via create_bot parameters)
    "FEATURE_REGISTRATION": "true",
    "FEATURE_YOUTUBE": "true",
    "FEATURE_QUIZ": "true",
    "FEATURE_REPOST_ANNOUNCE": "true",
    "FEATURE_QUICKET_SYNC": "false",
    "FEATURE_WAFER_SYNC": "false",
}
os.environ.update(TEST_ENV)

import pytest  # noqa: E402


def make_simcord_bot(**overrides):
    """Build a fresh bot, as required by SimCord (one per test).

    All user-facing features are on. The background sync cogs are off by
    default; tasks tests enable them (and fake their data sources) so that
    the cogs are added by `on_ready`, exactly like in production.
    """
    from regbot import create_bot

    flags = {
        "feature_registration": True,
        "feature_youtube": True,
        "feature_youtube_sync": False,
        "feature_quiz": True,
        "feature_repost_announce": True,
        "feature_quicket_sync": False,
        "feature_wafer_sync": False,
    }
    flags.update(overrides)
    return create_bot(**flags)


@pytest.fixture
def simcord_bot():
    return make_simcord_bot()


@pytest.fixture(autouse=True)
def _clean_module_state(monkeypatch):
    """Reset all of regbot's module-level caches around every test."""
    import regbot.helpers as helpers
    import regbot.quicket as quicket
    import regbot.wafer as wafer
    import regbot.youtube as youtube

    monkeypatch.setattr(helpers, "SERVER_INFO_CACHE", None)
    monkeypatch.setattr(quicket, "TICKETS", {})
    monkeypatch.setattr(wafer, "SPEAKERS_TICKETS", set())
    monkeypatch.setattr(wafer, "EVENTS_CACHE", set())
    monkeypatch.setattr(wafer, "ANNOUNCED_EVENT_NAMES", set())
    monkeypatch.setattr(youtube, "BROADCAST_CHANNELS", {})
    monkeypatch.setattr(youtube, "ANNOUNCED_BROADCASTS", set())


class Server:
    """The virtual PyConZA discord server: everything `ServerInfo` looks up."""

    def __init__(self, env, guild, roles, channels):
        self.env = env
        self.guild = guild
        self.roles = roles
        (self.log_channel, self.help_desk, self.welcome_channel) = channels[:3]
        (self.announcement_channel, self.announcement_staging_channel) = channels[3:5]
        self.youtube_category = channels[5]

    def add_member(self, name):
        """Add a member to the server, returning the SimCord actor."""
        return self.guild.add_member(self.env.create_user(name))


@pytest.fixture
def server(simcord_env, monkeypatch):
    """Build the virtual PyConZA server that `ServerInfo.get()` expects."""
    import regbot.helpers as helpers

    guild = simcord_env.create_guild("PyConZA Test", id=int(TEST_ENV["DISCORD_GUILD_ID"]))
    roles = {
        "attendee": guild.create_role(helpers.ATTENDEE_ROLE),
        "registration": guild.create_role(helpers.REGISTRATION_ROLE),
        "organizer": guild.create_role(helpers.ORGANIZER_ROLE),
        "speaker": guild.create_role(helpers.SPEAKER_ROLE),
        "patron_sponsor": guild.create_role(helpers.SPONSOR_PATRON_ROLE),
        "silver_sponsor": guild.create_role(helpers.SPONSOR_SILVER_ROLE),
        "gold_sponsor": guild.create_role(helpers.SPONSOR_GOLD_ROLE),
    }
    channels = [
        guild.create_text_channel("bot-log"),
        guild.create_text_channel("help-desk"),
        guild.create_text_channel("welcome"),
        guild.create_text_channel("announcements"),
        guild.create_text_channel("announcement-staging"),
        guild.create_category("youtube-talks"),
    ]
    # regbot reads the channel IDs from the (import time) module constants in
    # helpers.py, so point them at the generated SimCord channel IDs.
    for name, channel in zip(
        (
            "LOG_CHANNEL",
            "HELP_DESK",
            "WELCOME_CHANNEL",
            "ANNOUNCEMENT_CHANNEL",
            "ANNOUNCEMENT_STAGING_CHANNEL",
            "YOUTUBE_CATEGORY",
        ),
        channels,
        strict=True,
    ):
        monkeypatch.setattr(helpers, name, channel.id)

    return Server(simcord_env, guild, roles, channels)
