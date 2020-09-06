import logging
import os
import sys

from regbot import bot
import regbot.events  # noqa: F401
import regbot.commands  # noqa: F401
from regbot.helpers import get_str_env

TOKEN = get_str_env("DISCORD_TOKEN")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger()

bot.run(TOKEN)
