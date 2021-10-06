__version__ = "0.1.0"


from discord.ext import commands
import discord

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", description="Registration bot", intents=intents)
