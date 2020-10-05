import logging
import os
import sys

import regbot.commands  # noqa: F401
import regbot.events  # noqa: F401
from regbot import bot
from regbot.helpers import get_str_env
from regbot.tasks import QuicketSync, WaferSync

TOKEN = get_str_env("DISCORD_TOKEN")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger()

bot.add_cog(QuicketSync(bot))
bot.add_cog(WaferSync(bot))
bot.run(TOKEN)
