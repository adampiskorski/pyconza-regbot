"""Delete all unpinned posts"""

import os

import discord
from discord import Client, TextChannel

intents = discord.Intents.default()
client = Client(intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [
    764408838626607115,
]


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        assert isinstance(channel, TextChannel), "Need a valid text channel"
        print(f"Deleting messages for {channel.name}")
        await channel.purge(limit=1000)
        print("Messages deleted.")
    await client.close()


assert TOKEN is not None, "The DISCORD_TOKEN environment variable is required"
client.run(TOKEN)
