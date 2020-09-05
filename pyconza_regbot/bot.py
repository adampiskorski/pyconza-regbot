import logging
import os
import sys

import discord

from roles import ROLES


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

TOKEN = os.getenv("DISCORD_TOKEN")
assert TOKEN, "A discord token is expected!"


client = discord.Client()


@client.event
async def on_ready():
    logging.info(f"{client.user} has connected to the following guilds:")
    for guild in client.guilds:
        logging.info(f"{guild.name} ID: {guild.id}")


@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f"Welcome {member.name} to PyConZA 2020!")


client.run(TOKEN)
