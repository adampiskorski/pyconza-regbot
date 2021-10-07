from datetime import datetime

import gspread_asyncio
from discord import User
from gspread_asyncio import AsyncioGspreadWorksheet

from regbot.google import get_creds, get_str_env
from regbot.helpers import log
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
QUIZ_CHANNEL_COLUMN = 1
QUIZ_ANSWERED_BY_COLUMN = 2
QUIZ_WRONG_CHANNEL_MESSAGE_COLUMN = 3
QUIZ_QUESTION_COLUMN = 4
QUIZ_ANSWER_COLUMN = 5


async def get_worksheet(sheet_id: str, worksheet: str) -> AsyncioGspreadWorksheet:
    """Get the gspread worksheet used to store state of ticket registration"""
    client = await client_manager.authorize()
    sheet = await client.open_by_key(sheet_id)
    return await sheet.worksheet(worksheet)


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
