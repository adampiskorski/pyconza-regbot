import logging
import os
import sys

import regbot.commands  # noqa: F401
import regbot.events  # noqa: F401
from regbot import bot
from regbot.helpers import get_bool_env, get_str_env
from regbot.tasks import QuicketSync, WaferSync

TOKEN = get_str_env("DISCORD_TOKEN")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
FEATURE_WAFER_SYNC = get_bool_env("FEATURE_WAFER_SYNC")
FEATURE_QUICKET_SYNC = get_bool_env("FEATURE_QUICKET_SYNC")


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger()

if FEATURE_QUICKET_SYNC:
    bot.add_cog(QuicketSync(bot))
if FEATURE_WAFER_SYNC:
    bot.add_cog(WaferSync(bot))
bot.run(TOKEN)
