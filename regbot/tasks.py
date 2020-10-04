from regbot.quicket import update_ticket_cache
from discord.ext import commands, tasks

from regbot.helpers import get_int_env, log

CACHE_EXPIRE_MINUTES = get_int_env("QUICKET_CACHE_EXPIRE_MINUTES")


class QuicketSync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sync.start()

    @tasks.loop(minutes=CACHE_EXPIRE_MINUTES)
    async def sync(self):
        await log("Quicket ticket cache expired, downloading...")
        await update_ticket_cache()

    @sync.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()
