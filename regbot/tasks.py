from regbot.wafer import update_speakers_cache
from discord.ext import commands, tasks

from regbot.helpers import get_int_env, log
from regbot.quicket import update_ticket_cache

QUICKET_CACHE_EXPIRE_MINUTES = get_int_env("QUICKET_CACHE_EXPIRE_MINUTES")
WAFER_CACHE_EXPIRE_MINUTES = get_int_env("WAFER_CACHE_EXPIRE_MINUTES")


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

    @tasks.loop(minutes=WAFER_CACHE_EXPIRE_MINUTES)
    async def sync_speakers(self):
        await log("Refreshing Wafer speakers cache...")
        await update_speakers_cache()
        await log("Wafer speakers cache refreshed.")

    @sync_speakers.before_loop
    async def before_sync_speakers(self):
        await self.bot.wait_until_ready()
