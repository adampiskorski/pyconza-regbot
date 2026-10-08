"""Tests for the `!register` command: the core feature of the bot.

A user DMs the bot their Quicket ticket barcode; the bot checks the ticket
against the Quicket guest list and the Google Sheet of used tickets, then
grants the appropriate roles and sets the user's nickname to their real name.
"""

import pytest

from regbot.quicket import Ticket

from .fakes import FakeWorksheet, fake_google_sheets


def make_ticket(
    barcode="555777",
    first_name="Ada",
    surname="Lovelace",
    ticket_type="Standard",
):
    return Ticket(
        barcode=barcode,
        valid=True,
        first_name=first_name,
        surname=surname,
        type=ticket_type,
    )


@pytest.fixture
def registrations(monkeypatch):
    """An empty registration sheet, wired in as the Google Sheet backend."""
    sheet = FakeWorksheet()
    fake_google_sheets(monkeypatch, registrations=sheet)
    return sheet


def given_ticket(monkeypatch, ticket):
    """Put the given ticket on the Quicket guest list."""
    import regbot.quicket as quicket

    monkeypatch.setattr(quicket, "TICKETS", {**quicket.TICKETS, ticket.barcode: ticket})


async def test_valid_ticket_registers_with_attendee_role_and_nickname(
    simcord_env, server, registrations, monkeypatch
):
    # Arrange: Ada has a valid ticket on the guest list.
    given_ticket(monkeypatch, make_ticket())
    ada = server.add_member("ada")

    # Act: she DMs the bot her barcode.
    await ada.send_dm("!register 555777")

    # Assert: she is welcomed, gets the attendee role and her real name.
    assert "Registration successful!" in ada.user.dm_channel.last_message.content
    assert server.roles["attendee"].id in [role.id for role in ada.member.roles]
    assert ada.member.nick == "Ada Lovelace"
    # ...and her ticket is recorded as used in the registration sheet.
    assert registrations.rows[0][:4] == ["555777", "Ada Lovelace", "ada", str(ada.id)]


async def test_unknown_barcode_is_rejected_with_help_pointers(
    simcord_env, server, registrations
):
    ada = server.add_member("ada")

    await ada.send_dm("!register 000000")

    reply = ada.user.dm_channel.last_message.content
    assert "could not find a ticket" in reply
    assert server.help_desk.mention in reply
    assert server.roles["attendee"].id not in [role.id for role in ada.member.roles]


async def test_already_used_ticket_is_rejected(
    simcord_env, server, registrations, monkeypatch
):
    # Arrange: the ticket is on the guest list but already in the sheet.
    given_ticket(monkeypatch, make_ticket())
    registrations.rows.append(["555777", "Ada Lovelace", "someone-else", "42", "date"])
    ada = server.add_member("ada")

    await ada.send_dm("!register 555777")

    assert "already used" in ada.user.dm_channel.last_message.content
    assert server.roles["attendee"].id not in [role.id for role in ada.member.roles]


async def test_speaker_barcode_also_grants_the_speaker_role(
    simcord_env, server, registrations, monkeypatch
):
    import regbot.wafer as wafer

    given_ticket(monkeypatch, make_ticket())
    monkeypatch.setattr(wafer, "SPEAKERS_TICKETS", {"555777"})
    ada = server.add_member("ada")

    await ada.send_dm("!register 555777")

    assert server.roles["speaker"].id in [role.id for role in ada.member.roles]
    assert "you are a speaker" in ada.user.dm_channel.last_message.content


@pytest.mark.parametrize(
    ("ticket_type", "role_key"),
    [
        ("Gold Sponsor", "gold_sponsor"),
        ("Silver Sponsor", "silver_sponsor"),
        ("Patron Sponsor", "patron_sponsor"),
    ],
)
async def test_sponsor_tickets_grant_the_matching_sponsor_role(
    simcord_env, server, registrations, monkeypatch, ticket_type, role_key
):
    given_ticket(monkeypatch, make_ticket(ticket_type=ticket_type))
    ada = server.add_member("ada")

    await ada.send_dm("!register 555777")

    assert server.roles[role_key].id in [role.id for role in ada.member.roles]
    assert "you are a sponsor" in ada.user.dm_channel.last_message.content


async def test_names_over_32_characters_are_truncated_with_an_apology(
    simcord_env, server, registrations, monkeypatch
):
    long_name = "Bartholomew" * 3  # 33 characters
    given_ticket(monkeypatch, make_ticket(surname=long_name))
    ada = server.add_member("ada")

    await ada.send_dm("!register 555777")

    assert ada.member.nick == f"Ada {long_name}"[:32]
    assert (
        "we had to truncate your full name" in ada.user.dm_channel.history()[-2].content
    )


async def test_register_command_message_is_deleted_outside_dms(
    simcord_env, server, registrations, monkeypatch
):
    given_ticket(monkeypatch, make_ticket())
    ada = server.add_member("ada")
    channel = server.guild.create_text_channel("registrations")

    await ada.send(channel, "!register 555777")

    # The command message (which contains the barcode) is deleted...
    assert all("!register" not in m.content for m in channel.history())
    # ...and the registration still went through.
    assert server.roles["attendee"].id in [role.id for role in ada.member.roles]


async def test_registration_succeeds_even_if_nickname_change_is_forbidden(
    simcord_env, server, registrations, monkeypatch
):
    given_ticket(monkeypatch, make_ticket())
    ada = server.add_member("ada")
    simcord_env.inject_error("PATCH", "/guilds/*/members/*", status=403, code=50013)

    await ada.send_dm("!register 555777")

    assert ada.member.nick is None
    assert "Registration successful!" in ada.user.dm_channel.last_message.content
    assert any(
        "Failed to change the nickname" in m.content for m in server.log_channel.history()
    )


async def test_register_from_someone_not_on_the_server_is_logged_and_ignored(
    simcord_env, server, registrations
):
    outsider = simcord_env.create_user("outsider")

    await outsider.send_dm("!register 555777")

    assert "None object member encountered" in server.log_channel.last_message.content
    assert outsider.dm_channel.last_message.content.startswith("!register")
