from __future__ import annotations

import discord
from discord.ext import commands
from rich import pretty, traceback

__version__ = "0.1.0"

pretty.install()
traceback.install(show_locals=True)

# The most recently created bot. Helpers (e.g. `log`) resolve the bot lazily
# through this reference, so that tests can build a fresh bot per test.
bot: RegBot | None = None


class RegBot(commands.Bot):
    """The PyConZA registration bot.

    The feature flags decide which cogs are loaded in `setup_hook`. Each flag
    defaults to the value of its respective environmental variable, but can be
    set explicitly (useful for tests).
    """

    def __init__(
        self,
        *,
        feature_registration: bool | None = None,
        feature_youtube: bool | None = None,
        feature_youtube_sync: bool | None = None,
        feature_quiz: bool | None = None,
        feature_repost_announce: bool | None = None,
        feature_quicket_sync: bool | None = None,
        feature_wafer_sync: bool | None = None,
    ) -> None:
        from regbot.helpers import get_bool_env

        def resolve(flag: bool | None, env_name: str) -> bool:
            return flag if flag is not None else get_bool_env(env_name)

        self.feature_registration = resolve(feature_registration, "FEATURE_REGISTRATION")
        self.feature_youtube = resolve(feature_youtube, "FEATURE_YOUTUBE")
        # The YouTube channel-sync cog defaults to the YouTube feature flag, but
        # is separately controllable so that tests can use the `!question`
        # command without starting the channel sync loops.
        self.feature_youtube_sync = (
            self.feature_youtube if feature_youtube_sync is None else feature_youtube_sync
        )
        self.feature_quiz = resolve(feature_quiz, "FEATURE_QUIZ")
        self.feature_repost_announce = resolve(
            feature_repost_announce, "FEATURE_REPOST_ANNOUNCE"
        )
        self.feature_quicket_sync = resolve(feature_quicket_sync, "FEATURE_QUICKET_SYNC")
        self.feature_wafer_sync = resolve(feature_wafer_sync, "FEATURE_WAFER_SYNC")
        super().__init__(
            command_prefix="!",
            description="Registration bot",
            intents=discord.Intents.all(),
        )

    async def setup_hook(self) -> None:
        from regbot.commands import QuestionCog, QuizCog, RegistrationCog
        from regbot.events import EventsCog

        if self.feature_registration:
            await self.add_cog(RegistrationCog())
        if self.feature_youtube:
            await self.add_cog(QuestionCog())
        if self.feature_quiz:
            await self.add_cog(QuizCog())
        await self.add_cog(EventsCog(self))


def create_bot(**kwargs) -> RegBot:
    """Create the bot and remember it as the module-level bot for helpers."""
    global bot
    bot = RegBot(**kwargs)
    return bot
