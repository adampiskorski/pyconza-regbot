from discord.errors import Forbidden
from googleapiclient.errors import HttpError

from regbot import bot
from regbot.youtube import get_broadcast_channels, get_youtube
from regbot.helpers import ServerInfo, get_bool_env, get_str_env, log
from regbot.quicket import get_ticket_by_barcode
from regbot.sheets import is_ticket_used, register_ticket
from regbot.wafer import is_barcode_belong_to_speaker

EVENT_NAME = get_str_env("EVENT_NAME")
FEATURE_REGISTRATION = get_bool_env("FEATURE_REGISTRATION")
FEATURE_YOUTUBE = get_bool_env("FEATURE_YOUTUBE")
BASE_URL = "https://youtube.googleapis.com/youtube/v3/"
MESSAGES_URL = "liveChat/messages"
LIVE_BROADCAST_URL = "liveBroadcasts"

if FEATURE_REGISTRATION:

    @bot.command("register")
    async def register(ctx, barcode: str):
        """Registers the calling user based on their Quicket ticket barcode number."""
        if ctx.channel.type.name != "private":
            await ctx.message.delete()
        ticket = await get_ticket_by_barcode(barcode)
        server_info = await ServerInfo.get()
        member = server_info.guild.get_member(ctx.author.id)
        if member is None:
            return await log("None object member encountered in registration call.")
        assistance = (
            "\nIf you need assistance, then please ask for assistance from the "
            f"{server_info.help_desk.mention} or a/an {server_info.registration.name}"
        )

        if ticket is None:
            await ctx.send(
                f"Sorry {member.name}, I could not find a ticket with the given barcode. "
                f"{assistance}"
            )
            return await log(
                f"{member.name} tried and failed to register a ticket with the "
                f"barcode {barcode} as it wasn't found!"
            )

        if await is_ticket_used(ticket):
            await ctx.send(
                f"Sorry {member.name}, your ticket with the given barcode was already "
                f"used! {assistance}"
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
                f"We apologize {member.name}, but we had to truncate your full name on the"
                " discord server as it was over 32 characters. You are free to modify your"
                f" own nickname by right clicking on your user name on the {EVENT_NAME} "
                "server and selecting 'Change Nickname'."
            )
            await log(f"{ticket.full_name} was truncated to {truncated_name}")

        await ctx.send(
            f"Registration successful! Thank you for registering for {EVENT_NAME}! "
            f"We hope that you enjoy your stay, {ticket.full_name}!"
        )
        await log(
            f"{member.mention} was successfully registered with ticket {ticket.barcode}"
        )

        await register_ticket(ticket, member)

        if await is_barcode_belong_to_speaker(barcode):
            await member.add_roles(server_info.speaker)
            await log(f"{member.mention} has been given the speaker role.")
            await ctx.send(
                "I have also detected that you are a speaker and have assigned you that role."
            )

        ticket_type = ticket.type.lower()
        if "sponsor" in ticket_type:
            for level, role in (
                ("gold", server_info.gold_sponsor),
                ("silver", server_info.silver_sponsor),
                ("patron", server_info.patron_sponsor),
            ):
                if level in ticket_type:
                    await member.add_roles(role)
                    await log(
                        f"{member.mention} has been given the " f"{role.name} role."
                    )
                    await ctx.send(
                        "I have also detected that you are a sponsor and have assigned you "
                        "that role."
                    )
                    break


if FEATURE_YOUTUBE:

    @bot.command("question")
    async def question(ctx, *question_words):
        """Echo a question to YouTube"""
        if not question_words:
            await ctx.send(
                f"Thank you for your intention to ask a question {ctx.author.mention}, "
                "however it doesn't look like you gave us a question to ask!"
            )

        channels = get_broadcast_channels()
        if ctx.channel not in channels:
            await ctx.send(
                f"Thank you for your question {ctx.author.mention}, however this is "
                "not a channel dealing with YouTube Broadcasts."
            )
            return

        question = " ".join(question_words)
        live_chat_id = channels[ctx.channel]["live_chat_id"]

        youtube = get_youtube()
        question = f"Question from {ctx.author.display_name}: {question}"
        len_question = len(question)
        if len_question > 200:
            await ctx.send(
                f"Thank you for your question {ctx.author.mention}, however your question"
                f", after we add your name, is {len_question} characters long, but "
                " YouTube limits it to 200.\n"
                f"Please reduce your question by at least {len_question - 200} characters."
            )
            return
        request = youtube.liveChatMessages().insert(
            part="snippet",
            body={
                "snippet": {
                    "liveChatId": live_chat_id,
                    "type": "textMessageEvent",
                    "textMessageDetails": {"messageText": question},
                }
            },
        )
        try:
            request.execute()
        except HttpError as e:
            await ctx.send(
                f"Thank you for your question {ctx.author.mention}, however it was "
                f"rejected by YouTube for the following reason: {e.reason}"
            )
            return

        await ctx.send(f"Thank you for your question {ctx.author.mention}")
