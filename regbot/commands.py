from discord.errors import Forbidden
from regbot import bot
from regbot.helpers import get_str_env, log, ServerInfo
from regbot.quicket import get_ticket_by_barcode

EVENT_NAME = get_str_env("EVENT_NAME")


@bot.command("register")
async def register(ctx, barcode: str):
    """Registers the calling user based on their Quicket ticket barcode number."""
    ticket = await get_ticket_by_barcode(barcode)
    server_info = await ServerInfo.get()
    member = server_info.guild.get_member(ctx.author.id)
    if ticket is None:
        await ctx.send(
            f"Sorry, I could not find a ticket with the barcode {barcode}. If you need "
            f"assistance, then please ask for assistance from the "
            f"{server_info.help_desk.mention} or a/an {server_info.registration.mention}"
        )
        return await log(
            f"{member.name} tried and failed to register a ticket with the "
            f"barcode {barcode}!"
        )

    await member.add_roles(server_info.attendee)
    truncated_name = ticket.full_name[:32]  # Max nickname length on Discord
    try:
        await member.edit(nick=truncated_name)
    except Forbidden as e:
        await log(f"Failed to change the nickname of {member.mention}, due to {e.text}")
    if len(ticket.full_name) > len(truncated_name):
        await ctx.send(
            "We apologize, but we had to truncate your full name on the discord server "
            "as it was over 32 characters. You are free to modify your own nickname by "
            f"right clicking on your user name on the {EVENT_NAME} server and selecting "
            "'Change Nickname'."
        )
        await log(f"{ticket.full_name} was truncated to {truncated_name}")
    await ctx.send(
        f"Registration successfull. Thank you for registering for {EVENT_NAME}! "
        "We hope that you enjoy your stay!"
    )
    await log(
        f"{member.mention} was successfully registered with ticket {ticket.barcode}"
    )
