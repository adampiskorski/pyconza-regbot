"""Unit tests for the pure helper functions in regbot.helpers."""

import pytest

from regbot.helpers import (
    get_bool_env,
    int_or_none,
    safe_send_message,
    to_discord_description_safe,
    to_discord_title_safe,
)


class TestToDiscordTitleSafe:
    def test_spaces_become_dashes_and_text_is_lowercased(self):
        assert to_discord_title_safe("Opening Ceremony") == "opening-ceremony"

    def test_non_alphanumerics_are_stripped(self):
        assert (
            to_discord_title_safe("What's new in Python 3.14?")
            == "whats-new-in-python-314"
        )

    def test_repeated_dashes_collapse_into_one(self):
        assert to_discord_title_safe("a  -  b") == "a-b"

    def test_titles_are_capped_at_96_characters(self):
        assert len(to_discord_title_safe("x" * 200)) == 96


class TestToDiscordDescriptionSafe:
    def test_descriptions_are_capped_at_1024_characters(self):
        assert to_discord_description_safe("x" * 2000) == "x" * 1024

    def test_short_descriptions_are_unchanged(self):
        assert to_discord_description_safe("A nice talk.") == "A nice talk."


class TestIntOrNone:
    def test_integer_strings_convert(self):
        assert int_or_none("42") == 42

    def test_non_integer_strings_become_none(self):
        assert int_or_none("not a number") is None

    def test_empty_strings_become_none(self):
        assert int_or_none("") is None


class TestGetBoolEnv:
    @pytest.mark.parametrize("value", ["y", "yes", "t", "true", "on", "1"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("SOME_FLAG", value)
        assert get_bool_env("SOME_FLAG") is True

    @pytest.mark.parametrize("value", ["n", "no", "f", "false", "off", "0"])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("SOME_FLAG", value)
        assert get_bool_env("SOME_FLAG") is False

    def test_missing_variable_uses_the_default(self, monkeypatch):
        monkeypatch.delenv("SOME_FLAG", raising=False)
        assert get_bool_env("SOME_FLAG", default=True) is True
        assert get_bool_env("SOME_FLAG") is False


class FakeMessageable:
    """Records the messages it is asked to send."""

    def __init__(self):
        self.sent = []

    async def send(self, text):
        self.sent.append(text)
        return text


class TestSafeSendMessage:
    async def test_short_messages_are_sent_as_is(self):
        target = FakeMessageable()
        await safe_send_message(target, "hello")
        assert target.sent == ["hello"]

    async def test_long_messages_are_split_into_2000_character_parts(self):
        target = FakeMessageable()
        await safe_send_message(target, "x" * 4500)
        assert [len(part) for part in target.sent] == [2000, 2000, 500]
