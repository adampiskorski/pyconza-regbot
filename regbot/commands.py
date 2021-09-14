from discord.errors import Forbidden

from regbot import bot
from regbot.helpers import ServerInfo, get_bool_env, get_str_env, log
from regbot.quicket import get_ticket_by_barcode
from regbot.sheets import is_ticket_used, register_ticket
from regbot.wafer import is_barcode_belong_to_speaker

EVENT_NAME = get_str_env("EVENT_NAME")
FEATURE_REGISTRATION = get_bool_env("FEATURE_REGISTRATION")

if FEATURE_REGISTRATION:

    @bot.command("register")
    async def register(ctx, barcode: str):
        """Registers the calling user based on their Quicket ticket barcode number."""
        ticket = await get_ticket_by_barcode(barcode)
        server_info = await ServerInfo.get()
        member = server_info.guild.get_member(ctx.author.id)
        if member is None:
            return await log("None object member encountered in registration call.")
        assistance = (
            "If you need assistance, then please ask for assistance from the "
            f"{server_info.help_desk.mention} or a/an {server_info.registration.name}"
        )

        if ticket is None:
            await ctx.send(
                f"Sorry, I could not find a ticket with the barcode {barcode}. {assistance}"
            )
            return await log(
                f"{member.name} tried and failed to register a ticket with the "
                f"barcode {barcode} as it wasn't found!"
            )

        if await is_ticket_used(ticket):
            await ctx.send(
                f"Sorry, your ticket with barcode {barcode} was already used! {assistance}"
            )
            return await log(
                f"{member.name} tried and failed to register a ticket with the "
                f"barcode {barcode} as it was already registered!"
            )

        await member.add_roles(server_info.attendee)
        truncated_name = ticket.full_name[:32]  # Max nickname length on Discord
        try:
            await member.edit(nick=truncated_name)
        except Forbidden as e:
            await log(
                f"Failed to change the nickname of {member.mention}, due to {e.text}"
            )
        if len(ticket.full_name) > len(truncated_name):
            await ctx.send(
                "We apologize, but we had to truncate your full name on the discord server "
                "as it was over 32 characters. You are free to modify your own nickname by "
                f"right clicking on your user name on the {EVENT_NAME} server and selecting "
                "'Change Nickname'."
            )
            await log(f"{ticket.full_name} was truncated to {truncated_name}")

        await ctx.send(
            f"Registration successful! Thank you for registering for {EVENT_NAME}! "
            f"We hope that you enjoy your stay, {ticket.full_name}!"
        )
        await log(
            f"{member.mention} was successfully registered with ticket {ticket.barcode}"
        )

        if await is_barcode_belong_to_speaker(barcode):
            await member.add_roles(server_info.speaker)
            await log(f"{member.mention} has been given the speaker role!")
            await ctx.send(
                "I have also detected that you are a speaker and have assigned you that role."
            )

        await register_ticket(ticket, member)
