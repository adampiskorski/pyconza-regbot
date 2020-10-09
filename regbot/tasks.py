from discord.ext import commands, tasks

from regbot.helpers import ServerInfo, get_int_env, log
from regbot.quicket import update_ticket_cache
from regbot.wafer import (
    all_upcoming_events,
    mark_as_announced,
    update_calendar_cache,
    update_speakers_cache,
)

QUICKET_CACHE_EXPIRE_MINUTES = get_int_env("QUICKET_CACHE_EXPIRE_MINUTES")
WAFER_CACHE_EXPIRE_MINUTES = get_int_env("WAFER_CACHE_EXPIRE_MINUTES")
WAFER_ANNOUNCE_INTERVAL_SECONDS = 30
WAFER_UPCOMING_EVENTS_BOUNDARY_MINUTES = 5


class QuicketSync(commands.Cog):
    """For keeping the quicket database in sync"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sync.start()

    @tasks.loop(minutes=QUICKET_CACHE_EXPIRE_MINUTES)
    async def sync(self):
        await log("Refreshing Quicket cache...")
        await update_ticket_cache()
        await log("Quicket cache refreshed.")

    @sync.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()


class WaferSync(commands.Cog):
    """For regularly syncing Wafer data"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sync_speakers.start()
        self.sync_events.start()
        self.announcement_loop.start()

    @tasks.loop(minutes=WAFER_CACHE_EXPIRE_MINUTES)
    async def sync_speakers(self):
        await log("Refreshing Wafer speakers cache...")
        await update_speakers_cache()
        await log("Wafer speakers cache refreshed.")

    @sync_speakers.before_loop
    async def before_sync_speakers(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=WAFER_CACHE_EXPIRE_MINUTES)
    async def sync_events(self):
        await log("Refreshing Wafer events cache...")
        await update_calendar_cache()
        await log("Wafer events cache refreshed.")

    @sync_events.before_loop
    async def before_sync_events(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=WAFER_ANNOUNCE_INTERVAL_SECONDS)
    async def announcement_loop(self):
        """Regular check for events to announce, then do so and cache to avoid repeating."""
        server_info = await ServerInfo.get()
        events = await all_upcoming_events(minutes=WAFER_UPCOMING_EVENTS_BOUNDARY_MINUTES)
        for event in events:
            await server_info.announcement_channel.send(
                f"{server_info.guild.default_role} The event **{event.name}** is "
                f"happening in {WAFER_UPCOMING_EVENTS_BOUNDARY_MINUTES} minutes!"
            )
            await mark_as_announced(event)

    @announcement_loop.before_loop
    async def before_announcement_loop(self):
        await self.bot.wait_until_ready()
