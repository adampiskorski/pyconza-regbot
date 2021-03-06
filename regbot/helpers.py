from __future__ import annotations

from dataclasses import dataclass
import logging
import os

from discord import Guild, TextChannel, Role
from discord.utils import get

from regbot import bot

SERVER_INFO_CACHE = None


def get_str_env(env_name: str) -> str:
    """Get the given envar or raise an assertion error"""
    value = os.getenv(env_name)
    assert value, f"The environmental variable {env_name} was not found!"
    return value


def get_int_env(env_name: str) -> int:
    """Get the given integer envar or raise an assertion error"""
    value = int(os.getenv(env_name, "0"))
    assert value, f"The environmental variable {env_name} was not found!"
    return value


LOG_CHANNEL = get_int_env("DISCORD_LOG_CHANNEL_ID")


async def log(message: str):
    """Helper to log to discord as well as standard logging"""
    logging.info(message)
    channel = bot.get_channel(LOG_CHANNEL)
    await channel.send(message)


ATTENDEE_ROLE = get_str_env("DISCORD_REGISTERED_ROLE_NAME")
REGISTRATION_ROLE = get_str_env("DISCORD_REGISTRATION_ROLE")
ORGANIZER_ROLE = get_str_env("DISCORD_ORGANIZER_ROLE")
SPEAKER_ROLE = get_str_env("DISCORD_SPEAKER_ROLE")
HELP_DESK = get_int_env("DISCORD_HELPDESK_CHANNEL_ID")
WELCOME_CHANNEL = get_int_env("DISCORD_WELCOME_CHANNEL_ID")
ANNOUNCEMENT_CHANNEL = get_int_env("DISCORD_ANNOUNCEMENT_CHANNEL_ID")

GUILD_ID = get_int_env("DISCORD_GUILD_ID")


@dataclass
class ServerInfo:
    """A representation of data to be retrieved only once from the discord server"""

    guild: Guild
    attendee: Role
    registration: Role
    organizer: Role
    speaker: Role
    help_desk: TextChannel
    welcome_channel: TextChannel
    announcement_channel: TextChannel

    @classmethod
    async def get(cls) -> ServerInfo:
        """Get the server info from cache, or from Discord if it doesn't exist"""
        global SERVER_INFO_CACHE

        if SERVER_INFO_CACHE is None:
            guild = bot.get_guild(GUILD_ID)
            assert guild is not None, "No guild was found!"

            attendee = get(guild.roles, name=ATTENDEE_ROLE)
            assert attendee is not None, "The attendee role was not found!"

            registration = get(guild.roles, name=REGISTRATION_ROLE)
            assert registration is not None, "The registration role was not found!"

            organizer = get(guild.roles, name=ORGANIZER_ROLE)
            assert organizer is not None, "The organizer role was not found!"

            speaker = get(guild.roles, name=SPEAKER_ROLE)
            assert speaker is not None, "The speaker role was not found!"

            help_desk = bot.get_channel(HELP_DESK)
            assert help_desk is not None, "The help desk channel was not found!"

            welcome_channel = bot.get_channel(WELCOME_CHANNEL)
            assert welcome_channel is not None, "The general channel was not found!"

            announcement_channel = bot.get_channel(ANNOUNCEMENT_CHANNEL)
            assert (
                announcement_channel is not None
            ), "The announcement channel was not found!"

            SERVER_INFO_CACHE = cls(
                guild=guild,
                attendee=attendee,
                registration=registration,
                organizer=organizer,
                speaker=speaker,
                help_desk=help_desk,
                welcome_channel=welcome_channel,
                announcement_channel=announcement_channel,
            )

        return SERVER_INFO_CACHE
