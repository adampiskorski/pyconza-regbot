"""Integration tests for the `!question` command.

Questions asked in a talk's discord channel are echoed to that talk's YouTube
live chat, prefixed with the asker's name. YouTube rejects messages longer
than 200 characters, so the bot checks the length itself first.
"""

import pytest

import regbot.commands as commands
import regbot.youtube as youtube

from .fakes import FakeYouTube, make_http_error


@pytest.fixture
def broadcast_channel(simcord_bot, server, monkeypatch):
    """A talk channel that is linked to a YouTube live chat."""
    handle = server.guild.create_text_channel("opening-talk")
    channel = simcord_bot.get_channel(handle.id)
    monkeypatch.setattr(
        youtube, "BROADCAST_CHANNELS", {channel: {"live_chat_id": "live-chat-1"}}
    )
    return handle


@pytest.fixture
def fake_youtube(monkeypatch):
    """The fake YouTube API that the `!question` command will use."""
    fake = FakeYouTube()
    monkeypatch.setattr(commands, "get_youtube", lambda: fake)
    return fake


async def test_question_without_text_is_politely_refused(
    simcord_env, server, broadcast_channel
):
    ada = server.add_member("ada")

    await ada.send(broadcast_channel, "!question")

    assert "you gave us a question" in broadcast_channel.last_message.content


async def test_questions_only_work_in_broadcast_channels(simcord_env, server):
    ada = server.add_member("ada")
    general = server.guild.create_text_channel("general")

    await ada.send(general, "!question What is the airspeed velocity?")

    assert "not a channel dealing with YouTube Broadcasts" in (
        general.last_message.content
    )


async def test_questions_over_200_characters_are_rejected_with_the_excess(
    simcord_env, server, broadcast_channel
):
    ada = server.add_member("ada")
    # "ada asks: " adds 10 characters, so 191 characters become 201.
    await ada.send(broadcast_channel, f"!question {'x' * 191}")

    reply = broadcast_channel.last_message.content
    assert "is 201 characters long" in reply
    assert "reduce your question by at least 1 characters" in reply


async def test_a_question_is_echoed_to_the_youtube_live_chat_with_the_askers_name(
    simcord_env, server, broadcast_channel, fake_youtube
):
    ada = server.add_member("ada")

    await ada.send(broadcast_channel, "!question What is the airspeed velocity?")

    assert (
        broadcast_channel.last_message.content
        == f"Thank you for your question {ada.mention}"
    )
    (inserted,) = fake_youtube.inserted_messages
    snippet = inserted["snippet"]
    assert snippet["liveChatId"] == "live-chat-1"
    assert snippet["textMessageDetails"]["messageText"] == (
        "ada asks: What is the airspeed velocity?"
    )


async def test_youtube_rejections_are_relayed_to_the_asker(
    simcord_env, server, broadcast_channel, fake_youtube
):
    fake_youtube.error = make_http_error("The live chat is disabled.")
    ada = server.add_member("ada")

    await ada.send(broadcast_channel, "!question Too late?")

    reply = broadcast_channel.last_message.content
    assert "rejected by YouTube" in reply
    assert "The live chat is disabled." in reply
