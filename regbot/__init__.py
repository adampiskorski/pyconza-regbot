__version__ = "0.1.0"


import discord
from discord.ext import commands
from rich import pretty, traceback

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", description="Registration bot", intents=intents)
pretty.install()
traceback.install(show_locals=True)
