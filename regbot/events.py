from regbot import bot
from regbot.helpers import log
from regbot.helpers import get_str_env


EVENT_NAME = get_str_env("EVENT_NAME")


@bot.event
async def on_ready():
    await log(f"{bot.user.name} has connected to the following guilds:")
    for guild in bot.guilds:
        await log(f"{guild.name}, ID: {guild.id}")


@bot.event
async def on_member_join(member):
    channel = member.dm_channel()
    if channel is None:
        channel = await member.create_dm()
    await member.dm_channel.send(f"Welcome {member.name} to {EVENT_NAME}!")


@bot.event
async def on_command_error(ctx, error):
    await log(
        f"`{ctx.invoked_with}` command got message `{ctx.message.clean_content}` from "
        f"{ctx.author.mention} that caused error: `{error}`"
    )
