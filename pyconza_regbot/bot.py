import os

import discord

TOKEN = os.getenv("DISCORD_TOKEN")
assert TOKEN, "A discord token is expected!"
client = discord.Client()


@client.event
async def on_ready():
    print(f"{client.user} has connected to the following guilds:")
    for guild in client.guilds:
        print(f"{guild.name} ID: {guild.id}")


client.run(TOKEN)