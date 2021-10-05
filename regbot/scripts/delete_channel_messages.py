"""Delete all unpinned posts"""
from discord import Client
import os

client = Client()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_IDS = [
    751787094514335754,
    762803925530574850,
    751801331408437268,
    751801352895856751,
    762797421104463894,
    763488120745492490,
    763699786183344178,
    763729726686363701,
    763739955133546496,
    763749211568341012,
    763756025915506708,
    764080459381735464,
    764092803160342538,
    764141648586211348,
    762791863069179925,
]


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    for channel_id in CHANNEL_IDS:
        channel = client.get_channel(channel_id)
        print(f"Deleting messages for {channel.name}")
        count_deleted = 0
        async for message in channel.history(limit=1000):
            await message.delete()
            print(f"deleting message {message.id}")
            count_deleted += 1
        print(f"{count_deleted} messages deleted.")
    await client.close()


client.run(TOKEN)
