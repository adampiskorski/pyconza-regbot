"""Integration tests for the bot's event handlers: welcoming new members,
reposting staged announcements, and logging command errors."""

from regbot.events import REPOST_REACTION


async def test_new_member_is_welcomed_via_dm_and_in_the_welcome_channel(
    simcord_env, server
):
    ada = server.add_member("ada")

    await simcord_env.settle()

    # She gets a personal welcome DM explaining how to register...
    dm_messages = [m.content for m in ada.user.dm_channel.history()]
    assert any("Welcome ada to PyConZA Test!" in content for content in dm_messages)
    assert any("!register <Quicket Ticket barcode number>" in c for c in dm_messages)
    # ...and the server is told to expect her registration.
    assert ada.mention in server.welcome_channel.last_message.content


async def test_member_who_already_has_a_dm_channel_is_welcomed_without_warning(
    simcord_env, server
):
    # Ada has DM'd the bot before, so the DM channel already exists.
    user = simcord_env.create_user("ada")
    await user.send_dm("hello")

    server.guild.add_member(user)
    await simcord_env.settle()

    dm_messages = [m.content for m in user.dm_channel.history()]
    assert any("Welcome ada to PyConZA Test!" in content for content in dm_messages)
    assert all(
        "Could not create DM channel" not in m.content
        for m in server.log_channel.history()
    )


async def test_repost_reaction_reposts_staged_announcements(simcord_env, server):
    organizer = server.add_member("organizer")
    staged = await organizer.send(
        server.announcement_staging_channel, "PyConZA starts tomorrow!"
    )

    await organizer.react(staged, REPOST_REACTION)

    assert server.announcement_channel.last_message.content == "PyConZA starts tomorrow!"


async def test_other_reactions_do_not_repost(simcord_env, server):
    organizer = server.add_member("organizer")
    staged = await organizer.send(
        server.announcement_staging_channel, "PyConZA starts tomorrow!"
    )

    await organizer.react(staged, "👍")

    assert server.announcement_channel.last_message is None


async def test_reactions_elsewhere_do_not_repost(simcord_env, server):
    organizer = server.add_member("organizer")
    general = server.guild.create_text_channel("general")
    message = await organizer.send(general, "PyConZA starts tomorrow!")

    await organizer.react(message, REPOST_REACTION)

    assert server.announcement_channel.last_message is None


async def test_command_errors_are_logged_to_the_log_channel(simcord_env, server):
    from discord.ext.commands.errors import MissingRequiredArgument

    ada = server.add_member("ada")

    # `!register` without a barcode is a command error.
    await ada.send_dm("!register")

    assert "`register` command got message" in server.log_channel.last_message.content
    assert isinstance(simcord_env.errors[-1], MissingRequiredArgument)
