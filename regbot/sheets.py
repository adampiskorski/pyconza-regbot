from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import DefaultDict, Dict, List, Optional, Tuple

import gspread_asyncio
from discord import User
from gspread.models import Cell
from gspread_asyncio import AsyncioGspreadWorksheet

from regbot.google import get_creds, get_str_env
from regbot.helpers import int_or_none, log
from regbot.quicket import Ticket

client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
SHEET_ID = get_str_env("GOOGLE_SHEET_ID")
WORKSHEET = get_str_env("GOOGLE_SHEET_WORKSHEET_NAME")
REG_BARCODE_COLUMN = 1
REG_FULL_NAME_COLUMN = 2
REG_DISCORD_NAME_COLUMN = 3
REG_DISCORD_ID_COLUMN = 4
REG_DATE_COLUMN = 5

QUIZ_SHEET_ID = get_str_env("QUIZ_GOOGLE_SHEET_ID")
QUIZ_WORKSHEET = get_str_env("QUIZ_GOOGLE_SHEET_WORKSHEET_NAME")
QUIZ_QUESTION_COLUMN = 1
QUIZ_ANSWER_COLUMN = 2
QUIZ_CHANNEL_COLUMN = 3
QUIZ_CHANNEL_HINT_COLUMN = 4
QUIZ_ANSWERER_COLUMN = 5
QUIZ_MAX_COLUMN_NUMBER = 5


async def get_worksheet(sheet_id: str, worksheet: str) -> AsyncioGspreadWorksheet:
    """Get the gspread worksheet used to store state of ticket registration"""
    client = await client_manager.authorize()
    sheet = await client.open_by_key(sheet_id)
    return await sheet.worksheet(worksheet)


