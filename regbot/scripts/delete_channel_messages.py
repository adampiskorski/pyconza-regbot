"""Delete all unpinned posts"""
from discord import Client
import os

client = Client()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [
    764408838626607115,
]


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        assert channel is not None, "Need valid channel"
        print(f"Deleting messages for {channel.name}")
        await channel.purge(limit=1000)
        print("Messages deleted.")
    await client.close()


client.run(TOKEN)
