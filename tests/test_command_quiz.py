"""Integration tests for the `!quiz` command.

The quiz hunt is driven by a Google Sheet: each question belongs to a specific
channel, the first unanswered question is the current one, and answering it
correctly records the answerer in the sheet (which is also the scoreboard).
"""

from types import SimpleNamespace

import pytest

from .fakes import FakeWorksheet, fake_google_sheets


@pytest.fixture
def quiz(server, monkeypatch):
    """A two-question quiz: one question per channel, none answered yet."""
    quiz_room = server.guild.create_text_channel("quiz-room")
    final_room = server.guild.create_text_channel("final-room")
    sheet = FakeWorksheet(
        [
            ["Question", "Answer", "Channel", "Hint", "Answerer"],
            ["What is 2+2?", "four", str(quiz_room.id), "where maths lives", ""],
            ["Final question?", "yes", str(final_room.id), "the last place", ""],
        ]
    )
    fake_google_sheets(monkeypatch, quiz=sheet)
    return SimpleNamespace(quiz_room=quiz_room, final_room=final_room, sheet=sheet)


async def test_quiz_without_an_answer_returns_the_current_question(
    simcord_env, server, quiz
):
    ada = server.add_member("ada")

    await ada.send(quiz.quiz_room, "!quiz")

    assert quiz.quiz_room.last_message.content == "What is 2+2?"


async def test_asking_in_the_wrong_channel_gives_a_hint(simcord_env, server, quiz):
    ada = server.add_member("ada")

    await ada.send(quiz.final_room, "!quiz")

    reply = quiz.final_room.last_message.content
    assert "Hint for the right channel: where maths lives" in reply


async def test_a_correct_answer_is_recorded_in_the_sheet(simcord_env, server, quiz):
    ada = server.add_member("ada")

    # Answers are case-insensitive.
    await ada.send(quiz.quiz_room, "!quiz FOUR")

    assert ada.mention in quiz.quiz_room.last_message.content
    assert quiz.sheet.rows[1][4] == str(ada.id)


async def test_answering_the_final_question_completes_the_quiz(simcord_env, server, quiz):
    ada = server.add_member("ada")
    await ada.send(quiz.quiz_room, "!quiz four")

    await ada.send(quiz.final_room, "!quiz yes")

    assert "completed the final question" in quiz.final_room.last_message.content


async def test_a_wrong_answer_does_not_mark_the_question_answered(
    simcord_env, server, quiz
):
    ada = server.add_member("ada")

    await ada.send(quiz.quiz_room, "!quiz five")

    assert ada.mention in quiz.quiz_room.last_message.content
    assert quiz.sheet.rows[1][4] == ""


async def test_no_questions_left_once_all_are_answered(simcord_env, server, quiz):
    ada = server.add_member("ada")
    await ada.send(quiz.quiz_room, "!quiz four")
    await ada.send(quiz.final_room, "!quiz yes")

    await ada.send(quiz.quiz_room, "!quiz")

    assert "no more questions left" in quiz.quiz_room.last_message.content


async def test_who_is_winning_without_any_answers(simcord_env, server, quiz):
    ada = server.add_member("ada")

    await ada.send(quiz.quiz_room, "!quiz who is winning?")

    assert "no correctly answered questions yet" in (quiz.quiz_room.last_message.content)


async def test_who_is_winning_names_the_top_scorer(simcord_env, server, quiz):
    ada = server.guild.add_member(server.env.create_user("ada"), nick="Ada L.")
    await ada.send(quiz.quiz_room, "!quiz four")

    await ada.send(quiz.quiz_room, "!quiz who is winning?")

    assert quiz.quiz_room.last_message.content == "Ada L. with a score of 1"


async def test_who_is_winning_falls_back_to_the_username_without_a_nick(
    simcord_env, server, quiz
):
    ada = server.add_member("ada")  # no nickname set
    await ada.send(quiz.quiz_room, "!quiz four")

    await ada.send(quiz.quiz_room, "!quiz who is winning?")

    assert quiz.quiz_room.last_message.content == "ada with a score of 1"


async def test_scores_shows_unknown_for_answerers_who_left(simcord_env, server, quiz):
    quiz.sheet.rows[1][4] = "999999"  # answered by someone not on the server
    ada = server.add_member("ada")

    await ada.send(quiz.quiz_room, "!quiz scores?")

    assert quiz.quiz_room.last_message.content == "Unknown with a score of 1"


async def test_scores_lists_everyone_with_correct_answers(simcord_env, server, quiz):
    ada = server.guild.add_member(server.env.create_user("ada"), nick="Ada L.")
    alan = server.guild.add_member(server.env.create_user("alan"), nick="Alan T.")
    await ada.send(quiz.quiz_room, "!quiz four")
    await alan.send(quiz.final_room, "!quiz yes")

    await alan.send(quiz.quiz_room, "!quiz scores?")

    scores = quiz.quiz_room.last_message.content.splitlines()
    assert scores == ["Ada L. with a score of 1", "Alan T. with a score of 1"]
