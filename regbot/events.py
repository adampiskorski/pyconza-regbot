from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from regbot.google import get_client_credentials
from regbot.helpers import ServerInfo, get_str_env, log
from regbot.tasks import QuicketSync, WaferSync, YouTubeVideoSync

if TYPE_CHECKING:
    from discord import Reaction, User

    from regbot import RegBot

EVENT_NAME = get_str_env("EVENT_NAME")
REPOST_REACTION = "🔔"


class EventsCog(commands.Cog):
    """Bot lifecycle and server event handlers."""

    def __init__(self, bot: RegBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await log(f"{self.bot.user.name} has connected to the following guilds:")
        for guild in self.bot.guilds:
            await log(f"{guild.name}, ID: {guild.id}")
        if self.bot.feature_quicket_sync:
            await self.bot.add_cog(QuicketSync(self.bot))
        if self.bot.feature_wafer_sync:
            await self.bot.add_cog(WaferSync(self.bot))
        if self.bot.feature_youtube_sync:
            # Get oAuth Credentials on start.
            get_client_credentials()
            await self.bot.add_cog(YouTubeVideoSync(self.bot))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        server_info = await ServerInfo.get()
        await log(f"{member.mention} has joined the server!")
        if self.bot.feature_registration:
            if member.dm_channel is None:
                await member.create_dm()
            if member.dm_channel is None:
                await log(f"Could not create DM channel for {member.mention}!")
                return
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
            await server_info.welcome_channel.send(
                f"Welcome to {EVENT_NAME}, {member.mention}! Please register your ticket with me "
                "in the Direct Message channel that I created with you..."
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await log(
            f"`{ctx.invoked_with}` command got message `{ctx.message.clean_content}` from "
            f"{ctx.author.mention} that caused error: `{error}`"
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        if self.bot.feature_repost_announce:
            server_info = await ServerInfo.get()
            if (
                reaction.emoji == REPOST_REACTION
                and reaction.message.channel == server_info.announcement_staging_channel
            ):
                await server_info.announcement_channel.send(reaction.message.content)
