from __future__ import annotations
import textwrap

import logging
import os
import re
from dataclasses import dataclass
from distutils.util import strtobool
from typing import List, Optional

from discord import CategoryChannel, Guild, Role, TextChannel, Message
from discord.abc import Messageable
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


def get_bool_env(environ_var: str, default: Optional[bool] = False) -> bool:
    """Somewhat reliably returns a boolean value based on various kinds of `truthy` or
    `falsy` string values in the environment.
    """
    value = os.getenv(environ_var, str(default))
    return bool(strtobool(value))


def to_discord_title_safe(text: str) -> str:
    """Convert the given string to one that will be accepted by discord as a title for a
    channel.
    """
    text = text.replace(" ", "-")
    text = text[:96]
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\-]", "", text)  # Eliminate all non alpha numerics and `-`
    return re.sub(r"(\-)\1{1,}", "-", text)  # Eliminate repeated `-`


def to_discord_description_safe(text: str) -> str:
    """Convert the given string to one that will be accepted by discord as a description
    for a channel.
    """
    return text[:1024]


async def safe_send_message(target: Messageable, text: str) -> List[Message]:
    """Safely send a message to the given messageable target.
    The utility of this is function, is that the message will be split into multiple parts
    if its too long.
    """
    messages = []
    for part in textwrap.wrap(
        text,
        width=2000,
        expand_tabs=False,
        replace_whitespace=False,
        drop_whitespace=False,
    ):
        message = await target.send(part)
        messages.append(message)
    return messages


LOG_CHANNEL = get_int_env("DISCORD_LOG_CHANNEL_ID")


async def log(message: str):
    """Helper to log to discord as well as standard logging"""
    logging.info(message)
    channel = bot.get_channel(LOG_CHANNEL)
    assert channel is not None, "Need a log channel!"
    await safe_send_message(channel, message)


ATTENDEE_ROLE = get_str_env("DISCORD_REGISTERED_ROLE_NAME")
REGISTRATION_ROLE = get_str_env("DISCORD_REGISTRATION_ROLE")
ORGANIZER_ROLE = get_str_env("DISCORD_ORGANIZER_ROLE")
SPEAKER_ROLE = get_str_env("DISCORD_SPEAKER_ROLE")
SPONSOR_PATRON_ROLE = get_str_env("DISCORD_SPONSOR_PATRON_ROLE")
SPONSOR_SILVER_ROLE = get_str_env("DISCORD_SPONSOR_SILVER_ROLE")
SPONSOR_GOLD_ROLE = get_str_env("DISCORD_SPONSOR_GOLD_ROLE")
HELP_DESK = get_int_env("DISCORD_HELPDESK_CHANNEL_ID")
WELCOME_CHANNEL = get_int_env("DISCORD_WELCOME_CHANNEL_ID")
ANNOUNCEMENT_CHANNEL = get_int_env("DISCORD_ANNOUNCEMENT_CHANNEL_ID")
ANNOUNCEMENT_STAGING_CHANNEL = get_int_env("DISCORD_ANNOUNCEMENT_STAGING_CHANNEL_ID")
YOUTUBE_CATEGORY = get_int_env("DISCORD_YOUTUBE_CATEGORY")

GUILD_ID = get_int_env("DISCORD_GUILD_ID")


@dataclass
class ServerInfo:
    """A representation of data to be retrieved only once from the discord server"""

    guild: Guild
    attendee: Role
    registration: Role
    organizer: Role
    speaker: Role
    patron_sponsor: Role
    silver_sponsor: Role
    gold_sponsor: Role
    help_desk: TextChannel
    welcome_channel: TextChannel
    announcement_channel: TextChannel
    announcement_staging_channel: TextChannel
    youtube_category: CategoryChannel

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

            patron_sponsor = get(guild.roles, name=SPONSOR_PATRON_ROLE)
            assert patron_sponsor is not None, "The patron sponsor role was not found!"

            silver_sponsor = get(guild.roles, name=SPONSOR_SILVER_ROLE)
            assert silver_sponsor is not None, "The silver sponsor role was not found!"

            gold_sponsor = get(guild.roles, name=SPONSOR_GOLD_ROLE)
            assert gold_sponsor is not None, "The gold sponsor role was not found!"

            help_desk = bot.get_channel(HELP_DESK)
            assert help_desk is not None, "The help desk channel was not found!"

            welcome_channel = bot.get_channel(WELCOME_CHANNEL)
            assert welcome_channel is not None, "The general channel was not found!"

            announcement_channel = bot.get_channel(ANNOUNCEMENT_CHANNEL)
            assert (
                announcement_channel is not None
            ), "The announcement channel was not found!"

            announcement_staging_channel = bot.get_channel(ANNOUNCEMENT_STAGING_CHANNEL)
            assert (
                announcement_staging_channel is not None
            ), "The announcement staging channel was not found!"

            youtube_category = bot.get_channel(YOUTUBE_CATEGORY)
            assert youtube_category is not None, "The YouTube category was not found!"

            SERVER_INFO_CACHE = cls(
                guild=guild,
                attendee=attendee,
                registration=registration,
                organizer=organizer,
                speaker=speaker,
                help_desk=help_desk,
                welcome_channel=welcome_channel,
                announcement_channel=announcement_channel,
                announcement_staging_channel=announcement_staging_channel,
                youtube_category=youtube_category,
                patron_sponsor=patron_sponsor,
                silver_sponsor=silver_sponsor,
                gold_sponsor=gold_sponsor,
            )

        return SERVER_INFO_CACHE
