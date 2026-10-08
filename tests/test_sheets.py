"""Unit tests for the Google Sheets layer: quiz questions and ticket registration."""

import pytest

from regbot.quicket import Ticket
from regbot.sheets import QuizQuestion, is_ticket_used, register_ticket

from .fakes import FakeWorksheet, fake_google_sheets

QUIZ_ROWS = [
    ["Question", "Answer", "Channel", "Hint", "Answerer"],
    ["What is 2+2?", "four", "123", "where maths lives", ""],
    ["What is the airspeed of a swallow?", "42", "456", "the movie channel", "999"],
    ["Last question?", "yes", "789", "the last place", ""],
]


@pytest.fixture
def quiz_sheet(monkeypatch):
    """The quiz worksheet, wired in as the Google Sheet backend."""
    sheet = FakeWorksheet(QUIZ_ROWS)
    fake_google_sheets(monkeypatch, quiz=sheet)
    return sheet


class TestGetAllQuizQuestions:
    async def test_rows_become_questions_and_the_header_is_skipped(self, quiz_sheet):
        questions = await QuizQuestion.get_all_quiz_questions()

        assert len(questions) == 3
        first = questions[0]
        assert first.row == 2  # the sheet row, 1-based, after the header
        assert first.question == "What is 2+2?"
        assert first.answer == "four"
        assert first.channel_id == 123
        assert first.channel_hint == "where maths lives"
        assert first.answerer_id is None

    async def test_answered_questions_have_their_answerer_id(self, quiz_sheet):
        questions = await QuizQuestion.get_all_quiz_questions()

        assert questions[1].answerer_id == 999

    async def test_the_last_question_is_marked_as_final(self, quiz_sheet):
        questions = await QuizQuestion.get_all_quiz_questions()

        assert [question.is_final_question for question in questions] == [
            False,
            False,
            True,
        ]


class TestCellRoundTrip:
    async def test_a_question_converts_back_to_its_sheet_row(self, quiz_sheet):
        question = (await QuizQuestion.get_all_quiz_questions())[0]

        assert [cell.value for cell in question.cell] == QUIZ_ROWS[1]

    async def test_an_answered_question_writes_its_answerer(self, quiz_sheet):
        question = (await QuizQuestion.get_all_quiz_questions())[0]
        question.answerer_id = 42

        assert question.cell[-1].value == "42"


class TestGetCurrentQuestion:
    async def test_returns_the_lowest_unanswered_question(self, quiz_sheet):
        current = await QuizQuestion.get_current_question()

        assert current.question == "What is 2+2?"

    async def test_returns_none_when_all_questions_are_answered(self, monkeypatch):
        answered = FakeWorksheet([QUIZ_ROWS[0], QUIZ_ROWS[2]])
        fake_google_sheets(monkeypatch, quiz=answered)

        assert await QuizQuestion.get_current_question() is None


class TestMarkAsAnswered:
    async def test_writes_the_answerer_to_the_sheet(self, quiz_sheet):
        question = await QuizQuestion.get_current_question()

        await question.mark_as_answered(42)

        assert quiz_sheet.rows[1][4] == "42"


class TestScores:
    async def test_scores_count_correct_answers_per_answerer(self, quiz_sheet):
        assert await QuizQuestion.scores() == {999: 1}

    async def test_scores_are_ordered_highest_first(self, monkeypatch):
        rows = [
            QUIZ_ROWS[0],
            ["Q1?", "a", "1", "h", "111"],
            ["Q2?", "a", "1", "h", "222"],
            ["Q3?", "a", "1", "h", "111"],
        ]
        fake_google_sheets(monkeypatch, quiz=FakeWorksheet(rows))

        assert await QuizQuestion.scores() == {111: 2, 222: 1}

    async def test_top_scorer_is_the_highest_scoring_answerer(self, quiz_sheet):
        assert await QuizQuestion.top_scorer_and_score() == (999, 1)

    async def test_top_scorer_is_none_without_any_answers(self, monkeypatch):
        unanswered = FakeWorksheet([QUIZ_ROWS[0], QUIZ_ROWS[1]])
        fake_google_sheets(monkeypatch, quiz=unanswered)

        assert await QuizQuestion.top_scorer_and_score() is None


class FakeMember:
    """The parts of a discord member that register_ticket uses."""

    def __init__(self, name, member_id):
        self.name = name
        self.id = member_id


class TestTicketRegistrationSheet:
    async def test_an_unused_barcode_is_not_found(self, monkeypatch):
        registrations = FakeWorksheet()
        fake_google_sheets(monkeypatch, registrations=registrations)
        ticket = Ticket("555777", True, "Ada", "Lovelace", "Standard")

        assert await is_ticket_used(ticket) is False

    async def test_a_barcode_in_the_barcode_column_marks_the_ticket_used(
        self, monkeypatch
    ):
        registrations = FakeWorksheet([["555777", "Grace Hopper", "grace", "7", "date"]])
        fake_google_sheets(monkeypatch, registrations=registrations)
        ticket = Ticket("555777", True, "Ada", "Lovelace", "Standard")

        assert await is_ticket_used(ticket) is True

    async def test_a_barcode_elsewhere_in_the_sheet_does_not_count(self, monkeypatch):
        registrations = FakeWorksheet([["42", "555777 is not a barcode", "g", "7", "d"]])
        fake_google_sheets(monkeypatch, registrations=registrations)
        ticket = Ticket("555777", True, "Ada", "Lovelace", "Standard")

        assert await is_ticket_used(ticket) is False

    async def test_registering_appends_a_row_with_the_ticket_and_member(
        self, monkeypatch
    ):
        registrations = FakeWorksheet()
        fake_google_sheets(monkeypatch, registrations=registrations)
        ticket = Ticket("555777", True, "Ada", "Lovelace", "Standard")

        await register_ticket(ticket, FakeMember("ada", 42))

        row = registrations.rows[0]
        assert row[:4] == ["555777", "Ada Lovelace", "ada", "42"]
        assert row[4]  # the registration date
