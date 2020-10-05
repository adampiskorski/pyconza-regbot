from asyncio import sleep

from regbot import bot
from regbot.helpers import ServerInfo, get_str_env, log

EVENT_NAME = get_str_env("EVENT_NAME")


@bot.event
async def on_ready():
    await log(f"{bot.user.name} has connected to the following guilds:")
    for guild in bot.guilds:
        await log(f"{guild.name}, ID: {guild.id}")


@bot.event
async def on_member_join(member):
    server_info = await ServerInfo.get()
    await log(f"{member.mention} has joined the server!")
    channel = member.dm_channel
    if channel is None:
        channel = await member.create_dm()
    else:
        await log(f"Could not create DM channel for {member.mention}!")
    await member.dm_channel.send(f"Welcome {member.name} to {EVENT_NAME}!")
    await member.dm_channel.send(
        f"I am the registration bot for {EVENT_NAME}. Simply "
        "say `!register <Quicket Ticket barcode number>` without the `<`/`>`, and I "
        "will check in your ticket and give you the appropriate permissions on the "
        "discord server! You can also use the `!help` command for more options."
    )
    await member.dm_channel.send(
        f"If you need any assistance, then please do not hesitate to ask for it at the"
        f" {server_info.help_desk.mention}, or from an organizer."
    )
    await log(f"{member.mention} has been greeted via DM.")
    # Needed, otherwise a user who can't see history in a channel won't see a message
    # posted there if it's posted too soon after joining.
    await sleep(7)
    await server_info.welcome_channel.send(
        f"Welcome {member.mention} to {EVENT_NAME}! Please register your ticket with me "
        "in the Direct Message channel that I created with you..."
    )


@bot.event
async def on_command_error(ctx, error):
    await log(
        f"`{ctx.invoked_with}` command got message `{ctx.message.clean_content}` from "
        f"{ctx.author.mention} that caused error: `{error}`"
    )
