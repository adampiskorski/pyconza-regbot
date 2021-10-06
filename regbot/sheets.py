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


async def get_worksheet() -> AsyncioGspreadWorksheet:
    """Get the gspread worksheet used to store state of ticket registration"""
    client = await client_manager.authorize()
    sheet = await client.open_by_key(SHEET_ID)
    return await sheet.worksheet(WORKSHEET)


async def is_ticket_used(ticket: Ticket) -> bool:
    """Check if the given ticket exists (was registered) in the sheet"""
    work_sheet = await get_worksheet()
    # r = await work_sheet.find(ticket.barcode)
    cells = await work_sheet.findall(ticket.barcode)
    return bool(cells and [c for c in cells if c.col == 1])


async def register_ticket(ticket: Ticket, member: User) -> bool:
    """Registers the user to the ticket by appending a row with the relevant information
    to the work sheet
    """
    work_sheet = await get_worksheet()
    row = (
        ticket.barcode,
        ticket.full_name,
        member.name,
        str(member.id),
        str(datetime.now()),
    )
    await work_sheet.append_row(row)
    await log(f"Registering row to sheet: {row}")
    return True