@dataclass
class QuizQuestion:
    row: int
    question: str = field(metadata={"column": QUIZ_QUESTION_COLUMN})
    answer: str = field(metadata={"column": QUIZ_ANSWER_COLUMN})
    channel_id: int = field(metadata={"column": QUIZ_CHANNEL_COLUMN})
    channel_hint: str = field(metadata={"column": QUIZ_CHANNEL_HINT_COLUMN})
    answerer_id: Optional[int] = field(
        default=None, metadata={"column": QUIZ_ANSWERER_COLUMN}
    )
    is_final_question: bool = False

    @classmethod
    async def get_all_quiz_questions(cls) -> List[QuizQuestion]:
        """Get Convert the given worksheet """
        work_sheet = await get_worksheet(QUIZ_SHEET_ID, QUIZ_WORKSHEET)
        rows = await work_sheet.get_all_values()
        questions = [
            QuizQuestion(
                row=i + 1,
                question=row[fields(QuizQuestion)[1].metadata["column"] - 1],
                answer=row[fields(QuizQuestion)[2].metadata["column"] - 1],
                channel_id=int(row[fields(QuizQuestion)[3].metadata["column"] - 1]),
                channel_hint=row[fields(QuizQuestion)[4].metadata["column"] - 1],
                answerer_id=int_or_none(
                    row[fields(QuizQuestion)[5].metadata["column"] - 1]
                ),
            )
            for i, row in enumerate(rows)
            if i > 0  # The first row is the header row, so skip it.
        ]
        questions[-1].is_final_question = True
        return questions

    @property
    def cell(self) -> List[Cell]:
        """Convert the quiz question to list of gspread cells, which effectively
        represents an entire row in the sheet.
        """
        return [
            Cell(self.row, fields(QuizQuestion)[1].metadata["column"], self.question),
            Cell(self.row, fields(QuizQuestion)[2].metadata["column"], self.answer),
            Cell(
                self.row,
                fields(QuizQuestion)[3].metadata["column"],
                str(self.channel_id),
            ),
            Cell(
                self.row,
                fields(QuizQuestion)[4].metadata["column"],
                self.channel_hint,
            ),
            Cell(
                self.row,
                fields(QuizQuestion)[5].metadata["column"],
                str(self.answerer_id)
                or "",  # casting None to string does not give a falsy string
            ),
        ]

    @property
    def wrong_channel_response(self) -> str:
        """A response to asking for a question in the wrong channel"""
        denial = random.choice(
            (
                "Sorry, this is the wrong channel for this question.",
                "Oops, not this channel!",
                "Not the channel you are looking for...",
                "This particular question is not spoken about in this channel.",
                "Sorry, try a different channel!",
            )
        )
        return f"{denial} Hint for the right channel: {self.channel_hint}"

    @staticmethod
    def wrong_answer_response() -> str:
        """Get a random response to a wrong answer"""
        return random.choice(
            (
                "Sorry, that is not the answer that I have.",
                "Sorry, please try again.",
                "I don't think that is right",
                "We have different answers to that question.",
                "No dice!",
            )
        )

    def correct_answer_response(self) -> str:
        """Get a random response to a correct answer"""
        if self.is_final_question:
            return "Outstanding, you've completed the final question!"
        follow_up = random.choice(
            (
                "Please check if there is another question!",
                "Another one?",
                "How about another question?",
                "Let's go again?",
                "Let's see if you are on a roll!",
            )
        )
        return random.choice(
            (
                f"That's right, well done! {follow_up}",
                f"Affirmative! {follow_up}",
                f"Spot on! {follow_up}",
                f"Correct! {follow_up}",
                f"You've got it! {follow_up}",
            )
        )

    @classmethod
    async def scores(cls) -> Dict[int, int]:
        """Returns a an dictionary, representing the answerers ID mapped to the sum of
        correct answers, ordered from the highest to lowest sum.
        """
        questions = await cls.get_all_quiz_questions()
        sum_dict: DefaultDict[int, int] = defaultdict(int)
        for question in questions:
            if question.answerer_id:
                sum_dict[question.answerer_id] += 1
        return dict(sorted(sum_dict.items(), reverse=True, key=lambda x: x[1]))

    @classmethod
    async def top_scorer_and_score(cls) -> Optional[Tuple[int, int]]:
        """Returns the top scorer (0) and their score (1), with score being the sum of
        correctly answered questions.
        """
        scores = await cls.scores()
        if scores:
            return next(iter(scores.items()))
        return None

    @classmethod
    async def get_current_question(cls) -> Optional[QuizQuestion]:
        """Get lowest unanswered quiz question object."""
        questions = await cls.get_all_quiz_questions()
        for question in questions:
            if not question.answerer_id:
                return question
        return None

    async def write_question_to_sheet(self):
        """Writes the current QuizQuestion to the work sheet."""
        work_sheet = await get_worksheet(QUIZ_SHEET_ID, QUIZ_WORKSHEET)
        await work_sheet.update_cells(self.cell)

    async def mark_as_answered(self, answerer_id: int):
        """Set the answerer to mark the question as answered and save this state to the
        work sheet.
        """
        self.answerer_id = answerer_id
        await self.write_question_to_sheet()


async def is_ticket_used(ticket: Ticket) -> bool:
    """Check if the given ticket exists (was registered) in the sheet"""
    work_sheet = await get_worksheet(SHEET_ID, WORKSHEET)
    # r = await work_sheet.find(ticket.barcode)
    cells = await work_sheet.findall(ticket.barcode)
    return bool(cells and [c for c in cells if c.col == REG_BARCODE_COLUMN])


async def register_ticket(ticket: Ticket, member: User) -> bool:
    """Registers the user to the ticket by appending a row with the relevant information
    to the work sheet
    """
    work_sheet = await get_worksheet(SHEET_ID, WORKSHEET)
    row = ["", "", "", "", ""]
    row[REG_BARCODE_COLUMN - 1] = ticket.barcode
    row[REG_FULL_NAME_COLUMN - 1] = ticket.full_name
    row[REG_DISCORD_NAME_COLUMN - 1] = member.name
    row[REG_DISCORD_ID_COLUMN - 1] = str(member.id)
    row[REG_DATE_COLUMN - 1] = str(datetime.now())
    await work_sheet.append_row(row)
    await log(f"Registering row to sheet: {row}")
    return True
